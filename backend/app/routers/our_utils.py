# from autogen import ConversableAgent
from openai import OpenAI
import os
import re
import json
from pathlib import Path



# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

os.environ['OPENAI_BASE_URL'] ="https://xiaoai.plus/v1"
os.environ['OPENAI_API_KEY'] = "sk-2KqQUJUybPoQireXzyrckbN6rITOaNrqnm7pWmUB5snaVvLn"    # demo_backend

max_retry_times = 2
client = OpenAI()
config_list = [
    {
        'model': 'gpt-4o-mini',
        'api_key': "sk-2KqQUJUybPoQireXzyrckbN6rITOaNrqnm7pWmUB5snaVvLn",
        'base_url': 'https://api.xiaoai.plus/v1'
    }
]

def model_generate(query, model="gpt-4o-mini-2024-07-18", temperature=0.7, is_messages=False, n=1):
    count = 0
    if model == "o1-mini" or model == "o1-preview" or "o1-mini" in model:
        temperature = 1
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
    while count < 3:
        try:
            '''response = assistant.generate_reply(
                messages=query
            )'''
            response = client.chat.completions.create(
                model=model,
                messages=message,
                n=n,
                max_tokens=4096,
                temperature=temperature     # default 1
            )
            if n > 1:
                responses = []
                for i in range(n):
                    responses.append(response.choices[i].message.content)
                return responses, response.usage.prompt_tokens, response.usage.completion_tokens
            #return response, assistant.print_usage_summary(), assistant.clear_usage_summary()
            return response.choices[0].message.content,response.usage.prompt_tokens, response.usage.completion_tokens
        except Exception as e:
            print("error: ", e)
            #print("response: ", response)
            count += 1

def reflexion_and_regenerate(input_1, output_1, instruction_reflexion, instruction_regenerate, model="gpt-4o-mini-2024-07-18", max_iter=2):
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

        if eval(re.findall(r'\[(.*?)\]', response1)[-1].lower().replace("/5", "").replace("score: ", "")) >= 4.5:
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
    retry_times = 0
    parser_input_tokens = 0
    parser_output_tokens = 0
    
    while retry_times < max_retry_times:
        try:
            input = input.replace("json", "").replace("```", "").replace("```", "").strip()
            input = json.loads(input)
            return input, parser_input_tokens, parser_output_tokens
        except Exception as e:
            print(f"parser error {retry_times}: ", e)
            print(input, "\n\n\n")
            input, input_tokens, output_tokens = model_generate(prompts["json_correct"].format(input, e))
            parser_input_tokens += input_tokens
            parser_output_tokens += output_tokens
            retry_times += 1

    # print(e)
    print("parser_json failed! parser_json input is :")
    print(input, "\n\n")
    # exit()


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
