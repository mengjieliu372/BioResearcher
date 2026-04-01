# -*- coding: utf-8 -*-
import sys
from app.models.our_utils import *

# from our_utils import *

import time
import re
import subprocess
from pathlib import Path

try:
    from autogen import ConversableAgent
    from app.models.docker_r_compatible_executor import DockerRCompatibleExecutor
except ImportError:
    ConversableAgent = None
    DockerRCompatibleExecutor = None

sys.stdout.reconfigure(encoding='utf-8')


class _Ansi:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def _supports_color() -> bool:
    try:
        if os.getenv("NO_COLOR"):
            return False
        return bool(getattr(sys.stdout, "isatty", lambda: False)())
    except Exception:
        return False


def _color_text(text: str, color: str) -> str:
    if not _supports_color():
        return text
    return f"{color}{text}{_Ansi.RESET}"


def _print_info(text: str):
    print(_color_text(text, _Ansi.YELLOW))


def _print_success(text: str):
    print(_color_text(text, _Ansi.GREEN))


def _print_error(text: str):
    print(_color_text(text, _Ansi.RED))


def _print_stage(text: str):
    print(_color_text(text, _Ansi.CYAN))


def _brief_diag(text: str, limit: int = 220) -> str:
    raw = (text or "").strip().replace("\r", "\n")
    first = raw.split("\n")[0] if raw else ""
    if len(first) > limit:
        return first[:limit] + "..."
    return first


class CodingNeedsFeedbackError(RuntimeError):
    def __init__(self, task_id: str, message: str, fallback_path=None):
        super().__init__(message)
        self.task_id = task_id
        self.fallback_path = fallback_path or []


class CodingFinalFailureError(RuntimeError):
    def __init__(self, task_id: str, message: str, fallback_path=None):
        super().__init__(message)
        self.task_id = task_id
        self.fallback_path = fallback_path or []

CODE_SYSTEM_PROMPT = """
You are a coding agent operating inside a Docker code executor.

Hard requirements:
1. Output exactly one code block per reply, and it must be either ```r or ```sh.
2. Prefer ```r for data/statistics analysis tasks. Use ```sh for file/system operations.
3. Do not include explanations outside the code block.
4. Do not use interactive editors (nano/vim), prompts, or manual steps.
5. Write non-interactive, directly executable shell commands.
6. If a required tool/file/package is missing, do graceful degradation:
   print a warning, create placeholder output, and continue without hard exit.
7. Save artifacts to explicit paths when needed.
8. Only output "The conversation is over." after successful executor feedback or when blocked by missing human input.
9. Do not output code blocks that only print "The conversation is over." without producing task outputs.
"""


def _collect_available_files(base_dir: str, max_items: int = 120) -> str:
    root = Path(base_dir)
    if not root.exists():
        return "(workspace not found)"
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        files.append(rel)
    files = sorted(set(files))
    if not files:
        return "(no files)"
    if len(files) > max_items:
        files = files[:max_items] + [f"... ({len(files) - max_items} more)"]
    return "\n".join(f"- /workspace/{x}" for x in files)


def _probe_r_packages_in_image(image: str, packages: list[str], timeout_sec: int = 120) -> dict:
    """
    Probe package availability in a docker image via one R command.
    Returns:
      {
        "ok": bool,
        "packages": {"pkg": True/False, ...},
        "error": str,
      }
    """
    result = {"ok": False, "packages": {}, "error": ""}
    if not image or not packages:
        result["error"] = "empty image/packages"
        return result

    r_expr = (
        "pkgs<-c("
        + ",".join(f"'{p}'" for p in packages)
        + "); cat(paste(pkgs, sapply(pkgs, requireNamespace, quietly=TRUE), sep='='), sep='\\n')"
    )
    cmd = ["docker", "run", "--rm", image, "R", "-q", "-e", r_expr]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout_sec,
            check=False,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        pkg_map = {}
        for line in out.splitlines():
            line = line.strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().lower()
            if k in packages and v in {"true", "false"}:
                pkg_map[k] = (v == "true")
        if pkg_map:
            result["ok"] = True
            result["packages"] = pkg_map
        else:
            result["error"] = f"no package probe output, exit={proc.returncode}"
    except Exception as e:
        result["error"] = str(e)
    return result


def _chat_execution_status(chat_history) -> tuple[bool, str]:
    """
    Parse autogen chat history and determine whether executor actually succeeded.
    Returns (success, diagnostic_text).
    """
    if not chat_history:
        return False, "empty chat history"
    exec_msgs = []
    for msg in chat_history:
        content = msg.get("content", "")
        if not isinstance(content, str):
            continue
        if "exitcode:" in content or "execution failed" in content or "Code output:" in content:
            exec_msgs.append(content.strip())

    if not exec_msgs:
        return False, "no executor exitcode found in chat history"

    # Use the LAST executor result as final truth.
    last = exec_msgs[-1]
    m = re.search(r"exitcode:\s*(\d+)", last, flags=re.IGNORECASE)
    if not m:
        return False, last
    code = int(m.group(1))
    if code != 0:
        return False, last

    # Quality guard: reject placeholder/fallback-style "successful" runs.
    low_quality_markers = [
        "placeholder",
        "fallback",
        "creating placeholder",
        "wrote placeholder",
        "no rows matched",
        "no hit",
        "missing required",
        "data directory /workspace/data does not exist",
    ]
    last_lc = last.lower()
    bad = [k for k in low_quality_markers if k in last_lc]
    if bad:
        return False, f"{last}\nquality_guard_failed_markers={bad}"

    return True, last


def _clean_chat_history(chat_history):
    if not isinstance(chat_history, list):
        return chat_history
    cleaned = []
    for msg in chat_history:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", "")
        if isinstance(content, str) and content.strip() == "The conversation is over.":
            continue
        cleaned.append(msg)
    return cleaned


def _is_structural_error(status_text: str) -> bool:
    text = (status_text or "").lower()
    structural_markers = [
        "numbers of columns of arguments do not match",
        "length =",
        "in coercion to 'logical(1)'",
        "unused argument",
        "[.data.table",
        "rbind(",
        "rbindlist",
        "subscript out of bounds",
        "object of type 'closure' is not subsettable",
        "could not find function",
        "cannot coerce",
        "unexpected ','",
        "syntax error",
    ]
    return any(k in text for k in structural_markers)


def dry_experiment_extractor(data, output_path, log_path):
    parts = ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7", "Part 8", "Part 9", "Part 10",
             "Part 11", "Part 12"]
    steps = ["step 1", "step 2", "step 3", "step 4", "step 5", "step 6", "step 7", "step 8", "step 9", "step 10",
             "step 11", "step 12"]
    
    protocol_dict = dict()

    for p in parts:
        if p in data:
            protocol = p + ": " + data[p][p] + "\n\n"
            for s in steps:
                if s in data[p]:
                    protocol += data[p][s]["implementation details"] + "\n\n"
                else:
                    break

            protocol_dict[p] = protocol

        else:
            break

    count = 0
    result = dict()
    dry_experiment = dict()
    input_tokens_total = 0
    output_tokens_total = 0



    # 原本的 protocol 输入的是整篇的 text，现在要分 part 提取干实验
    # 下面的 protocol 就换为 protocol_dict

    print(f"dry experiment extractor starts ...\n")
    for p, protocol in protocol_dict.items():
        print(f"Dry experiment extraction {p} start")
        result[p] = dict()

        retry_times = 0
        while retry_times < max_retry_times:
            try:
                dry, dry_input_tokens_num, dry_output_tokens_num = model_generate(
                    prompts["extract_dry"].format(part=p, protocol=protocol),
                    model=MODEL_5_MINI,
                )
                count += 1

                dry, history, regenerate_iter, dry_reflex_input_tokens_num, dry_reflex_output_tokens_num, dry_reflex_count = reflexion_and_regenerate(
                    prompts["extract_dry"].format(part=p, protocol=protocol),
                    dry,
                    prompts['extract_dry_reflexion'],
                    prompts['extract_dry_regenerate'].format(part=p),
                    model=MODEL_5_MINI,
                )
                dry, parser_input_token, parser_output_token = parser_json(dry, prompts["json_correct"])
                count += dry_reflex_count

                result[p]["input"] = prompts["extract_dry"].format(part=p, protocol=protocol)
                result[p]["output"] = dry
                result[p]["history"] = history
                result[p]["input_tokens"] = dry_input_tokens_num + dry_reflex_input_tokens_num + parser_input_token
                result[p]["output_tokens"] = dry_output_tokens_num + dry_reflex_output_tokens_num + parser_output_token
                dry_experiment[p] = dry

                input_tokens_total += result[p]["input_tokens"]
                output_tokens_total += result[p]["output_tokens"]
                print(f"Dry experiment extraction {p} complete.")
                break
            except Exception as e:
                print(f"dry experiment {p} 提取失败，当前总调用次数：", count)
                print(f"dry experiment {p} error: ", e)
                retry_times += 1
        if retry_times == max_retry_times:
            print(f"Dry experiment extraction {p} failed!")

    print(f"\n\n执行完毕，总调用次数 {count}\n总 input tokens 数：{input_tokens_total}\n总 output tokens 数：{output_tokens_total}\n保存结果...\n\n")
    write_json(result, log_path)
    write_json(dry_experiment, output_path)

    # 原先返回的是 list，现在是 dict
    return dry_experiment, input_tokens_total, output_tokens_total



def code_generator(
    dry_data,
    output_path,
    save_dir,
    model=None,
    user_feedback: str = "",
    is_feedback_retry: bool = False,
    progress_callback=None,
):
    if ConversableAgent is None or DockerRCompatibleExecutor is None:
        raise RuntimeError("pyautogen is not installed. Please install pyautogen before code generation.")
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    primary_codegen_model = model or MODEL_CODEX
    workspace_root = os.path.dirname(save_dir)

    docker_image = "rocker/verse"
    executor = DockerRCompatibleExecutor(
        image=docker_image,
        timeout=3600,
        work_dir=save_dir,
        bind_dir=workspace_root,
    )

    code_executor_agent_using_docker = ConversableAgent(
        "code_executor_agent_docker",
        llm_config=False,
        code_execution_config={"executor": executor},
        human_input_mode="NEVER",
    )

    print("\ncode generating starts ...\n\n\n")

    if not os.path.exists(output_path):
        results = dict()
        input_token_num = 0
        output_token_num = 0
    else:
        results = read_json(output_path)
        input_token_num = results.get("input_token_num", 0)
        output_token_num = results.get("output_token_num", 0)

    history = "The HISTORY of your other task executions is as follows:\n"
    flag = False
    previous_task = ""
    previous_summary = ""
    available_files_text = _collect_available_files(workspace_root)
    workspace_root_path = Path(workspace_root)
    workspace_files_full = []
    if workspace_root_path.exists():
        for p in workspace_root_path.rglob("*"):
            if p.is_file():
                rel = p.relative_to(workspace_root_path).as_posix()
                workspace_files_full.append(f"/workspace/{rel}")
    workspace_files_full = sorted(set(workspace_files_full))
    key_r_packages = [
        "DESeq2",
        "limma",
        "edgeR",
        "GEOquery",
        "affy",
        "gcrma",
        "jsonlite",
        "readxl",
        "data.table",
        "httr",
        "curl",
    ]
    pkg_probe = _probe_r_packages_in_image(docker_image, key_r_packages, timeout_sec=120)
    if pkg_probe.get("ok"):
        present = [k for k, v in pkg_probe.get("packages", {}).items() if v]
        missing = [k for k, v in pkg_probe.get("packages", {}).items() if not v]
        env_summary = (
            f"Docker image: {docker_image}\n"
            f"R package probe status: ok\n"
            f"Installed key packages: {', '.join(present) if present else '(none)'}\n"
            f"Missing key packages: {', '.join(missing) if missing else '(none)'}\n"
        )
    else:
        env_summary = (
            f"Docker image: {docker_image}\n"
            f"R package probe status: failed\n"
            f"Probe error: {pkg_probe.get('error', 'unknown')}\n"
        )

    def _make_writer_agent(model_name: str):
        cfg = [{
            "model": model_name,
            "api_key": config_list_coding[0]["api_key"],
            "base_url": config_list_coding[0]["base_url"],
        }]
        return ConversableAgent(
            f"code_writer_{model_name}",
            system_message=CODE_SYSTEM_PROMPT,
            llm_config={"config_list": cfg},
            code_execution_config=False,
        )

    def _sum_tokens_from_chat_cost(chat_cost):
        prompt_tok = 0
        completion_tok = 0
        usage = (chat_cost or {}).get("usage_including_cached_inference", {})
        if isinstance(usage, dict):
            for _, val in usage.items():
                prompt_tok += int((val or {}).get("prompt_tokens", 0) or 0)
                completion_tok += int((val or {}).get("completion_tokens", 0) or 0)
        return prompt_tok, completion_tok

    def _score_file_for_task(task_text_lc: str, path: str) -> int:
        p = path.lower()
        score = 0
        if p.startswith("/workspace/data/"):
            score += 6
        if any(x in p for x in [".rawcount", ".counts", "count", "matrix", "normalized", "tpm", "fpkm", "rld"]):
            score += 5
        if any(x in p for x in ["meta", "clinical", "annot", "phenotype", "sample"]):
            score += 4
        if p.endswith((".csv", ".tsv", ".txt", ".xlsx", ".json", ".gz", ".rds", ".rda", ".rdata")):
            score += 2
        if p.endswith((".tar", ".pdf", ".png", ".jpg", ".jpeg")):
            score -= 4

        # Task-aware boosts
        if "differential" in task_text_lc or "limma" in task_text_lc or "deseq2" in task_text_lc:
            if any(x in p for x in ["rawcount", "counts", "normalized", "meta", "design", "clinical"]):
                score += 4
        if "download" in task_text_lc:
            if any(x in p for x in ["manifest", "datasets", "retrieved", "search_queries"]):
                score += 3
        if "survival" in task_text_lc:
            if any(x in p for x in ["clinical", "meta", "survival"]):
                score += 4
        if "kegg" in task_text_lc or "go " in task_text_lc or "enrichment" in task_text_lc:
            if any(x in p for x in ["deg", "differential", "results", "gene"]):
                score += 3
        return score

    def _heuristic_candidate_files(task_obj: dict, limit: int = 50) -> list[str]:
        task_text = json.dumps(task_obj, ensure_ascii=False).lower()
        scored = []
        for fp in workspace_files_full:
            s = _score_file_for_task(task_text, fp)
            scored.append((s, fp))
        scored.sort(key=lambda x: (-x[0], len(x[1]), x[1]))
        positive = [fp for s, fp in scored if s > 0]
        if not positive:
            return [fp for _, fp in scored[: min(20, len(scored))]]
        return positive[: min(limit, len(positive))]

    def _narrow_candidates_for_task(task_obj: dict, candidate_files: list[str]) -> list[str]:
        tid = str(task_obj.get("task_id", "")).lower()
        desc = str(task_obj.get("task_description", "")).lower()
        t = f"{tid} {desc}"
        files = list(candidate_files)

        # Part1 sample-centric tasks should avoid pulling massive expression matrices.
        if "part 1-dry-experiment-" in t or "eligibility" in t or "sample" in t:
            allow_tokens = [
                "sample",
                "metadata",
                "characteristic",
                "biobank",
                "local",
                "tcga",
                "gtex",
                "filtered",
                "clinical",
            ]
            block_tokens = [
                "rawcount",
                "allsamples",
                "tpm",
                "fpkm",
                "rld",
                "counts.txt",
                "read_counts",
                "normalized_counts",
                "narrowpeak",
                "_raw.tar",
                ".tar",
                ".bam",
                ".fastq",
                ".fq",
            ]
            narrowed = [
                p for p in files
                if any(tok in p.lower() for tok in allow_tokens)
                and not any(tok in p.lower() for tok in block_tokens)
            ]
            if narrowed:
                files = narrowed

        # Explicit stricter rule for Part 1-dry-experiment-5 (eligibility filtering).
        if "part 1-dry-experiment-5" in t or "eligibility filtering" in t:
            keep_tokens = [
                "/workspace/coding3/",
                "filtered_samples",
                "raw_samples",
                "sample_characteristics",
                "sample_meta",
                "clinical",
            ]
            banned_tokens = [
                "/workspace/data/",
                "rawcount",
                "tpm",
                "fpkm",
                "rld",
                "counts",
                ".xlsx",
                ".rds",
                ".rda",
            ]
            narrowed = [
                p for p in files
                if any(k in p.lower() for k in keep_tokens)
                and not any(b in p.lower() for b in banned_tokens)
            ]
            if narrowed:
                files = narrowed

        # Final dedup and small cap to prevent broad probing.
        out = []
        for x in files:
            if x not in out:
                out.append(x)
        return out[:8]

    def _select_task_files_with_thinking(task_obj: dict, candidate_files: list[str]) -> tuple[list[str], int, int, str]:
        if not candidate_files:
            return [], 0, 0, "no_candidates"
        # Cost-control mode: select files by local heuristic only (no extra model call per task).
        narrowed = _narrow_candidates_for_task(task_obj, candidate_files)
        if narrowed:
            return narrowed, 0, 0, "heuristic_narrowed"
        return candidate_files[:8], 0, 0, "heuristic_only"

    def _run_codegen_chat(message: str, model_name: str):
        writer = _make_writer_agent(model_name)
        return code_executor_agent_using_docker.initiate_chat(
            writer,
            message=message,
            summary_method="reflection_with_llm",
            summary_prompt="Please summarize the description of the task and the exact paths to all the files involved.",
            max_turns=6,
            is_termination_msg=lambda msg: "The conversation is over." in msg["content"],
        )

    def _diagnose_failure(task_str: str, status_text: str, model_name: str):
        prompt = (
            "You are diagnosing a failed coding task.\n"
            "Given the task and executor diagnostic, provide concise actionable fixes.\n"
            "Focus on missing files, wrong paths, package/runtime issues, and output naming.\n"
            "Return plain text with 3-8 bullet points.\n\n"
            f"Task:\n{task_str}\n\n"
            f"Executor diagnostic:\n{status_text}\n"
        )
        try:
            advice, in_tok, out_tok = model_generate(prompt, model=model_name)
            return advice, in_tok, out_tok
        except Exception as e:
            return f"[diagnosis_failed:{model_name}] {e}", 0, 0

    def _summarize_tasks_for_planning(data: dict, max_items: int = 30, max_len: int = 220) -> str:
        lines = []
        count = 0
        for part_name, tasks in data.items():
            if not isinstance(tasks, list):
                continue
            for task in tasks:
                tid = str(task.get("task_id", "unknown_task"))
                raw = json.dumps(task, ensure_ascii=False)
                raw = raw.replace("\n", " ")
                if len(raw) > max_len:
                    raw = raw[:max_len] + "..."
                lines.append(f"- {part_name}::{tid}: {raw}")
                count += 1
                if count >= max_items:
                    lines.append(f"... ({sum(len(v) for v in data.values() if isinstance(v, list)) - count} more tasks)")
                    return "\n".join(lines)
        return "\n".join(lines) if lines else "(no tasks)"

    def _build_global_plan(task_overview: str):
        prompt = (
            "You are a senior computational biology workflow planner.\n"
            "Create one global execution plan for all coding tasks below.\n"
            "Goals:\n"
            "1) Propose a stable execution order and shared file contracts.\n"
            "2) Define naming conventions for intermediate/final outputs.\n"
            "3) Preempt common failures (missing files, package issues, path mismatch, timeout) with robust fallbacks.\n"
            "4) Keep the plan executable by a cheaper model in many independent tasks.\n"
            "5) Based on container package availability, decide whether each task should install extra packages.\n"
            "   If installation is needed, propose minimal install commands and reuse installed packages whenever possible.\n"
            "Return concise markdown with sections:\n"
            "- Execution Order\n"
            "- File Contract\n"
            "- Error Prevention Rules\n"
            "- Minimal Validation Checklist\n\n"
            f"Container environment summary:\n{env_summary}\n"
            f"Task overview:\n{task_overview}\n"
        )
        try:
            plan_text, in_tok, out_tok = model_generate(prompt, model=MODEL_5_2_THINKING)
            return plan_text, in_tok, out_tok
        except Exception as e:
            return f"[global_plan_failed] {e}", 0, 0

    def _report_progress(stage: str, **payload):
        if progress_callback is None:
            return
        try:
            progress_callback(stage, payload)
        except Exception:
            pass

    # Preflight before planning/execution: lock task-level input allowlist up front.
    preflight_manifest = {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "workspace_root": workspace_root,
        "tasks": [],
        "missing_input_tasks": [],
    }
    preflight_selection_map = {}
    _report_progress("preflight_start")
    for part_name, task_list in dry_data.items():
        if not isinstance(task_list, list):
            continue
        for task_obj in task_list:
            task_id = str(task_obj.get("task_id", "")).strip() or "unknown_task"
            candidate_files = _heuristic_candidate_files(task_obj)
            selected_files, sel_in_tok, sel_out_tok, sel_status = _select_task_files_with_thinking(task_obj, candidate_files)
            input_token_num += sel_in_tok
            output_token_num += sel_out_tok
            preflight_selection_map[task_id] = selected_files
            rec = {
                "part": part_name,
                "task_id": task_id,
                "selector_status": sel_status,
                "selected_files": selected_files,
            }
            preflight_manifest["tasks"].append(rec)
            if not selected_files:
                preflight_manifest["missing_input_tasks"].append(task_id)

    preflight_path = os.path.join(workspace_root, "coding_task_inputs_preflight.json")
    write_json(preflight_manifest, preflight_path)
    if preflight_manifest["missing_input_tasks"]:
        _report_progress("preflight_blocked", missing_tasks=preflight_manifest["missing_input_tasks"])
        raise RuntimeError(
            "Coding preflight blocked. No selected input files for tasks: "
            + ", ".join(preflight_manifest["missing_input_tasks"])
            + f". See {preflight_path}"
        )
    _report_progress("preflight_done", preflight_file=preflight_path)

    _report_progress("planning_start")
    task_overview = _summarize_tasks_for_planning(dry_data)
    global_plan_text, plan_in_tok, plan_out_tok = _build_global_plan(task_overview)
    _report_progress("planning_done", ok=not str(global_plan_text).startswith("[global_plan_failed]"))
    input_token_num += plan_in_tok
    output_token_num += plan_out_tok
    results["global_plan"] = {
        "model": MODEL_5_2_THINKING,
        "overview": task_overview,
        "plan": global_plan_text,
        "runtime_env_summary": env_summary,
        "runtime_pkg_probe": pkg_probe,
        "input_tokens": plan_in_tok,
        "output_tokens": plan_out_tok,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    results["input_token_num"] = input_token_num
    results["output_token_num"] = output_token_num
    write_json(results, output_path)

    for part in dry_data:
        if part not in results:
            results[part] = dict()

        for idx, task in enumerate(dry_data[part], start=1):
            if task["task_id"] in results[part]:
                existing = results[part][task["task_id"]]
                existing_ok = False
                if isinstance(existing, dict):
                    existing_ok = bool(existing.get("flag", True) if "flag" in existing else True)
                if existing_ok:
                    previous_task = results.get("previous_task", previous_task)
                    flag = results.get("flag", flag)
                    history = results.get("history", history)
                    previous_summary = results.get("previous_summary", previous_summary)
                    continue

            _print_stage("\n\nNow Now Now! generate code for {}\n".format(task["task_id"]))
            _report_progress("task_start", task_id=task["task_id"], part=part, index=idx)

            task_str = json.dumps(task, indent=4)
            task_id = task["task_id"].replace(" ", "")
            objective = "Write the corresponding R code to implement the following task ($filename-{task_id}-saved$):\n\n{dry}.".format(task_id=task_id, dry=task_str)
            selected_files = preflight_selection_map.get(task["task_id"], [])
            sel_status = "preflight_cache"
            selected_files_text = "\n".join(f"- {x}" for x in selected_files) if selected_files else "(none)"
            safety_hint = (
                "Constraints:\n"
                "1) Use only existing files under /workspace listed below; do not invent names like summary_statistics_report.csv.\n"
                "2) Prefer graceful handling for missing files: print warning and create placeholder output instead of hard stop.\n"
                "3) For missing files/packages, do not use exit(), quit(status=1), or stop(...); continue with placeholder outputs.\n"
                "4) Save outputs under /workspace/coding3 with concrete filenames.\n"
                "5) Do not write final outputs to /workspace root.\n"
                "6) Use ONLY the selected files below as inputs for this task.\n"
                "7) DO NOT scan/probe whole directories (forbidden: list.files('/workspace', recursive=TRUE), Sys.glob('/workspace/**')).\n"
                "8) If combining multiple tables, first map them to a shared schema and then merge with data.table::rbindlist(fill=TRUE).\n\n"
                "Container environment (for package decision):\n"
                f"{env_summary}\n"
                "Package policy:\n"
                "- Prefer already installed packages.\n"
                "- If missing packages are required by this task, decide whether to install minimal extras in-code.\n"
                "- Avoid broad/full installs; install only what's needed for this task.\n\n"
                "Dataset selection for this task (strict input allowlist):\n"
                f"{selected_files_text}\n\n"
                f"Available files:\n{available_files_text}\n\n"
            )

            if idx > 1 or part != "Part 1":
                if flag:
                    history += previous_summary
                else:
                    history += previous_task
                results["history"] = history
                base_message = history + "\n" + safety_hint + objective
            else:
                base_message = safety_hint + objective

            if user_feedback:
                base_message += (
                    "\n\nUser feedback and preferences to follow strictly:\n"
                    f"{user_feedback}\n"
                )
            base_message += (
                "\n\nGlobal plan generated by gpt-5.2-thinking (must follow unless conflicting with user feedback):\n"
                f"{global_plan_text}\n"
            )

            step_records = []
            step_records.append(
                {
                    "stage": "global_plan_5.2-thinking",
                    "ok": not str(global_plan_text).startswith("[global_plan_failed]"),
                }
            )
            step_records.append(
                {
                    "stage": "dataset_select_heuristic",
                    "ok": True if selected_files else False,
                    "status": sel_status,
                    "selected_files": selected_files,
                }
            )

            # 1) Primary execution with 5.2-codex.
            status_text = ""
            _report_progress("primary_execute_start", task_id=task["task_id"])
            try:
                chat_result = _run_codegen_chat(base_message, primary_codegen_model)
                p_tok, c_tok = _sum_tokens_from_chat_cost(chat_result.cost)
                input_token_num += p_tok
                output_token_num += c_tok
                ok, status_text = _chat_execution_status(chat_result.chat_history)
                cleaned_history = _clean_chat_history(chat_result.chat_history)
                step_records.append({"stage": "execute_5.2-codex", "ok": ok, "diagnostic": status_text})
                if ok:
                    _print_success(f"[SUCCESS] {task['task_id']} via 5.2-codex | {_brief_diag(status_text)}")
                    _report_progress("task_success", task_id=task["task_id"], model_stage="execute_5.2-codex")
                    flag = True
                    result = {
                        "chat_history": cleaned_history,
                        "cost": chat_result.cost,
                        "human_input": chat_result.human_input,
                        "fallback_path": step_records,
                        "selected_files": selected_files,
                    }
                    previous_summary = part + " " + str(idx) + ": " + chat_result.summary + "\n"
                    results[part][task["task_id"]] = result
                    results["flag"] = flag
                    results["previous_summary"] = previous_summary
                    results["input_token_num"] = input_token_num
                    results["output_token_num"] = output_token_num
                    write_json(results, output_path)
                    _print_info(f"The coding log was saved to: {output_path}")
                    continue
                _print_error(f"[ERROR] {task['task_id']} via 5.2-codex | {_brief_diag(status_text)}")
            except Exception as e:
                status_text = f"exception: {e}"
                step_records.append({"stage": "execute_5.2-codex", "ok": False, "diagnostic": status_text})
                _print_error(f"[ERROR] {task['task_id']} via 5.2-codex | {_brief_diag(status_text)}")

            # 2) Retry strategy:
            # - structural errors: 5.2-thinking diagnosis -> 5.3-codex execute
            # - non-structural errors: direct 5.3-codex execute (cost control)
            needs_thinking_diag = _is_structural_error(status_text)
            diag_52 = ""
            if needs_thinking_diag:
                _print_info(f"[INFO] Structural error detected, asking 5.2-thinking for diagnosis: {task['task_id']}")
                _report_progress("diag_5_2_thinking_start", task_id=task["task_id"])
                diag_52, in_tok, out_tok = _diagnose_failure(task_str, status_text, MODEL_5_2_THINKING)
                input_token_num += in_tok
                output_token_num += out_tok
                step_records.append({"stage": "diagnose_5.2-thinking", "advice": diag_52, "trigger": "structural_error"})
                retry_message_52 = (
                    base_message
                    + "\n\nError diagnosis from model gpt-5.2-thinking:\n"
                    + diag_52
                    + "\n\nGenerate corrected code and execute."
                )
            else:
                _print_info(f"[INFO] Non-structural error, direct escalation to 5.3-codex: {task['task_id']}")
                step_records.append({"stage": "diagnose_5.2-thinking", "skipped": True, "trigger": "non_structural_error"})
                retry_message_52 = (
                    base_message
                    + "\n\nPrevious execution diagnostic:\n"
                    + status_text
                    + "\n\nGenerate corrected code and execute."
                )
            _report_progress("execute_5_3_codex_start", task_id=task["task_id"])
            try:
                chat_result = _run_codegen_chat(retry_message_52, MODEL_5_3_CODEX)
                p_tok, c_tok = _sum_tokens_from_chat_cost(chat_result.cost)
                input_token_num += p_tok
                output_token_num += c_tok
                ok, status_text = _chat_execution_status(chat_result.chat_history)
                cleaned_history = _clean_chat_history(chat_result.chat_history)
                step_records.append({"stage": "execute_5.3-codex", "ok": ok, "diagnostic": status_text})
                if ok:
                    _print_success(f"[SUCCESS] {task['task_id']} via 5.3-codex | {_brief_diag(status_text)}")
                    _report_progress("task_success", task_id=task["task_id"], model_stage="execute_5.3-codex")
                    flag = True
                    result = {
                        "chat_history": cleaned_history,
                        "cost": chat_result.cost,
                        "human_input": chat_result.human_input,
                        "fallback_path": step_records,
                        "selected_files": selected_files,
                    }
                    previous_summary = part + " " + str(idx) + ": " + chat_result.summary + "\n"
                    results[part][task["task_id"]] = result
                    results["flag"] = flag
                    results["previous_summary"] = previous_summary
                    results["input_token_num"] = input_token_num
                    results["output_token_num"] = output_token_num
                    write_json(results, output_path)
                    _print_info(f"The coding log was saved to: {output_path}")
                    continue
                _print_error(f"[ERROR] {task['task_id']} via 5.3-codex | {_brief_diag(status_text)}")
            except Exception as e:
                status_text = f"exception: {e}"
                step_records.append({"stage": "execute_5.3-codex", "ok": False, "diagnostic": status_text})
                _print_error(f"[ERROR] {task['task_id']} via 5.3-codex | {_brief_diag(status_text)}")

            # 3) Hard stop.
            _report_progress("task_failed_final", task_id=task["task_id"])
            flag = False
            fail_msg = (
                f"Task failed after escalation chain: {task['task_id']}\n"
                f"1) 5.2-codex execute failed\n"
                f"2) {'5.2-thinking diagnose + ' if needs_thinking_diag else ''}5.3-codex execute failed\n"
                f"Final diagnostic:\n{status_text}\n"
            )
            previous_task = part + " " + str(idx) + ": " + task_str + "\n" + fail_msg
            results["flag"] = flag
            results["previous_task"] = previous_task
            results["input_token_num"] = input_token_num
            results["output_token_num"] = output_token_num
            results[part][task["task_id"]] = {
                "flag": False,
                "error": fail_msg,
                "fallback_path": step_records,
                "message": base_message,
                "selected_files": selected_files,
            }
            write_json(results, output_path)
            _print_error(f"[FINAL FAIL] {task['task_id']} | {_brief_diag(status_text)}")
            if is_feedback_retry:
                raise CodingFinalFailureError(task["task_id"], fail_msg, step_records)
            raise CodingNeedsFeedbackError(task["task_id"], fail_msg, step_records)

    return "done", input_token_num, output_token_num

# # from translate_zh import translate

# work_dir = "21"
# version = "1"

# # design_savepath = os.path.join(work_dir, f"experiment_program{version}.json")
# # experiments = read_json(design_savepath)

# dry_experiment_savepath = os.path.join(work_dir, f"dry_experiment{version}.json")
# # dry_experiment_log_path = os.path.join(work_dir, f"dry_experiment{version}.log")
# # dry_tranlate_savepath = os.path.join(work_dir, f"dry_experiment_zh{version}.txt")



# # #programming: dry experiment extractor
# # dry_experiment_extract_begin = time.time()
# # input_tokens4, output_tokens4 = 0, 0
# # if not os.path.exists(dry_experiment_savepath):
# #     dry_experiment = dry_experiment_extractor(experiments, dry_experiment_savepath, dry_experiment_log_path)
# #     input_tokens4 += dry_experiment[1]
# #     output_tokens4 += dry_experiment[2]
# #     dry_experiment = dry_experiment[0]
# # else:
# #     dry_experiment = read_json(dry_experiment_savepath)
# # dry_experiment_extract_end = time.time()
# # dry_experiment_extract_time = dry_experiment_extract_end - dry_experiment_extract_begin
# # print("dry_experiment_extract_time:", dry_experiment_extract_time)

# # #translation
# # dry_translation_begin = time.time()
# # if not os.path.exists(dry_tranlate_savepath):
# #     translate(dry_experiment, dry_tranlate_savepath)
# # dry_translation_end = time.time()
# # dry_translation_time = dry_translation_end - dry_translation_begin
# # print("dry_translation_time:", dry_translation_time)



# code_result_log_path = os.path.join(work_dir, f"coding{version}.log")
# code_save_dir = os.path.join(work_dir, f"coding{version}")
# dry_experiment = read_json(dry_experiment_savepath)

# #programming: coding
# coding_begin = time.time()
# code = code_generator(dry_experiment, code_result_log_path, code_save_dir)
# input_tokens5 = code[1]
# output_tokens5 = code[2]

# print("coding token_count: ", input_tokens5, output_tokens5)
# coding_end = time.time()
# coding_time = coding_end-coding_begin
# print("coding time: "+ str(coding_time) + "\n")


