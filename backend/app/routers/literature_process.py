# -*- coding: utf-8 -*-

import os
import json
from collections import OrderedDict
import time
from concurrent.futures import ThreadPoolExecutor
import re
import fitz
import sys

from app.routers.search_datasets_detail import *
from app.routers.our_utils import *

# from search_datasets_detail import *
# from our_utils import *

from pathlib import Path



sys.stdout.reconfigure(encoding='utf-8')

def extract_text(pdf_file):
    print("Start to convert...")
    starttime = time.time()
    doc = fitz.open(pdf_file)
    text = ""

    # Iterate through each page and extract text
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()

    # Close the PDF document
    doc.close()

    endtime = time.time()
    print("Finished. Converting PDF to text costs {}s.".format(endtime-starttime))
    return text



def make_fewshots(fewshots_paper_ref):
    parts = ['Part 1', 'Part 2', 'Part 3', 'Part 4', 'Part 5', 'Part 6']

    # step1
    fewshots_step1 = fewshots_paper_ref['title'] + '\n'
    for i, part in enumerate(parts):
        title_level1 = fewshots_paper_ref['content'][part]['标题']
        #fewshots_step1 += f'{i+1}. {part}：{title_level1}' '\n'
        fewshots_step1 += f'"{part}": "{title_level1}"' '\n'
    fewshots_step1 = fewshots_step1[:-1]

    # step2
    fewshots_step2 = fewshots_paper_ref['title'] + '\n'
    for i, part in enumerate(parts):
        title_level1 = fewshots_paper_ref['content'][part]['标题']
        fewshots_step2 += f'\"{part}\": {{\"Title\": \"{title_level1}\", ' '\n\"Outline\": \"'
        for line in fewshots_paper_ref['content'][part]['大纲']:
            fewshots_step2 += line +'\n'
        fewshots_step2 += "\"}, \n"
    #fewshots_step2 = fewshots_step2[:-1]    # 对应 step2 prompt 的 'guideline_paper_ref'

    # step3
    fewshots_step3 = dict()
    #for i, part in enumerate(parts):
    part = "Part 1"
    fewshots_step3[part] = dict()
    title_level1 = fewshots_paper_ref['content'][part]['标题']
    fewshots_step3[part]['部分大纲'] = fewshots_paper_ref['title'] + "\n" + f'\"{part}\": {{\"Title\": \"{title_level1}\", ' '\n\"Outline\": \"' + '\n'    # 对应 step3 prompt 的 'guideline_paper_ref'
    for line in fewshots_paper_ref['content'][part]['大纲']:
        fewshots_step3[part]['部分大纲'] += line + '\n'
    fewshots_step3[part]['部分大纲'] += "\"}, \n"

    fewshots_step3[part]['实验方案'] = fewshots_paper_ref['content'][part]['protocol']    # 对应 step3 prompt 的 'experiment_paper_ref'

    # step4-6 无

    return fewshots_step1, fewshots_step2, fewshots_step3


def step3_multi(i, output_step2_json, prompts, parts_tar_i, fewshots_step3_parts, paper_ref, paper_tar):
    time.sleep(i*0.5)
    count = 0
    output_step2_part = output_step2_json[parts_tar_i]
    output_step2_part = json.dumps(output_step2_part, indent=4)
    input3 = prompts['step3'].format(paper_ref=paper_ref, paper_tar=paper_tar, num_part=parts_tar_i, guideline_paper_ref=fewshots_step3_parts['部分大纲'], experiment_paper_ref=fewshots_step3_parts['实验方案'], guideline_paper_tar=output_step2_part)
    input_tokens_num = 0
    output_tokens_num = 0
    retry_times = 0
    while retry_times < max_retry_times:
        try:
            response_step3, response_step3_input_tokens_num, response_step3_output_tokens_num = model_generate(input3)
            count += 1
            input_tokens_num += response_step3_input_tokens_num
            output_tokens_num += response_step3_output_tokens_num
            output_step3 = response_step3

            # reflexion
            output_step3, history3, regenerate_iter3, reflexion_input_tokens_num, reflexion_output_tokens_num, rcount3 = reflexion_and_regenerate(input3, output_step3, prompts['step3_reflexion'].format(num_part=parts_tar_i), prompts['step3_regenerate'].format(num_part=parts_tar_i))
            count += rcount3


            #output_step3 = output_step3.replace("json", "").replace("```", "").replace("```", "").strip()
            output_step3_json, parser_input_token, parser_output_token = parser_json(output_step3, prompts)
            output_step3 = json.dumps(output_step3_json, indent=4)
            input_tokens_num += reflexion_input_tokens_num + parser_input_token
            output_tokens_num += reflexion_output_tokens_num + parser_output_token
            print(f"step3 multi {parts_tar_i} 调用次数：", count)
            return parts_tar_i, input3, output_step3, output_step3_json, history3, regenerate_iter3, input_tokens_num, output_tokens_num, count
        except Exception as e:
            print(f"step3 multi {parts_tar_i} error: ",e)
            retry_times += 1
    print(f"step3 {parts_tar_i} 模型返回 None")
    # print(response_step3.prompt_feedback, '\n')
    return None, None, None, None, None, None, None, None, None

def step4_multi(i, part, outputs_step3_part, paper_tar, prompts):
    count = 0
    input4 = prompts['step4'].format(paper_tar=paper_tar, num_part=part, experiment_paper_tar=outputs_step3_part)
    time.sleep(i*0.5)
    # try_times = 0
    input_tokens_num = 0
    output_tokens_num = 0
    retry_times = 0
    while retry_times < max_retry_times:
        try:
            response_step4, response_step4_input_tokens_num, response_step4_output_tokens_num = model_generate(input4)
            count += 1
            input_tokens_num += response_step4_input_tokens_num
            output_tokens_num += response_step4_output_tokens_num
            output_step4 = response_step4

            # reflexion
            output_step4, history4, regenerate_iter4, reflexion_input_tokens_num, reflexion_output_tokens_num, rcount4 = reflexion_and_regenerate(input4, output_step4, prompts['step4_reflexion'].format(num_part=part), prompts['step4_regenerate'].format(num_part=part))
            count += rcount4


            #output_step4 = output_step4.replace("json", "").replace("```", "").replace("```", "").strip()
            output_step4_json, parser_input_token, parser_output_token = parser_json(output_step4, prompts)
            output_step4 = json.dumps(output_step4_json, indent=4)
            input_tokens_num += reflexion_input_tokens_num + parser_input_token
            output_tokens_num += reflexion_output_tokens_num + parser_output_token
            print(f"step4 multi {part} 调用次数：", count)
            return part, input4, output_step4, output_step4_json, history4, regenerate_iter4, input_tokens_num, output_tokens_num, count

        except Exception as e:
            print(f"step4 multi {part} error: ",e)
            print(f"step4 multi {part} 调用次数：", count)
            retry_times += 1
            # try_times += 1
            # time.sleep(4)
    print(f"step4 {part} 模型返回 None")
    # print(response_step4.prompt_feedback, '\n')
    return None, None, None, None, None, None, None, None, None

def step5_multi(i, part, output_step4_part, paper_tar, prompts):
    count = 0
    input5 = prompts['step5'].format(paper_tar=paper_tar, num_part=part, experiment_paper_tar=output_step4_part)
    time.sleep(i*0.5)
    # try_times = 0
    input_tokens_num = 0
    output_tokens_num = 0
    retry_times = 0
    while retry_times < max_retry_times:
        try:
            response_step5, response_step5_input_tokens_num, response_step5_output_tokens_num = model_generate(input5)
            count += 1
            input_tokens_num += response_step5_input_tokens_num
            output_tokens_num += response_step5_output_tokens_num
            output_step5 = response_step5

            # reflexion
            output_step5, history5, regenerate_iter5, reflexion_input_tokens_num, reflexion_output_tokens_num, rcount5 = reflexion_and_regenerate(input5, output_step5, prompts['step5_reflexion'].format(num_part=part), prompts['step5_regenerate'].format(num_part=part))
            count += rcount5


            #output_step5 = output_step5.replace("json", "").replace("```", "").replace("```", "").strip()
            output_step5_json, parser_input_token, parser_output_token = parser_json(output_step5, prompts)
            output_step5 = json.dumps(output_step5_json, indent=4)
            input_tokens_num += reflexion_input_tokens_num + parser_input_token
            output_tokens_num += reflexion_output_tokens_num + parser_output_token
            print(f"step5 multi {part} 调用次数：", count)
            return part, input5, output_step5, output_step5_json, history5, regenerate_iter5, input_tokens_num, output_tokens_num, count
        except Exception as e:
            retry_times += 1
            print(f"step5 multi {part} error: ",e)
            print(f"step5 multi {part} 调用次数：", count)
            # time.sleep(4)
    print(f"step5 {part} 模型返回 None")
    # print(response_step5.prompt_feedback, '\n')
    return None, None, None, None, None, None, None, None, None


def extract_test_pipeline(paper_ref, paper_tar, title_paper_tar, prompts, fewshots_step1, fewshots_step2, fewshots_step3, output_path, log_path):
    parts_tar = ['Part 1', 'Part 2', 'Part 3', 'Part 4', 'Part 5', 'Part 6', 'Part 7', 'Part 8', 'Part 9', 'Part 10', 'Part 11', 'Part 12', 'Part 13', 'Part 14', 'Part 15', 'Part 16', 'Part 17', 'Part 18', 'Part 19', 'Part 20']
    #'第十二部分', '第十三部分', '第十四部分', '第十五部分', '第十六部分', '第十七部分', '第十八部分', '第十九部分', '第二十部分']
    pattern = r'\[(.*?)\]'
    final_output = dict()
    count = 0   # 调用 LLM API 总次数的记录；在 checkpoints 中则是对应开始 step 后的总次数记录


    if os.path.exists(log_path):
        final_output = read_json(log_path)

    flag = True #完全处理成功
    enter = False
    steps = ['step1', 'step2', 'step3', 'step4', 'step5']
    for i, step in enumerate(steps):
        if step in final_output:
            if i >= 2:
                if len(final_output[steps[i]]["output"]) == len(final_output[steps[i-1]]["output"]):
                    continue
            else:
                continue
        enter = True    #进入提取步骤，说明仍有待处理的部分
        if step == 'step1':
            print("\n\n\nfirst level heading extraction starts ...\n\n\n")
            step1_input_tokens_num = 0
            step1_output_tokens_num = 0
            retry_times = 0
            while retry_times < max_retry_times:
                try:
                    input_step1 = prompts['step1'].format(paper_ref=paper_ref, paper_tar=paper_tar, titlelevel1_paper_ref=fewshots_step1)
                    response_step1, response_step1_input_tokens_num, response_step1_output_tokens_num = model_generate(input_step1)
                    count += 1
                    step1_input_tokens_num += response_step1_input_tokens_num
                    step1_output_tokens_num += response_step1_output_tokens_num
                    output_step1 = response_step1

                    # step1 reflexion
                    #print("step1 reflexion ...\n\n\n")
                    output_step1, history1, regenerate_iter1, reflexion_input_tokens_num, reflexion_output_tokens_num, rcount1 = reflexion_and_regenerate(input_step1, output_step1, prompts['step1_reflexion'], prompts['step1_regenerate'])
                    count += rcount1
                    step1_input_tokens_num += reflexion_input_tokens_num
                    step1_output_tokens_num += reflexion_output_tokens_num

                    # 使用 re.DOTALL 使 . 匹配换行符
                    #output_step1 = output_step1.replace("json","").replace("```","").replace("```","").strip()
                    output_step1_json, parser_input_token, parser_output_token = parser_json(output_step1, prompts)
                    output_step1 = json.dumps(output_step1_json, indent=4)
                    print("step1:\n {}".format(output_step1), "\n")
                    '''print("step1_history:")
                    for his in history1:
                        print(his['role'], ':', '='*50, '\n', his['content'][0]['text'])'''

                    final_output["step1"] = dict()
                    final_output["step1"]['input'] = input_step1
                    final_output["step1"]['output'] = output_step1_json
                    final_output["step1"]['history'] = history1
                    final_output["step1"]['all_input_tokens_num'] = step1_input_tokens_num + parser_input_token
                    final_output["step1"]['all_output_tokens_num'] = step1_output_tokens_num + parser_output_token
                    break
                except Exception as e:
                    retry_times += 1
                    print("first level heading extraction error: ", e, '\n\n')
            if retry_times == max_retry_times:
                print("Error: first level heading extraction failed, please try again.")
                return None
            print(f"\n\n\ncall times: {count}")
            print("\n\n\nfirst level heading extraction ends ...\n\n\n")

            print('保存中间结果（step1 及之前）...')
            write_json(final_output, log_path)

        elif step == 'step2':
            # step2
            print("\n\n\nOutlines extraction starts ...\n\n\n")
            step2_input_tokens_num = 0
            step2_output_tokens_num = 0
            retry_times = 0
            while retry_times < max_retry_times:
                try:
                    # time.sleep(4)
                    output_step1 = json.dumps(final_output["step1"]['output'], indent=4)
                    input_step2 = prompts['step2'].format(paper_ref=paper_ref, paper_tar=paper_tar, titlelevel1_paper_ref=fewshots_step1, guideline_paper_ref=fewshots_step2, titlelevel1_paper_tar=output_step1)
                    response_step2, response_step2_input_tokens_num, response_step2_output_tokens_num = model_generate(input_step2)
                    count += 1
                    step2_input_tokens_num += response_step2_input_tokens_num
                    step2_output_tokens_num += response_step2_output_tokens_num
                    output_step2 = response_step2

                    # step2 reflexion
                    output_step2, history2, regenerate_iter2, reflexion_input_tokens_num, reflexion_output_tokens_num, rcount2 = reflexion_and_regenerate(input_step2, output_step2, prompts['step2_reflexion'], prompts['step2_regenerate'])
                    count += rcount2
                    step2_input_tokens_num += reflexion_input_tokens_num
                    step2_output_tokens_num += reflexion_output_tokens_num

                    #output_step2 = output_step2.replace("json","").replace("```","").replace("```","").strip()

                    print("step2:\n{}".format(output_step2))
                    '''print("step2_history:")
                    for his in history2:
                        print(his['role'], ':', '='*50, '\n', his['content'][0]['text'])'''

                    pattern = r'\"Outline\": \"(.*)\"'
                    outlines = re.findall('\"Outline\": (.*?)\}', output_step2, re.DOTALL)
                    new = output_step2
                    for ol in outlines:
                        ol = ol.strip()
                        new = new.replace(ol, ol.replace("\n","\\n"))
                    output_step2_json, parser_input_token, parser_output_token = parser_json(new, prompts)
                    #output_step2 = json.dumps(output_step2_json)
                    final_output["step2"] = dict()
                    final_output["step2"]['input'] = input_step2
                    final_output["step2"]['output'] = output_step2_json
                    final_output["step2"]['history'] = history2
                    final_output["step2"]['all_input_tokens_num'] = step2_input_tokens_num + parser_input_token
                    final_output["step2"]['all_output_tokens_num'] = step2_output_tokens_num + parser_output_token
                    break
                except Exception as e:
                    retry_times += 1
                    print("Outline extraction error: ", e, '\n\n')
            if retry_times == max_retry_times:
                print("Error: Outline extraction failed, please try again.")
                return None
            print(f"\n\n\ncall times: {count}")
            print("\n\n\nOutline extraction ends ...\n\n\n")

            print('保存中间结果（step2 及之前）...')
            write_json(final_output, log_path)

        elif step == 'step3':
            # step3
            print("\n\n\nstep3 starts ...\n\n\n")
            output_step2_json = final_output["step2"]['output']
            final_output["step3"] = final_output.get("step3", dict())
            inputs_step3 = final_output["step3"].get("input", dict())
            outputs_step3 = final_output["step3"].get("output", dict())
            history_step3 = final_output["step3"].get("history", dict())
            step3_input_tokens_num = final_output["step3"].get("all_input_tokens_num", 0)
            step3_output_tokens_num = final_output["step3"].get("all_output_tokens_num", 0)

            step3_parts = list(set(output_step2_json.keys()) - set(outputs_step3.keys()))
            executor = ThreadPoolExecutor(max_workers=len(step3_parts))
            paras = [[i, output_step2_json, prompts, step3_parts[i], fewshots_step3["Part 1"], paper_ref, paper_tar] for i in range(len(step3_parts))]
            paras = list(map(list, zip(*paras)))   #change for debug

            '''for p in paras:
                result = step3_multi(*p)
                parts_tar_i, input3, output3, output3_json, history3, regenerate_iter3, input_tokens_num, output_tokens_num, count3 = result
                count += count3
                step3_input_tokens_num += input_tokens_num
                step3_output_tokens_num += output_tokens_num
                if input3 != None and output3 != None:
                    inputs_step3[parts_tar_i] = input3
                    outputs_step3[parts_tar_i] = output3
                    history_step3[parts_tar_i] = history3'''


            for result in executor.map(step3_multi, *paras):
                parts_tar_i, input3, output3, output3_json, history3, regenerate_iter3, input_tokens_num, output_tokens_num, count3 = result
                if input3 is not None and output3 is not None:
                    count += count3
                    step3_input_tokens_num += input_tokens_num
                    step3_output_tokens_num += output_tokens_num
                    inputs_step3[parts_tar_i] = input3
                    outputs_step3[parts_tar_i] = output3
                    history_step3[parts_tar_i] = history3

                else:
                    flag = False


            #print("step3:\n {}".format(outputs_step3))
            '''for part in history_step3:
                print("step3", part)
                for his in history_step3[part]:
                    print(his['role'], ':', '='*50, '\n', his['content'][0]['text'])'''

            final_output["step3"]['input'] = inputs_step3
            final_output["step3"]['output'] = outputs_step3
            final_output["step3"]['history'] = history_step3
            final_output["step3"]['all_input_tokens_num'] = step3_input_tokens_num
            final_output["step3"]['all_output_tokens_num'] = step3_output_tokens_num
            print(f"\n\n当前调用总次数{count}")
            print("\n\n\nstep3 ends ...\n\n\n")

            print('保存中间结果（step3 及之前）...')
            write_json(final_output, log_path)

        elif step == 'step4':
            # step4
            print("\n\n\nstep4 starts ...\n\n\n")
            outputs_step3 = final_output["step3"]['output']
            final_output["step4"] = final_output.get("step4", dict())
            inputs_step4 = final_output["step4"].get("input", dict())
            outputs_step4 = final_output["step4"].get("output", dict())
            history_step4 = final_output["step4"].get("history", dict())
            step4_input_tokens_num = final_output["step4"].get("all_input_tokens_num", 0)
            step4_output_tokens_num = final_output["step4"].get("all_output_tokens_num", 0)

            step4_parts = list(set(outputs_step3.keys()) - set(outputs_step4.keys()))
            executor = ThreadPoolExecutor(max_workers=len(step4_parts))
            paras = [(i, part, outputs_step3[part], paper_tar, prompts) for i, part in enumerate(step4_parts)]
            paras = list(map(list, zip(*paras)))


            for result in executor.map(step4_multi, *paras):
                part, input4, output4, output4_json, history4, regenerate_iter4, input_tokens_num, output_tokens_num, count4 = result
                if input4 is not None and output4 is not None:
                    count += count4
                    step4_input_tokens_num += input_tokens_num
                    step4_output_tokens_num += output_tokens_num
                    inputs_step4[part] = input4
                    outputs_step4[part] = output4
                    history_step4[part] = history4
                else:
                    flag = False

            #print("step4:\n {}".format(output_step4))
            '''for part in history_step4:
                print("step4", part)
                for his in history_step4[part]:
                    print(his['role'], ':', '='*50, '\n', his['content'][0]['text'])'''

            final_output["step4"]['input'] = inputs_step4
            final_output["step4"]['output'] = outputs_step4
            final_output["step4"]['history'] = history_step4
            final_output["step4"]['all_input_tokens_num'] = step4_input_tokens_num
            final_output["step4"]['all_output_tokens_num'] = step4_output_tokens_num
            print(f"\n\n当前调用总次数{count}")
            print("\n\n\nstep4 ends ...\n\n\n")

            print('保存中间结果（step4 及之前）...')
            write_json(final_output, log_path)

        elif step == 'step5':
            # step5
            print("\n\n\nstep5 starts ...\n\n\n")
            outputs_step4 = final_output["step4"]['output']
            final_output["step5"] = final_output.get("step5", dict())
            inputs_step5 = final_output["step5"].get("input", dict())
            outputs_step5 = final_output["step5"].get("output", dict())
            history_step5 = final_output["step5"].get("history", dict())
            step5_input_tokens_num = final_output["step5"].get("all_input_tokens_num", 0)
            step5_output_tokens_num = final_output["step5"].get("all_output_tokens_num", 0)
            step5_parts = list(set(outputs_step4.keys()) - set(outputs_step5.keys()))

            executor = ThreadPoolExecutor(max_workers=len(step5_parts))
            paras = [(i, part, outputs_step4[part], paper_tar, prompts) for i, part in enumerate(step5_parts)]
            paras = list(map(list, zip(*paras)))

            for result in executor.map(step5_multi, *paras):
                part, input5, output5, output5_json, history5, regenerate_iter5, input_tokens_num, output_tokens_num, count5 = result
                if input5 is not None and output5 is not None:
                    inputs_step5[part] = input5
                    outputs_step5[part] = output5
                    history_step5[part] = history5
                    count += count5
                    step5_input_tokens_num += input_tokens_num
                    step5_output_tokens_num += output_tokens_num
                else:
                    flag = False



            #print("step5:\n {}".format(output_step5))
            '''for part in history_step5:
                print("step5", part)
                for his in history_step5[part]:
                    print(his['role'], ':', '='*50, '\n', his['content'][0]['text'])'''

            final_output["step5"]['input'] = inputs_step5
            final_output["step5"]['output'] = outputs_step5
            final_output["step5"]['history'] = history_step5
            final_output["step5"]['all_input_tokens_num'] = step5_input_tokens_num
            final_output["step5"]['all_output_tokens_num'] = step5_output_tokens_num
            print(f"\n\n当前调用总次数{count}")
            print("\n\n\nstep5 ends ...\n\n\n")

            print('保存中间结果（step5 及之前）...')
            write_json(final_output, log_path)

    if enter:
        experiment = title_paper_tar + ": " + '\n\n'
        sorted_dict = OrderedDict(sorted(final_output["step5"]['output'].items()))
        for part in sorted_dict:
            experiment += sorted_dict[part]
        final_output["experiment"] = experiment

        all_input_tok = final_output["step1"]['all_input_tokens_num'] + final_output["step2"]['all_input_tokens_num'] + final_output["step3"]['all_input_tokens_num'] + final_output["step4"]['all_input_tokens_num'] + final_output["step5"]['all_input_tokens_num']
        all_output_tok = final_output["step1"]['all_output_tokens_num'] + final_output["step2"]['all_output_tokens_num'] + final_output["step3"]['all_output_tokens_num'] + final_output["step4"]['all_output_tokens_num'] + final_output["step5"]['all_output_tokens_num']
        final_output["total_input_tokens_num"] = all_input_tok
        final_output["total_output_tokens_num"] = all_output_tok

        print('\n\n', '总输入 tokens 数目：', all_input_tok, '\n\n')
        print(' 总输出 tokens 数目：', all_output_tok, '\n\n')
        print('extractor 调用总次数：', count, '\n\n')
        write_json(final_output, log_path)
        write_json(sorted_dict, output_path)
        #write_txt(experiment, output_path)
    else:
        experiment = final_output.get("experiment", None)
        if experiment is None:
            experiment = final_output["step6"]["output"]
        all_input_tok = final_output.get("total_input_tokens_num", 0)
        all_output_tok = final_output.get("total_output_tokens_num", 0)
    return experiment, all_input_tok, all_output_tok, flag



def generate_report(
    path_paper_tar,
    title_paper_tar,
    output_path,
    log_path
):
    try:
        current_dir = Path(__file__).parent
        paper_ref_path = current_dir / 'data' / '论文2.pdf'
        fewshots_paper_ref_path = current_dir / 'data' / '论文2-demo.json'
        paper_ref = extract_text(paper_ref_path)
        fewshots_paper_ref = read_json(fewshots_paper_ref_path)
        print("extracting {}".format(path_paper_tar))
        paper_tar = extract_text(path_paper_tar)
    except:
        return None, 0, 0, False
    # step1-3 的 上下文参考内容生成
    fewshots_step1, fewshots_step2, fewshots_step3 = make_fewshots(fewshots_paper_ref)

    # 逐步提取
    return extract_test_pipeline(paper_ref, paper_tar, title_paper_tar, prompts, fewshots_step1, fewshots_step2, fewshots_step3, output_path, log_path)


def analyze(target, conditions, requirements, report, analysis_path, log_path, datasets_path):
    count = 0
    results = {}
    protocols = ''

    print("\nanalysis starts ...\n", flush=True)
    #try:
    analysis, analysis_input_tokens_num, analysis_output_tokens_num = model_generate(prompts["analyze"].format(report, target, conditions, requirements))
    print("\nanalysis initialized...\n", flush=True)
    count += 1
    # reflexion
    retry_times = 0
    while retry_times < max_retry_times:
        try:
            analysis, history, regenerate_iter, analysis_reflex_input_tokens_num, analysis_reflex_output_tokens_num, analysis_reflex_count = reflexion_and_regenerate(prompts["analyze"].format(target, conditions, requirements, report), analysis, prompts['analyze_reflexion'], prompts['analyze_regenerate'])
            break
        except Exception as e:
            print("error: ", e, flush=True)
            retry_times += 1
    if retry_times == 3:
        print("error!", flush=True)
        exit()
    count += analysis_reflex_count
    analysis_json, parser_input_token, parser_output_token = parser_json(analysis, prompts)

    '''except Exception as e:
        print(f"调用次数：", count)
        print("analysis error: ", e)'''

    results["analyze"] = analysis_json
    results["history"] = history
    results["input_tokens_num"] = analysis_input_tokens_num + analysis_reflex_input_tokens_num + parser_input_token
    results["output_tokens_num"] = analysis_output_tokens_num + analysis_reflex_output_tokens_num + parser_output_token
    print("\nanalysis ends ...\n", flush=True)

    count = 0
    for p, v in analysis_json.items():
        if v["Referability"].lower() == "high":
            count += 1
    Referability = count/len(analysis_json)
    analysis_json["Referability"] = Referability

    print("\nsearching for report datasets...", flush=True)
    datasets_selected_all = {
        "useful": {"GEO": {}, "TCGA": {}},
        "all": {"GEO": {}, "TCGA": {}}
    }
    GEO_datasets = extract_datasets(report)     # 提取 geo accesion number
    count = 0
    
    if len(GEO_datasets) > 0:
        dataset_description = {"GEO": {}, "TCGA": {}}
        dataset_description["GEO"] = search_datasets_ids(GEO_datasets)

        print("Extract {} dataset from report, after search got {} datasets\n\n".format(len(GEO_datasets), len(dataset_description["GEO"])))
        datasets_selected_all["all"].update(dataset_description)

        # 检索得到的数据集描述过长，有一些不必要的信息，需要选择关键信息给大模型（LLM 无参与）
        #dataset_description = select_attr(dataset_description)
        # 过滤数据集
        dataset_description_llm_selected = dataset_llm_related(target, dataset_description)
        count += 1
        filter_input_tokens_num = dataset_description_llm_selected[1]
        filter_output_tokens_num = dataset_description_llm_selected[2]
        results["input_tokens_num"] += filter_input_tokens_num
        results["output_tokens_num"] += filter_output_tokens_num
        dataset_description_llm_selected = dataset_description_llm_selected[0]
        # 是否有有用数据集
        num_data = 0
        for db in dataset_description_llm_selected:
            datasets_selected_all["useful"][db].update(dataset_description_llm_selected[db])
            num_data += len(dataset_description_llm_selected[db])
        print("Got {} useful dataset\n\n".format(num_data))
    else:
        print("No dataset extract.\n\n")

    #analysis = json.dumps(analysis_json, indent=4)
    print('保存中间结果（analysis 及之前）...', flush=True)
    write_json(results, log_path)
    write_json(datasets_selected_all, datasets_path)
    write_json(analysis_json, analysis_path)
    return analysis_json, results["input_tokens_num"], results["output_tokens_num"]


