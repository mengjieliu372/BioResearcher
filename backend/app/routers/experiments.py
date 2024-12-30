from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import random

# BioReseacher
import os
import copy

from app.routers.search_download import *
from app.routers.literature_process import *
from app.routers.experimental_design import *
from app.routers.programming import *
from app.routers.our_utils import *
from app.routers.translate_zh import translate

# from search_download import *
# from literature_process import *
# from experimental_design import *
# from programming import *
# from our_utils import *
# from translate_zh import translate

import time



router = APIRouter()


Experiments_File = Path(__file__).parent.parent / "data" / "experiments.json"
data_dir = Path(__file__).parent.parent / "data"
existing_ids = set()


class PaperSet(BaseModel):
    PMC: bool
    PubMed: bool

class Dataset(BaseModel):
    GEO: bool
    NCBI: bool
    cBioPortal: bool

class Experiment(BaseModel):
    expName: str
    expPurpose: str
    expCondition: str
    expRequirement: str
    paperset: PaperSet
    dataset: Dataset
    llmModel: str
    refNum: Optional[int] = None
    reviewerRound: Optional[int] = None

class Projectid(BaseModel):
    id: str



def run_bioresearcher(expid: str, target: str, conditions: str, requirements: str, model_type: str):
    print("start generating protocol...")
    work_dir = data_dir / expid
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    work_log_path = os.path.join(work_dir, "work_log.txt")
    related_paper_savedir = os.path.join(work_dir, "papers")
    related_paper_path = os.path.join(related_paper_savedir, "related_papers_info.json")
    retrieved_paper_path = os.path.join(related_paper_savedir, "retrieved_papers_info.json")
    related_paper_search_queries_path = os.path.join(related_paper_savedir, "related_paper_search_queries_llm_res.json")
    related_dataset_savedir = os.path.join(work_dir, "dataset_1")
    related_dataset_path = os.path.join(related_dataset_savedir, "related_datasets_info.json")
    retrieved_dataset_path = os.path.join(related_dataset_savedir, "retrieved_datasets_info.json")
    related_dataset_search_queries_path = os.path.join(related_dataset_savedir, "related_dataset_search_queries_llm_res.json")

    reports_savedir = os.path.join(work_dir, "reports")

    log_file = open(work_log_path, "a+", encoding="utf-8")

    if not os.path.exists(reports_savedir):
        os.mkdir(reports_savedir)
    if not os.path.exists(related_paper_savedir):
        os.mkdir(related_paper_savedir)
    if not os.path.exists(related_dataset_savedir):
        os.mkdir(related_dataset_savedir)

    #Literature searching module
    print("start search paper...")
    search_begin = time.time()
    input_tokens1, output_tokens1 = 0, 0
    if not os.path.exists(related_paper_path):
        queries, input_tokens1, output_tokens1, flag, full_llm_res = search_download(target, conditions, requirements, model_type, retmax=2, savedir=related_paper_savedir, retrieved_paper_info_path=retrieved_paper_path, related_paper_info_path=related_paper_path)     # retmax: 检索次数，用户可选定义
        write_json(full_llm_res, related_paper_search_queries_path)
        log_file.write("search_queries: " + str(queries) + "\n")
        if not flag:
            print(f"Warning: There are some papers that failed to download, please download them manually!")
    print("generating search query token_count: ", input_tokens1, output_tokens1)
    search_end = time.time()
    search_time = search_end - search_begin
    log_file.write("generating search query search_time: "+ str(search_time) + "\n")

    #Data searching module
    search_begin = time.time()
    input_tokens12, output_tokens12 = 0, 0
    if not os.path.exists(related_dataset_path):
        queries, datasets, input_tokens12, output_tokens12, full_llm_res = search_datasets(target, model_type, related_dataset_path)
        write_json(full_llm_res, related_dataset_search_queries_path)
        log_file.write("search_datasets: " + str(datasets) + "\n")
        log_file.write("search_datasets_queries: " + str(queries) + "\n")
        write_json(datasets, retrieved_dataset_path)
    print("Data searching token_count: ", input_tokens12, output_tokens12)
    search_end = time.time()
    search_time = search_end - search_begin
    log_file.write("Data searching search_time: "+ str(search_time) + "\n")



    # Literature processing
    input_tokens2, output_tokens2 = 0, 0

    paper_info = read_json(related_paper_path)
    papers = paper_info["download successfully"]

    reports_analysis = ""
    match_id = ""
    pending_papers = copy.deepcopy(papers)
    temp_papers = copy.deepcopy(papers)

    retry_time = 0
    while len(pending_papers) > 0 and retry_time < max_retry_times:
        for index, p in enumerate(pending_papers, start=1):
            report_begin = time.time()
            title = p["title"]
            path = p["path"]
            print("\n\n\nProcessing paper from search phase.\npaper title: {}\npaper path: {}\n".format(title, path))

            name, ext = os.path.splitext(os.path.basename(path))
            report_path = reports_savedir + "/" + name + "_report.json"
            report_log_path = reports_savedir + "/" + name + "_report_log.json"
            analysis_path = reports_savedir + "/" + name + "_analysis.json"
            analysis_log_path = reports_savedir + "/" + name + "_analysis_log.json"
            datasets_path = reports_savedir + "/" + name + "_datasets.json"
            report = generate_report(path, title, report_path, report_log_path)
            if report is not None:
                input_tokens2 += report[1]
                output_tokens2 += report[2]
                if report[3]:
                    report = report[0]
                    temp_papers.remove(p)
                else:
                    continue

            report_end = time.time()
            report_time = report_end - report_begin
            log_file.write("report_time: "+ str(report_time) + "\n")

            analysis_begin = time.time()
            if not os.path.exists(analysis_path):   #待改进
                analysis = analyze(target, conditions, requirements, report, analysis_path, analysis_log_path, datasets_path)
                input_tokens2 += analysis[1]
                output_tokens2 += analysis[2]
                analysis = analysis[0]
                if len(pending_papers) == len(papers):
                    papers[index - 1]['Referability'] = analysis["Referability"]
                else:
                    # retry 第二轮
                    for pp in papers:
                        if pp["title"] == p["title"]:
                            pp["Referability"] = analysis["Referability"]
                            break
            else:
                analysis = read_json(analysis_path)
                papers[index - 1]['Referability'] = analysis["Referability"]
            analysis_end = time.time()
            analysis_time = analysis_end-analysis_begin
            log_file.write("analysis_time: "+ str(analysis_time) + "\n")
        retry_time += 1
        pending_papers = copy.deepcopy(temp_papers)

    if len(pending_papers) > 0:
        print("Warning: There are still papers failed to generate experiment report!\n")
        print(pending_papers)
        #continue_info = input("Would you want to disregard the failed papers and continue with the experimental design? (Input \"no\" to end the process, Input anything else to continue the process.)")
        #if continue_info == "no":
            #exit()
        #else:
            #papers = list(set(papers) - set(pending_papers))
        for pend in pending_papers:
            papers.remove(pend)

    # print("\n\n11-4-报错点：\npapers: \n", json.dumps(papers, ensure_ascii=False, indent=4), "\n\n\n")
    sorted_paper = sorted(papers, key=lambda x: (x['score'], x["Referability"]))
    datasets_from_paper = {"GEO":{}, "TCGA":{}}
    results = {}
    heading_results = {}
    outlines_results = {}
    parts = ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7", "Part 8", "Part 9", "Part 10", "Part 11", "Part 12", "Part 13", "Part 14", "Part 15", "Part 16", "Part 17", "Part 18", "Part 19", "Part 20"]
    for index, p in enumerate(sorted_paper, start=1):
        title = p["title"]
        path = p["path"]
        name, ext = os.path.splitext(os.path.basename(path))
        report_path = reports_savedir + "/" + name + "_report.json"
        report_log_path = reports_savedir + "/" + name + "_report_log.json"
        analysis_path = reports_savedir + "/" + name + "_analysis.json"
        datasets_path = reports_savedir + "/" + name + "_datasets.json"
        paper_datasets = read_json(datasets_path)
        datasets_from_paper['GEO'].update(paper_datasets["useful"]['GEO'])
        datasets_from_paper['TCGA'].update(paper_datasets["useful"]['TCGA'])
        report = read_json(report_path)
        report_log = read_json(report_log_path)
        first_heading = {}
        outlines = {}
        for p in parts:
            if p in report:
                pattern = ': "([^"]+)"?'
                match = re.search(pattern, report[p], re.DOTALL)
                if match:
                    value = match.group(1)
                    #print(value)
                else:
                    print("No match found")
                first_heading[p] = value
            if p in report_log["step2"]["output"]:
                outlines[p] = report_log["step2"]["output"][p]
        analysis = read_json(analysis_path)
        results[name] = {}
        heading_results[name] = {}
        outlines_results[name] = {}
        del analysis["Referability"]
        for k, v in analysis.items():
            del v["Title"]
            #only high
            if v["Referability"].lower() == "high":
                if k in report:
                    part_content = json.loads(report[k])
                    for key, value in part_content.items():
                        if "original text" in part_content[key]:
                            del part_content[key]["original text"]
                        if "results original text" in part_content[key]:
                            del part_content[key]["results original text"]
                    results[name].update({k: part_content, "{} analysis".format(k): v})
                    heading_results[name].update({k: first_heading[k], "{} analysis".format(k): v})
                    if k in outlines:
                        outlines_results[name].update({k: outlines[k], "{} analysis".format(k): v})
                    else:
                        print(f"{k}. parts title not matched.")

            #all
            '''if k in report:
                results[name].update({k: report[k], "{} analysis".format(k): v})'''
        #analysis = json.dumps(analysis)
        match_id += str(index) + ": " + name + "\n"
        #reports_analysis += "Protocol{}: {}\n\nAnalysis{}: {}\n\n".format(index, report, index, analysis)

    # print("token_count: ", input_tokens2, output_tokens2)
    log_file.write("id match: " + match_id + "\n\n")



    for version in ["1", "2", "3"]:
        try:
            design_savepath = os.path.join(work_dir, f"experiment_program{version}.json")
            design_log_path = os.path.join(work_dir, f"experiment_program{version}.log")

            design_translate_savepath = os.path.join(work_dir, f"experiment_program_zh{version}.txt")
            dry_experiment_savepath = os.path.join(work_dir, f"dry_experiment{version}.json")
            dry_experiment_log_path = os.path.join(work_dir, f"dry_experiment{version}.log")
            dry_tranlate_savepath = os.path.join(work_dir, f"dry_experiment_zh{version}.txt")
            code_result_log_path = os.path.join(work_dir, f"coding{version}.log")
            code_save_dir = os.path.join(work_dir, f"coding{version}")
            datasets_savepath = os.path.join(work_dir, f"final_datasets.json")

            #experimental design
            design_begin = time.time()
            dataset = read_json(related_dataset_path)
            datasets = {"GEO": dataset}
            datasets["GEO"].update(datasets_from_paper["GEO"])
            #datasets["TCGA"].update(datasets_from_paper["TCGA"])

            # 存最终所用的数据集
            if not os.path.exists(datasets_savepath):
                write_json(datasets, datasets_savepath)
            else:
                datasets = read_json(datasets_savepath)

            input_tokens3, output_tokens3 = 0, 0
            if not os.path.exists(design_savepath):
                experiments = design(target, conditions, requirements, results, str(heading_results), outlines_results, design_savepath, design_log_path, datasets)
                input_tokens3 += experiments[1]
                output_tokens3 += experiments[2]
                experiments = experiments[0]
            else:
                experiments = read_json(design_savepath)
            design_end = time.time()
            design_time = design_end - design_begin
            log_file.write("design_time: "+ str(design_time) + "\n\n")
            print("token_count: ", input_tokens3, output_tokens3)


            #translation
            design_translation_begin = time.time()
            if not os.path.exists(design_translate_savepath):
                translate(experiments, design_translate_savepath)
            design_translation_end = time.time()
            design_translation_time = design_translation_end - design_translation_begin
            log_file.write("design_translation_time: "+ str(design_translation_time) + "\n")


            #programming: dry experiment extractor
            dry_experiment_extract_begin = time.time()
            input_tokens4, output_tokens4 = 0, 0
            if not os.path.exists(dry_experiment_savepath):
                dry_experiment = dry_experiment_extractor(experiments, dry_experiment_savepath, dry_experiment_log_path)
                input_tokens4 += dry_experiment[1]
                output_tokens4 += dry_experiment[2]
                dry_experiment = dry_experiment[0]
            else:
                dry_experiment = read_json(dry_experiment_savepath)
            dry_experiment_extract_end = time.time()
            dry_experiment_extract_time = dry_experiment_extract_end - dry_experiment_extract_begin
            log_file.write("dry_experiment_extract_time: "+ str(dry_experiment_extract_time) + "\n")

            #translation
            dry_translation_begin = time.time()
            if not os.path.exists(dry_tranlate_savepath):
                translate(dry_experiment, dry_tranlate_savepath)
            dry_translation_end = time.time()
            dry_translation_time = dry_translation_end - dry_translation_begin
            log_file.write("dry_translation_time: "+ str(dry_translation_time) + "\n")
        except Exception as e:
            print(e)



@router.post("/addExperiment")
async def add_experiment(experiment: Experiment, background_tasks: BackgroundTasks):
    try:
        experiment_dict = experiment.model_dump()
        experiment_dict["id"] = generate_id()
        experiments = read_experiments()
        experiments.append(experiment_dict)
        print("write_experiments...")
        write_experiments(experiments)



        # 运行 BioResearcher
        model_type = "gpt-4o-mini-2024-07-18"   # 用户定义
        
        target = experiment_dict["expName"] + "\n" + experiment_dict["expPurpose"]
        conditions = experiment_dict["expCondition"]
        requirements = experiment_dict["expRequirement"]

        background_tasks.add_task(run_bioresearcher, str(experiment_dict["id"]), target, conditions, requirements, model_type)



        return {"message": "Experiment added successfully"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/getExperiments")
async def get_experiments():
    try:
        experiments = read_experiments()
        return experiments
    except Exception as e:
        return {"error": str(e)}


def read_experiments():
    with open(Experiments_File, "r") as f:
        json_data = json.load(f)
        # get the existing ids
        for item in json_data:
            existing_ids.add(item["id"])
        return json_data


def write_experiments(experiments):
    with open(Experiments_File, "w") as f:
        json.dump(experiments, f, indent=4)


def generate_id():
    while True:
        new_id = random.randint(10000, 99999)
        if new_id not in existing_ids:
            existing_ids.add(new_id)
            return new_id

@router.post("/uploadfile")
async def upload_file():
    return {"message": "Upload file here"}



# @router.get("/getSearchModule_paper_back")
# async def get_SearchModule_paper(projectid: Projectid):
#     try:
#         projectid_dict = projectid.model_dump()
#         work_dir = data_dir / projectid_dict["id"]
#         related_paper_savedir = work_dir / "papers"
#         related_paper_path = os.path.join(related_paper_savedir, "related_papers_info.json")
#         retrieved_paper_path = related_paper_savedir / "retrieved_papers_info.json"
#         related_paper_search_queries_path = os.path.join(related_paper_savedir, "related_paper_search_queries_llm_res.json")

#         retrieved_paper = read_json(retrieved_paper_path)

#         return retrieved_paper
#     except Exception as e:
#         return {"error": str(e)}



# 手动重跑
expid = "62367"
target = "Experiment\nClassification of the Immune Microenvironment and Identification of Key Genes in Liposarcoma Based on Transcriptomics"
conditions = "Available Resources: Frozen samples, sarcoma cell lines, and paraffin sections. Data Sources: RNA sequencing data from 80 cases and single-cell sequencing data from 10 cases, along with any publicly available datasets. Animal Experiments: All necessary materials are available if required. Funding: The total funding for the experiment is 200,000 RMB. Computing Resources: Sufficient computing resources are accessible for data analysis"
requirements = "null"
model_type = "gpt-4o-mini-2024-07-18"
run_bioresearcher(expid, target, conditions, requirements, model_type)

