from app.routers.our_utils import *

# from our_utils import *

import json

def translate(data, save_path):
    print("translation start...", flush=True)
    if isinstance(data, dict):
        results = dict()
        parts = ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7", "Part 8", "Part 9", "Part 10", "Part 11", "Part 12"]
        steps = ["step 1", "step 2", "step 3", "step 4", "step 5", "step 6", "step 7", "step 8", "step 9", "step 10", "step 11", "step 12"]
        input_tokens = 0
        output_tokens = 0
        if "dry" in save_path:
            for p in parts:
                content = ""
                if p in data:
                    content += p + ": " + json.dumps(data[p], ensure_ascii=False, indent=4)
                else:
                    break
                print(f"translating {p}...")
                input = "请将下文全文翻译为中文，在适当位置添加换行。\n" + content
                result = model_generate(input)
                results[p] = result[0]
                write_txt(json.dumps(results, ensure_ascii=False, indent=4) + "\n\n", save_path)
                input_tokens += result[1]
                output_tokens += result[2]
        else:
            for p in parts:
                content = ""
                if p in data:
                    content += p + ": " + data[p][p] + "\n\n"
                    for s in steps:
                        if s in data[p]:
                            content += data[p][s]["implementation details"] + "\n\nReference Source: " + str(data[p][s]["Reference Source"]) + "\n\n"
                        else:
                            break
                    content += "\n\n"
                else:
                    break
                print(f"translating {p}...")
                input = "请将下文全文翻译为中文，在适当位置添加换行。\n" + content
                result = model_generate(input)
                results[p] = result[0]
                write_txt(json.dumps(results, ensure_ascii=False, indent=4) + "\n\n", save_path)
                input_tokens += result[1]
                output_tokens += result[2]
        write_txt(json.dumps(results, ensure_ascii=False, indent=4) + "\n\n" + str(input_tokens) + " " + str(output_tokens), save_path)

    elif isinstance(data, str):
        input = "请将下文全文翻译为中文，在适当位置添加换行。\n" + data
        result = model_generate(input)
        input_tokens = result[1]
        output_tokens = result[2]
        result = result[0]
        write_txt(result + "\n\n" + str(input_tokens) + " " + str(output_tokens), save_path)

    else:
         raise TypeError("The data should be a dictionary or a string, but got %s" % type(data))

    print("translation ended.", flush=True)