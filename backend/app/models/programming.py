# -*- coding: utf-8 -*-
import sys
from app.models.our_utils import *

# from our_utils import *

from autogen import ConversableAgent
from autogen.coding import DockerCommandLineCodeExecutor
import time


sys.stdout.reconfigure(encoding='utf-8')



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
                dry, dry_input_tokens_num, dry_output_tokens_num = model_generate(prompts["extract_dry"].format(part=p, protocol=protocol))
                count += 1

                dry, history, regenerate_iter, dry_reflex_input_tokens_num, dry_reflex_output_tokens_num, dry_reflex_count = reflexion_and_regenerate(
                    prompts["extract_dry"].format(part=p, protocol=protocol),
                    dry,
                    prompts['extract_dry_reflexion'],
                    prompts['extract_dry_regenerate'].format(part=p))
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



def code_generator(dry_data, output_path, save_dir):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    #if not os.path.exists(save_dir+"/data"):
    #    os.mkdir(save_dir+"/data")

    code_writer_agent = ConversableAgent(
        "code_writer",
        system_message=prompts["code"],
        llm_config={"config_list": config_list},
        code_execution_config=False,  # Turn off code execution for this agent.
    )

    # Create a Docker command line code executor.
    executor = DockerCommandLineCodeExecutor(
        image="rocker/verse",  # Execute code using the given docker image name.
        timeout=3600,  # Timeout for each code execution in seconds.
        work_dir=save_dir  # Use the temporary directory to store the code files.
        # functions=[GEO_API_test.geo_download_dataset, Nucldotide_API.GenBank_download_data]
    )

    # Create an agent with code executor configuration that uses docker.
    code_executor_agent_using_docker = ConversableAgent(
        "code_executor_agent_docker",
        llm_config=False,  # Turn off LLM for this agent.
        code_execution_config={"executor": executor},  # Use the docker command line code executor.
        human_input_mode="NEVER",  # Always take human input for this agent for safety.
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

    # dry_data["Part 1"] = dry_data["Part 1"][1:]
    for part in dry_data:
        '''if part in dataset_paths:
            datasets = dataset_paths[part]
            datasets = json.dumps(datasets, indent=4)
        else:'''
        # datasets = None

        if not part in results:
            results[part] = dict()

        for idx, task in enumerate(dry_data[part], start=1):    #下一个任务的输入要加上上一个任务的执行记录
            if task["task_id"] in results[part]:
                previous_task = results.get("previous_task", previous_task)
                flag = results.get("flag", flag)
                history = results.get("history", history)
                previous_summary = results.get("previous_summary", "")
                continue

            print("\n\nNow Now Now! generate code for {}\n\n".format(task["task_id"]))
            
            retry = 0
            while retry < max_retry_times:
                try:
                    task_str = json.dumps(task, indent=4)
                    task_id = task["task_id"].replace(" ", "")      # only for file name
                    objective = "Write the corresponding R code to implement the following task ($filename-{task_id}-saved$):\n\n{dry}.".format(task_id=task_id, dry=task_str)

                    if idx > 1 or part != "Part 1": # 不是最开头
                        if flag:
                            history += previous_summary
                        else:
                            if retry < 1:
                                history += previous_task

                        results["history"] = history

                        # if datasets:
                        #     message = history + "\n" + "The following are some downloaded datasets that could be used for this part of the dry experiment, and their details and local paths: \n{datasets}\n\n".format(datasets=datasets) + objective
                        # else:
                        message = history + "\n" + objective
                    else:
                        # # 在这里插入一下载的数据集路径，上面的 message 也要插入数据集
                        # if datasets:
                        #     message = "The following are some downloaded datasets that can be used for this part of the dry experiment, and their details and local paths: \n{datasets}\n\n".format(datasets=datasets) + objective
                        # else:
                        message = objective

                    # objective = "从独立的原发性STS数据集中获取公开的转录组数据，具体包括GEO（Gene Expression Omnibus）数据库中的GSE21050、GEO数据库中的GSE21122。"
                    chat_result = code_executor_agent_using_docker.initiate_chat(
                        code_writer_agent,
                        message=message,
                        summary_method = "reflection_with_llm",
                        summary_prompt = "Please summarize the description of the task and the exact paths to all the files involved.",
                        max_turns=6,
                        is_termination_msg=lambda msg : "The conversation is over." in msg["content"])
                    #executor.stop()

                    flag = True
                    result = {
                        "chat_history": chat_result.chat_history,
                        "cost": chat_result.cost,
                        "human_input": chat_result.human_input}
                    previous_summary = part + " " + str(idx) + ": " + chat_result.summary + "\n"
                    input_token_num += chat_result.cost['usage_including_cached_inference'][config_list[0]["model"]]["prompt_tokens"]
                    output_token_num += chat_result.cost['usage_including_cached_inference'][config_list[0]["model"]]["completion_tokens"]

                    # results.append(result)
                    results[part][task["task_id"]] = result
                    results["flag"] = flag
                    results["previous_summary"] = previous_summary
                    results["input_token_num"] = input_token_num
                    results["output_token_num"] = output_token_num

                    write_json(results, output_path)
                    print(f"\n\nThe coding log was saved to the file `{output_path}`\n")
                    break


                except Exception as e:
                    retry += 1
                    flag = False
                    previous_task = part + " " + str(idx) + ": " + task_str + "\nThis task failed to execute and failed to obtain corresponding output.\n"
                    print("coding error: ", e)

                    results["flag"] = flag
                    results["previous_task"] = previous_task
                    continue

            if flag:
                continue
            # 为未完成的任务记录当时的 status，只需记录 message
            results[part][task["task_id"]] = {
                "flag": flag,
                "message": message,
            }


    # return "done", chat_result.cost['usage_including_cached_inference']["gpt-4o"]["prompt_tokens"], chat_result.cost['usage_including_cached_inference']["gpt-4o"]["completion_tokens"]
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


