# from autogen import ConversableAgent
from openai import OpenAI
import os
import re
import json
import time
import socket
import threading
from collections import deque
from itertools import count
from pathlib import Path

import requests



# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

OPENAI_PRIMARY_BASE_URL = "https://hk-api.gptbest.vip/v1"
OPENAI_SECONDARY_BASE_URL = "https://api.bltcy.ai/v1"
CONNECT_TIMEOUT_SEC = float(os.getenv("OPENAI_CONNECT_TIMEOUT_SEC", "8"))
MODEL_CALL_RETRIES = int(os.getenv("MODEL_CALL_RETRIES", "1"))
MAX_TOTAL_MODEL_ATTEMPTS = int(os.getenv("MAX_TOTAL_MODEL_ATTEMPTS", "6"))

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-LyefXpoTSxEqyeet09NirlY5kbNlKbku8Xr9LHV9a8PSgxKb")

MODEL_NANO = "gpt-5-nano-2025-08-07"
MODEL_4O_MINI = "gpt-4o-mini"
MODEL_5_MINI = "gpt-5-mini"
MODEL_PRECISE = "gpt-5.2"
MODEL_5_2_THINKING = "gpt-5.2-thinking"
MODEL_CODEX = "gpt-5.2-codex"
MODEL_5_3_CODEX = "gpt-5.3-codex"
PREFER_NANO_FIRST = os.getenv("PREFER_NANO_FIRST", "1").strip().lower() not in {"0", "false", "no"}
LOG_MODEL_USED = os.getenv("LOG_MODEL_USED", "1").strip().lower() not in {"0", "false", "no"}
ACTIVE_OPENAI_BASE_URL = OPENAI_PRIMARY_BASE_URL
CONNECTIVITY_ERROR = None
MODEL_MAX_ACTIVE = max(1, int(os.getenv("MODEL_MAX_ACTIVE", "1")))


def _is_reachable_status(code: int) -> bool:
    return code in {200, 401, 403, 404, 405}


def _probe_base_url(base_url: str, proxies: dict | None = None):
    test_url = base_url.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    t0 = time.time()
    try:
        r = requests.get(test_url, headers=headers, timeout=CONNECT_TIMEOUT_SEC, proxies=proxies)
        cost = int((time.time() - t0) * 1000)
        return _is_reachable_status(r.status_code), r.status_code, cost, ""
    except Exception as e:
        cost = int((time.time() - t0) * 1000)
        return False, None, cost, str(e)


def _local_proxy_url():
    # Detect common local Clash/Proxy ports.
    for host, port in [("127.0.0.1", 7890), ("127.0.0.1", 7897), ("127.0.0.1", 10809)]:
        try:
            with socket.create_connection((host, port), timeout=0.8):
                return f"http://{host}:{port}"
        except Exception:
            continue
    return None


def _bootstrap_openai_base_url():
    global ACTIVE_OPENAI_BASE_URL, CONNECTIVITY_ERROR
    # 1) direct probe: hk primary -> bltcy secondary
    for candidate in [OPENAI_PRIMARY_BASE_URL, OPENAI_SECONDARY_BASE_URL]:
        ok, status, cost, err = _probe_base_url(candidate)
        print(f"[openai-link] direct probe {candidate} ok={ok} status={status} time_ms={cost} err={err}")
        if ok:
            ACTIVE_OPENAI_BASE_URL = candidate
            os.environ["OPENAI_BASE_URL"] = candidate
            CONNECTIVITY_ERROR = None
            return

    # 2) direct failed: check local proxy
    proxy = _local_proxy_url()
    if not proxy:
        CONNECTIVITY_ERROR = (
            "OpenAI relay endpoints are unreachable by direct connection, and no local proxy was detected. "
            "Program terminated."
        )
        print(f"[openai-link] ERROR: {CONNECTIVITY_ERROR}")
        return

    # 3) proxy exists: test again through proxy
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    prox = {"http": proxy, "https": proxy}
    for candidate in [OPENAI_PRIMARY_BASE_URL, OPENAI_SECONDARY_BASE_URL]:
        ok, status, cost, err = _probe_base_url(candidate, proxies=prox)
        print(f"[openai-link] proxy probe {candidate} ok={ok} status={status} time_ms={cost} err={err}")
        if ok:
            ACTIVE_OPENAI_BASE_URL = candidate
            os.environ["OPENAI_BASE_URL"] = candidate
            CONNECTIVITY_ERROR = None
            return

    CONNECTIVITY_ERROR = (
        "OpenAI relay endpoints are unreachable in both direct and proxy modes "
        "(hk primary + bltcy secondary). Program terminated."
    )
    print(f"[openai-link] ERROR: {CONNECTIVITY_ERROR}")


_bootstrap_openai_base_url()

max_retry_times = 2
client = OpenAI()
config_list_general = [
    {
        'model': MODEL_PRECISE,
        'api_key': os.environ["OPENAI_API_KEY"],
        'base_url': ACTIVE_OPENAI_BASE_URL
    }
]
# Keep backward compatibility for existing imports.
config_list = config_list_general
config_list_coding = [
    {
        'model': MODEL_CODEX,
        'api_key': os.environ["OPENAI_API_KEY"],
        'base_url': ACTIVE_OPENAI_BASE_URL
    }
]


class _ModelCallQueue:
    """Process-wide FIFO queue to serialize model calls."""
    def __init__(self, max_active: int = 1):
        self._max_active = max(1, int(max_active))
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._active = 0
        self._queue = deque()
        self._ticket_gen = count(1)

    def acquire(self):
        ticket = next(self._ticket_gen)
        with self._cond:
            self._queue.append(ticket)
            while True:
                is_head = self._queue and self._queue[0] == ticket
                if is_head and self._active < self._max_active:
                    self._active += 1
                    return ticket
                self._cond.wait()

    def release(self, ticket):
        with self._cond:
            if self._queue and self._queue[0] == ticket:
                self._queue.popleft()
            else:
                try:
                    self._queue.remove(ticket)
                except ValueError:
                    pass
            if self._active > 0:
                self._active -= 1
            self._cond.notify_all()

    def snapshot(self):
        with self._lock:
            return {
                "max_active": self._max_active,
                "active": self._active,
                "queue_waiting": len(self._queue) - self._active if len(self._queue) >= self._active else 0,
                "queue_total": len(self._queue),
            }


MODEL_CALL_QUEUE = _ModelCallQueue(MODEL_MAX_ACTIVE)

def model_generate(query, model=MODEL_NANO, temperature=0.7, is_messages=False, n=1):
    if CONNECTIVITY_ERROR:
        raise RuntimeError(CONNECTIVITY_ERROR)
    if not is_messages:
        message = [
            {
                "role": "user",
                "content": query,
                "type": "text"
            }
        ]
    else:
        message = query

    def _dedup_keep_order(seq):
        out = []
        for x in seq:
            if x and x not in out:
                out.append(x)
        return out

    # Global fallback chain.
    # Non-coding preference:
    # - default entry with MODEL_NANO: nano -> 4o-mini -> 5-mini -> 5.2
    # - non-nano entries: 4o-mini -> 5-mini -> 5.2 (no fallback back to nano)
    # Codex must only be used when explicitly requested by coding stage.
    if model == MODEL_5_3_CODEX:
        fallback_order = [MODEL_5_3_CODEX, MODEL_CODEX, MODEL_PRECISE, MODEL_4O_MINI]
    elif model == MODEL_CODEX:
        fallback_order = [MODEL_CODEX, MODEL_PRECISE, MODEL_4O_MINI]
    elif model == MODEL_4O_MINI:
        fallback_order = [MODEL_4O_MINI, MODEL_PRECISE]
    elif model == MODEL_5_MINI:
        fallback_order = [MODEL_5_MINI, MODEL_PRECISE, MODEL_4O_MINI]
    elif model == MODEL_PRECISE:
        fallback_order = [MODEL_PRECISE, MODEL_4O_MINI]
    elif model == MODEL_5_2_THINKING:
        fallback_order = [MODEL_5_2_THINKING, MODEL_PRECISE, MODEL_4O_MINI]
    elif model == MODEL_NANO:
        fallback_order = [MODEL_NANO, MODEL_4O_MINI]
    else:
        fallback_order = [MODEL_4O_MINI, MODEL_PRECISE]
    candidate_models = _dedup_keep_order(fallback_order)

    ticket = MODEL_CALL_QUEUE.acquire()
    try:
        last_error = None
        total_attempts = 0
        for candidate_model in candidate_models:
            if total_attempts >= MAX_TOTAL_MODEL_ATTEMPTS:
                break
            count = 0
            candidate_temperature = temperature
            if candidate_model in {"o1-mini", "o1-preview"} or "o1-mini" in candidate_model:
                candidate_temperature = 1
            while count < max(1, MODEL_CALL_RETRIES):
                if total_attempts >= MAX_TOTAL_MODEL_ATTEMPTS:
                    break
                total_attempts += 1
                try:
                    response = client.chat.completions.create(
                        model=candidate_model,
                        messages=message,
                        n=n,
                        max_tokens=4096,
                        temperature=candidate_temperature
                    )
                    if LOG_MODEL_USED:
                        print(f"[model_used] requested={model} used={candidate_model}")
                    if n > 1:
                        responses = []
                        for i in range(n):
                            content = response.choices[i].message.content
                            if not (content or "").strip():
                                raise RuntimeError(f"Empty model output. model={candidate_model}")
                            responses.append(content)
                        return responses, response.usage.prompt_tokens, response.usage.completion_tokens
                    content = response.choices[0].message.content
                    if not (content or "").strip():
                        raise RuntimeError(f"Empty model output. model={candidate_model}")
                    return content, response.usage.prompt_tokens, response.usage.completion_tokens
                except Exception as e:
                    last_error = e
                    print("error: ", e)
                    count += 1
            current_idx = candidate_models.index(candidate_model)
            if current_idx + 1 < len(candidate_models):
                print(f"model_generate fallback: {candidate_model} -> {candidate_models[current_idx + 1]}")

        raise RuntimeError(f"model_generate failed after retries. model={model}, last_error={last_error}")
    finally:
        MODEL_CALL_QUEUE.release(ticket)


def parse_bracket_score(text: str, default: float = 0.0) -> float:
    if not isinstance(text, str):
        return default
    matches = re.findall(r"\[(.*?)\]", text, flags=re.DOTALL)
    if not matches:
        return default
    raw = matches[-1].strip().lower()
    raw = raw.replace("/5", "")
    raw = raw.replace("score:", "").replace("score", "").strip()
    m = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not m:
        return default
    try:
        return float(m.group(0))
    except Exception:
        return default

def reflexion_and_regenerate(input_1, output_1, instruction_reflexion, instruction_regenerate, model=MODEL_4O_MINI, max_iter=2):
    count = 0
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": input_1}]
        }
    ]
    messages.append(
        {
            "role": "assistant",
            "content": [{"type": "text", "text": output_1}]
        }
    )

    final_response = ""
    regenerate_iter = 0
    input_tokens_num = 0
    output_tokens_num = 0
    for i in range(max_iter):
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": instruction_reflexion}]
        })

        # time.sleep(4)
        response1, response1_input_tokens_num, response1_output_tokens_num = model_generate(messages, model, temperature=0.1, is_messages=True)
        count += 1
        input_tokens_num += response1_input_tokens_num
        output_tokens_num += response1_output_tokens_num
        messages.append({
            "role": "assistant",
            "content": [{"type": "text", "text": response1}]
        })

        if parse_bracket_score(response1, default=0.0) >= 4.5:
            assert messages[-3]['role'] == 'assistant'
            final_response = messages[-3]['content'][0]['text']
            break

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": instruction_regenerate}]
        })

        # time.sleep(4)
        response2, response2_input_tokens_num, response2_output_tokens_num = model_generate(messages, model, is_messages=True)
        count += 1
        input_tokens_num += response2_input_tokens_num
        output_tokens_num += response2_output_tokens_num

        messages.append({
            "role": "assistant",
            "content": [{"type": "text", "text": response2}]
        })

        final_response = response2
        regenerate_iter += 1

    return final_response, messages, regenerate_iter, input_tokens_num, output_tokens_num, count



def write_txt(text, output_path):
    with open(output_path, 'w', encoding='utf-8') as fw:
        fw.write(text)

def read_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    return data

def read_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def write_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as fw:
        json.dump(data, fw, ensure_ascii=False, indent=4)


def parser_json(input, prompts):
    def _parse_json_lenient(raw_text: str):
        if not isinstance(raw_text, str):
            raise ValueError("parser_json expects string content")
        txt = raw_text.strip()
        # Direct parse.
        try:
            return json.loads(txt)
        except Exception:
            pass

        # Parse from fenced code block.
        code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", txt, flags=re.IGNORECASE)
        for block in code_blocks:
            block = block.strip()
            try:
                return json.loads(block)
            except Exception:
                continue

        # Parse from first object/array span.
        candidates = []
        lobj, robj = txt.find("{"), txt.rfind("}")
        if lobj != -1 and robj != -1 and robj > lobj:
            candidates.append(txt[lobj:robj + 1])
        larr, rarr = txt.find("["), txt.rfind("]")
        if larr != -1 and rarr != -1 and rarr > larr:
            candidates.append(txt[larr:rarr + 1])

        for cand in candidates:
            try:
                return json.loads(cand)
            except Exception:
                continue

        raise ValueError("No valid JSON payload found")

    retry_times = 0
    parser_input_tokens = 0
    parser_output_tokens = 0
    repair_candidates = [MODEL_4O_MINI, MODEL_5_MINI, MODEL_PRECISE]

    parser_prompt = prompts["json_correct"] if isinstance(prompts, dict) else str(prompts)
    current_text = input

    while retry_times < (max_retry_times + 2):
        try:
            parsed = _parse_json_lenient(current_text)
            return parsed, parser_input_tokens, parser_output_tokens
        except Exception as e:
            print(f"parser error {retry_times}: ", e)
            print(current_text, "\n\n\n")
            repair_prompt = (
                parser_prompt.format(current_text, e)
                + "\n\nReturn JSON only. Do not ask questions, do not explain."
            )
            for repair_model in repair_candidates:
                regen_text, input_tokens, output_tokens = model_generate(
                    repair_prompt,
                    model=repair_model,
                    temperature=0.1,
                )
                parser_input_tokens += input_tokens
                parser_output_tokens += output_tokens
                current_text = regen_text
                try:
                    parsed = _parse_json_lenient(current_text)
                    return parsed, parser_input_tokens, parser_output_tokens
                except Exception:
                    continue
            retry_times += 1

    print("parser_json failed! parser_json input is :")
    print(current_text, "\n\n")
    raise ValueError("parser_json failed after retries")


prompts_path = Path(__file__).parent / 'data' / 'prompts_withReflexion_en2.json'
prompts = read_json(prompts_path)



def extract_datasets(report):
    pattern = r"\b(?:GPL|GSM|GSE|GDS)\d+\b"
    GEO_datasets_id = re.findall(pattern, report, re.DOTALL)
    # TCGA_datasets_id = re.findall()
    return list(set(GEO_datasets_id))

def llm_retrieve(parts, outlines_analysis):
    print("relevant parts retrieval start...")
    related_parts_outlines = {}
    #related_parts = {}
    for part in parts.keys():
        #related_parts[part] = {}
        if "Reference Source" in parts[part]:
            del parts[part]["Reference Source"]
        for article_id in outlines_analysis.keys():
            related_parts_str, input_tokens, output_tokens = model_generate(prompts["llm_retrieve"].format(str(parts[part]), str(outlines_analysis[article_id])))
            related_parts_json, parse_input_tokens, parse_output_tokens = parser_json(related_parts_str, prompts)
            related_parts_outlines[article_id] = {}
            #related_parts[part][article_id] = {}
            for p in related_parts_json["related_parts"]:
                related_parts_outlines[article_id][p] = outlines_analysis[article_id][p]
                related_parts_outlines[article_id][str(p) + " analysis"] = outlines_analysis[article_id][str(p) + " analysis"]
                #related_parts[part][article_id][p] = reports_analysis[article_id][p]
                #related_parts[part][article_id][str(p) + " analysis"] = reports_analysis[article_id][
                #    str(p) + " analysis"]
    print("relevant parts retrieval end...")
    return related_parts_outlines

def find_related_parts(part_content, reports_analysis):
    try:
        reference_source = part_content["Reference Source"]
        if reference_source is None or reference_source == "none":
            return {}
        related_parts = {}
        for article_id, parts in reference_source.items():
            related_parts[article_id] = {}
            for p in parts:
                if p in reports_analysis[article_id].keys():
                    related_parts[article_id][p] = reports_analysis[article_id][p]
                    related_parts[article_id][str(p) + " analysis"] = reports_analysis[article_id][str(p) + " analysis"]
    except Exception as e:
        print(e)
    return related_parts

project_root = os.path.dirname(os.path.abspath(__file__))
