import copy
import json
from concurrent.futures import ThreadPoolExecutor
import re
import time

from app.models.our_utils import *
from app.models.search_download import llm_related

# from our_utils import *
# from search_download import llm_related



def design(target, conditions, requirements, reports_analysis, reports_title_analysis, outlines_analysis, save_path, log_path, datasets):
    model = "gpt-4o-mini"
    count = 0
    results = {}
    if os.path.exists(log_path):
        results = read_json(log_path)
    all_input_tokens = 0
    all_output_tokens = 0
    for i, step in enumerate(['step1', 'step2']):
        if step in results:
            all_input_tokens += results[step]['input_tokens_num']
            all_output_tokens += results[step]['output_tokens_num']
            continue
        results[step] = {}
        if step == 'step1':
            print("\nfirst_level_heading starts ...\n", flush=True)
            step1_input_tokens = 0
            step1_output_tokens = 0
            retry_times = 0
            while retry_times < max_retry_times:
                try:
                    first_level_heading, first_level_heading_input_tokens_num, first_level_heading_output_tokens_num = model_generate(
                        prompts["first_heading_design"].format(reports_title_analysis, target, conditions, requirements))
                    step1_input_tokens += first_level_heading_input_tokens_num
                    step1_output_tokens += first_level_heading_output_tokens_num
                    count += 1
                    # reflexion
                    first_level_heading, history_first_level_heading, regenerate_iter, first_level_heading_reflex_input_tokens_num, first_level_heading_reflex_output_tokens_num, first_level_heading_reflex_count = reflexion_and_regenerate(
                        prompts["first_heading_design"].format(reports_title_analysis, target, conditions, requirements),
                        first_level_heading, prompts['first_heading_design_reflexion'],
                        prompts['first_heading_design_regenerate'])
                    results["step1_history"] = history_first_level_heading
                    count += first_level_heading_reflex_count
                    step1_input_tokens += first_level_heading_reflex_input_tokens_num
                    step1_output_tokens += first_level_heading_reflex_output_tokens_num
                    # first_level_heading = first_level_heading.replace("json", "").replace("```", "").replace("```", "").strip()
                    first_level_heading_json, parser_input_token, parser_output_token = parser_json(first_level_heading,
                                                                                                    prompts)
                    step1_input_tokens += parser_input_token
                    step1_output_tokens += parser_output_token
                    first_level_heading = json.dumps(first_level_heading_json, indent=4)
                    break
                except Exception as e:
                    print("到 first_level_heading 总调用次数：", count, flush=True)
                    print("first_level_heading error: ", e, flush=True)
                    retry_times += 1
            if retry_times == max_retry_times:
                print("Error: first level heading generation failed, please try again.", flush=True)
                print("input: ",
                      prompts["first_heading_design"].format(reports_title_analysis, target, conditions, requirements),
                      flush=True)

            results[step]["json"] = first_level_heading_json
            results[step]["input_tokens_num"] = step1_input_tokens
            results[step]["output_tokens_num"] = step1_output_tokens
            print("到 first_level_heading 总调用次数：", count, flush=True)
            print("\nfirst_level_heading ends ...\n", flush=True)

            print('保存中间结果（first_level_heading 及之前）...', flush=True)
            write_json(results, log_path)

        if step == "step2":
            parts = copy.deepcopy(results["step1"]["json"])
            #related_parts_outlines = llm_retrieve(parts, outlines_analysis)
            #results["related_parts_outlines"] = related_parts_outlines
            print("\nbrief_steps starts ...\n", flush=True)
            step2_input_tokens = 0
            step2_output_tokens = 0
            retry_times = 0
            while retry_times < max_retry_times:
                try:
                    brief_steps, brief_steps_input_tokens_num, brief_steps_output_tokens_num = model_generate(
                        prompts["brief_steps_generate"].format(str(outlines_analysis), target, conditions, requirements,
                                                               json.dumps(results["step1"]["json"], indent=4)))
                    count += 1
                    step2_input_tokens += brief_steps_input_tokens_num
                    step2_output_tokens += brief_steps_output_tokens_num
                    # reflexion
                    brief_steps, history_brief_steps, regenerate_iter, brief_steps_reflex_input_tokens_num, brief_steps_reflex_output_tokens_num, brief_steps_reflex_count = reflexion_and_regenerate(
                        prompts["brief_steps_generate"].format(str(outlines_analysis), target, conditions, requirements,
                                                               json.dumps(results["step1"]["json"], indent=4)),
                        brief_steps, prompts['brief_steps_generate_reflexion'],
                        prompts['brief_steps_generate_regenerate'])
                    results["step2_history"] = history_brief_steps
                    count += brief_steps_reflex_count
                    step2_input_tokens += brief_steps_reflex_input_tokens_num
                    step2_output_tokens += brief_steps_reflex_output_tokens_num
                    # brief_steps = brief_steps.replace("json", "").replace("```", "").replace("```", "").strip()
                    brief_steps_json, parser_input_token, parser_output_token = parser_json(brief_steps, prompts)
                    step2_input_tokens += parser_input_token
                    step2_output_tokens += parser_output_token

                    brief_steps = json.dumps(brief_steps_json, indent=4)
                    break
                except Exception as e:
                    print("到 brief_steps 总调用次数：", count, flush=True)
                    print("brief_steps error: ", e, flush=True)
            if retry_times == max_retry_times:
                print("Error: brief steps generation failed, please try again.", flush=True)
                print("input: ", prompts["brief_steps_generate"].format(str(outlines_analysis), target, conditions, requirements,
                                                               json.dumps(results["step1"]["json"], indent=4)))
            results[step]["json"] = brief_steps_json
            results[step]["input_tokens_num"] = step2_input_tokens
            results[step]["output_tokens_num"] = step2_output_tokens
            print("到 brief_steps 总调用次数：", count, flush=True)
            print("\nbrief_steps ends ...\n", flush=True)

            print('保存中间结果（brief_steps 及之前）...', flush=True)
            write_json(results, log_path)
        all_input_tokens += results[step]['input_tokens_num']
        all_output_tokens += results[step]['output_tokens_num']

    # parts = [('第一部分', part31), ('第二部分', part32), ('第三部分',part33) , ('第四部分', part34), ('第五部分', part35), ('第六部分', part36)]

    step = "step3"
    if step not in results:
        results[step] = {}
    if "json" not in results[step] or len(results["step2"]["json"]) != len(results[step]["json"]):
        history_detailed_steps_dict = results.get("step3_history", {})
        detailed_steps_total_input_tokens_num = results[step].get("input_tokens_num", 0)
        detailed_steps_total_output_tokens_num = results[step].get("output_tokens_num", 0)
        final_experiments = results[step].get('json', {})
        failed_parts = []

        paras = list()
        n = 0
        for pt, p in results["step2"]["json"].items():
            if "json" in results[step] and pt in results[step]["json"]:
                continue
            related_parts = find_related_parts(p, reports_analysis)
            step3_input = prompts["final_design"].format(str(related_parts), str(datasets), target, conditions, requirements, json.dumps(results["step2"]["json"], indent=4),
                                                         str(pt), str(p), str(pt), str(p["Title"]))
            reflexion = prompts['final_design_reflexion'].format(str(pt), str(pt), str(p["Title"]))
            regenerate = prompts['final_design_regenerate'].format(str(pt), str(pt), str(p["Title"]))
            paras.append((n, pt, step3_input, reflexion, regenerate, prompts))
            n += 1

        executor = ThreadPoolExecutor(max_workers=len(paras))
        paras = list(map(list, zip(*paras)))

        for result in executor.map(design_step3_multi, *paras):
            pt, step3_input, detailed_steps, detailed_steps_json, history_detailed_steps, regenerate_iter3, this_pt_input_tokens_num, this_pt_output_tokens_num, count3 = result

            count += count3
            detailed_steps_total_input_tokens_num += this_pt_input_tokens_num
            detailed_steps_total_output_tokens_num += this_pt_output_tokens_num
            if detailed_steps_json != None:
                history_detailed_steps_dict[pt] = history_detailed_steps
                final_experiments[pt] = detailed_steps_json
            else:
                failed_parts.append(pt)

        results["step3_history"] = history_detailed_steps_dict
        results[step]['json'] = final_experiments
        results[step]['input_tokens_num'] = detailed_steps_total_input_tokens_num
        results[step]['output_tokens_num'] = detailed_steps_total_output_tokens_num
        print(f"until detailed_steps finished, total call times：", count, flush=True)
        print("\ndetailed_steps ends ...\n", flush=True)
        all_input_tokens += results[step]['input_tokens_num']
        all_output_tokens += results[step]['output_tokens_num']

        results["experiment"] = final_experiments
        print("total call times: ", count, flush=True)
        print("total input tokens: ", all_input_tokens, flush=True)
        print("total output tokens: ", all_output_tokens, flush=True)
        write_json(results, log_path)
        print("\nFinished！\n", flush=True)
        with open(save_path, "w", encoding="utf-8") as fout:
            json.dump(final_experiments, fout, ensure_ascii=False, indent=4)
        if len(failed_parts) > 0:
            print(f"Error: detailed_steps {str(failed_parts)} generation failed, please try again.", flush=True)
        return final_experiments, all_input_tokens, all_output_tokens

    else:
        return results["experiment"], all_input_tokens, all_output_tokens


def design_step3_multi(n, pt, step3_input, reflexion, regenerate, prompts):
    count = 0
    this_pt_input_tokens_num = 0
    this_pt_output_tokens_num = 0
    print("\nThe {} of detailed_steps starts ...\n".format(pt), flush=True)
    retry_times = 0
    while retry_times < max_retry_times:
        try:
            time.sleep((n + retry_times) * 0.5)
            detailed_steps, detailed_steps_input_tokens_num, detailed_steps_output_tokens_num = model_generate(
                step3_input)

            count += 1
            print(f"detailed_steps {pt} initialization success.", flush=True)
            this_pt_input_tokens_num += detailed_steps_input_tokens_num
            this_pt_output_tokens_num += detailed_steps_output_tokens_num

            time.sleep(0.5)

            # reflexion ========================
            detailed_steps, history_detailed_steps, regenerate_iter, detailed_steps_reflex_input_tokens_num, detailed_steps_reflex_output_tokens_num, detailed_steps_reflex_count = reflexion_and_regenerate(
                step3_input,
                detailed_steps, reflexion,
                regenerate)

            count += detailed_steps_reflex_count
            print(f"detailed_steps {pt} reflexion success，called {detailed_steps_reflex_count} times\n", flush=True)

            # re = detailed_steps.replace("json", "").replace("```", "").replace("```", "").strip()
            detailed_steps_json, parser_input_token, parser_output_token = parser_json(detailed_steps, prompts)

            this_pt_input_tokens_num += detailed_steps_reflex_input_tokens_num + parser_input_token
            this_pt_output_tokens_num += detailed_steps_reflex_output_tokens_num + parser_output_token
            break
        except Exception as e:
            print(f"\ndesign step3 {pt} 第 {retry_times} 次 try，本 part 调用次数：", count, flush=True)
            print(f"step3 {pt} 第 {retry_times} 次 try error: ", e, '\n', flush=True)
            retry_times += 1

    if retry_times == max_retry_times:
        return None, None, None, None, None, regenerate_iter, this_pt_input_tokens_num, this_pt_output_tokens_num, count

    return pt, step3_input, detailed_steps, detailed_steps_json, history_detailed_steps, regenerate_iter, this_pt_input_tokens_num, this_pt_output_tokens_num, count

