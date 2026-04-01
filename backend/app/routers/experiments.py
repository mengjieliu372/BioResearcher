from fastapi import APIRouter, BackgroundTasks, Header
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import json
import random
import threading
import time
from datetime import datetime

import os
import copy
import re
from app.models.search_download import *
from app.models.literature_process import *
from app.models.experimental_design import *
from app.models.programming import *
from app.models.our_utils import *
from app.models.translate_zh import translate
import app.models.GEO_API_test as GEO_API_test
from app.auth_core import (
    EXAMPLE_PROJECT_ID,
    _db_conn,
    ensure_project_access,
    generate_unique_experiment_id,
    list_projects_for_user,
    require_user,
)

router = APIRouter()


Experiments_File = Path(__file__).parent.parent / "data" / "experiments.json"
data_dir = Path(__file__).parent.parent / "data"
existing_ids = set()
PROCESS_FLAG_DEFAULTS = {
    "page_search_paper": False,
    "page_search_datasets": False,
    "page_Literature_processing": False,
    "page_design_1": False,
    "page_design_2": False,
    "page_design_3": False,
    "page_dry_1": False,
    "page_dry_2": False,
    "page_dry_3": False,
    "page_coding_1": False,
    "page_coding_2": False,
    "page_coding_3": False,
}
RUNNING_EXPERIMENTS = set()
RUNNING_LOCK = threading.Lock()
STOP_REQUESTED_EXPERIMENTS = set()

RUNTIME_STATUS_DEFAULTS = {
    "running": False,
    "progress": 0,
    "message": "Idle",
    "checkpoint": "init",
    "error": None,
    "updated_at": "",
}
RUNTIME_STALE_SECONDS = int(os.getenv("RUNTIME_STALE_SECONDS", "900"))
RUNTIME_STALE_SECONDS_HEAVY = int(os.getenv("RUNTIME_STALE_SECONDS_HEAVY", "3600"))
RUNTIME_STALE_SECONDS_CODING = int(os.getenv("RUNTIME_STALE_SECONDS_CODING", "7200"))


class PaperSet(BaseModel):
    PMC: bool
    PubMed: bool

class Dataset(BaseModel):
    GEO: bool
    NCBI: bool
    cBioPortal: bool

class Experiment(BaseModel):
    id: int
    expName: str
    expPurpose: str
    expCondition: str
    expRequirement: str
    paperset: PaperSet
    dataset: Dataset
    llmModel: str
    refNum: Optional[int] = None
    reviewerRound: Optional[int] = None
    fileNames: List[str]


def with_progress_defaults(experiment: dict) -> dict:
    for key, default_value in PROCESS_FLAG_DEFAULTS.items():
        experiment.setdefault(key, default_value)
    return experiment


def experiment_all_done(experiment: dict) -> bool:
    return (
        bool(experiment.get("page_search_paper", False))
        and bool(experiment.get("page_search_datasets", False))
        and bool(experiment.get("page_Literature_processing", False))
        and all(bool(experiment.get(k, False)) for k in ["page_design_1", "page_design_2", "page_design_3"])
        and all(bool(experiment.get(k, False)) for k in ["page_dry_1", "page_dry_2", "page_dry_3"])
        and bool(experiment.get("page_coding_3", False))
    )


def resolve_model_type(llm_model: str) -> str:
    model_map = {
        "chatgpt5.x": MODEL_NANO,
        "gpt-4o-mini": MODEL_4O_MINI,
        "gpt-5-mini": MODEL_5_MINI,
        "gpt-5.2": MODEL_PRECISE,
        "gpt-5.2-codex": MODEL_CODEX,
        # Backward compatibility for old frontend values / history data.
        "gpt4o": MODEL_4O_MINI,
        "gemini": MODEL_4O_MINI,
        "claude": MODEL_4O_MINI,
    }
    key = (llm_model or "").strip().lower()
    return model_map.get(key, MODEL_4O_MINI)


def runtime_status_path(expid: str) -> Path:
    return data_dir / str(expid) / "runtime_status.json"


def read_runtime_status(expid: str) -> dict:
    p = runtime_status_path(expid)
    if not p.exists():
        return dict(RUNTIME_STATUS_DEFAULTS)
    try:
        data = read_json(p)
        out = dict(RUNTIME_STATUS_DEFAULTS)
        out.update(data)
        return out
    except Exception:
        return dict(RUNTIME_STATUS_DEFAULTS)


def write_runtime_status(expid: str, **kwargs):
    p = runtime_status_path(expid)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = read_runtime_status(expid)
    data.update(kwargs)
    data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    write_json(data, p)


def is_runtime_stale(runtime_status: dict) -> bool:
    if not runtime_status.get("running"):
        return False
    updated_at = runtime_status.get("updated_at") or ""
    if not updated_at:
        return True
    checkpoint = str(runtime_status.get("checkpoint", "")).lower()
    timeout_sec = RUNTIME_STALE_SECONDS
    if checkpoint.startswith("coding_"):
        timeout_sec = RUNTIME_STALE_SECONDS_CODING
    elif checkpoint.startswith("literature") or checkpoint.startswith("design_") or checkpoint.startswith("dry_"):
        timeout_sec = RUNTIME_STALE_SECONDS_HEAVY
    try:
        dt = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        return (now - dt).total_seconds() > timeout_sec
    except Exception:
        return True


class ExperimentPausedError(Exception):
    pass


def request_stop(expid: str):
    with RUNNING_LOCK:
        STOP_REQUESTED_EXPERIMENTS.add(str(expid))


def clear_stop_request(expid: str):
    with RUNNING_LOCK:
        STOP_REQUESTED_EXPERIMENTS.discard(str(expid))


def is_stop_requested(expid: str) -> bool:
    with RUNNING_LOCK:
        return str(expid) in STOP_REQUESTED_EXPERIMENTS


def abort_if_stop_requested(expid: str):
    if is_stop_requested(expid):
        write_runtime_status(
            expid,
            running=False,
            checkpoint="paused_by_user",
            message="Paused by user. You can resume later.",
            error=None,
        )
        raise ExperimentPausedError("Paused by user.")


def _extract_geo_accessions_from_dry(dry_experiment: dict) -> list[str]:
    hits = []
    if not isinstance(dry_experiment, dict):
        return hits
    for _, tasks in dry_experiment.items():
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            text = json.dumps(task, ensure_ascii=False)
            for acc in re.findall(r"\bGSE\d{4,}\b", text, flags=re.IGNORECASE):
                acc = acc.upper()
                if acc not in hits:
                    hits.append(acc)
    return hits


def _collect_local_geo_accessions(data_dir_path: str) -> set[str]:
    found = set()
    p = Path(data_dir_path)
    if not p.exists():
        return found
    for f in p.iterdir():
        if not f.is_file():
            continue
        m = re.match(r"^(GSE\d{4,})", f.name, flags=re.IGNORECASE)
        if m:
            found.add(m.group(1).upper())
    return found


def _preflight_download_required_geo(
    dry_experiment: dict,
    work_dir: str,
    related_dataset_path: str,
    datasets_manifest_path: str,
) -> dict:
    """
    Validate required GEO accessions before coding starts.
    - Determine required accessions from dry task descriptions.
    - Compare with local /data files in this project.
    - Attempt download for missing accessions with existing GEO downloader.
    """
    report = {
        "required_accessions": [],
        "local_accessions_before": [],
        "missing_accessions_before_download": [],
        "download_attempted_accessions": [],
        "download_succeeded_accessions": [],
        "still_missing_accessions": [],
        "status": "ok",
        "error": None,
    }
    data_dir_path = os.path.join(work_dir, "data")
    os.makedirs(data_dir_path, exist_ok=True)

    required = _extract_geo_accessions_from_dry(dry_experiment)
    local_before = _collect_local_geo_accessions(data_dir_path)
    missing = [x for x in required if x not in local_before]

    report["required_accessions"] = required
    report["local_accessions_before"] = sorted(local_before)
    report["missing_accessions_before_download"] = missing

    if not missing:
        return report

    details = {}
    for acc in missing:
        try:
            info = GEO_API_test.get_details_and_download_links(acc)
            if isinstance(info, dict) and info.get("Supplementary file"):
                details[acc] = info
                report["download_attempted_accessions"].append(acc)
        except Exception as e:
            report["error"] = f"{report['error']}; {acc}:{e}" if report["error"] else f"{acc}:{e}"

    if details:
        try:
            GEO_API_test.geo_download_dataset(details, str(work_dir), manifest_path=datasets_manifest_path)
        except Exception as e:
            report["error"] = f"{report['error']}; download:{e}" if report["error"] else f"download:{e}"

    local_after = _collect_local_geo_accessions(data_dir_path)
    succeeded = [x for x in missing if x in local_after]
    still_missing = [x for x in missing if x not in local_after]
    report["download_succeeded_accessions"] = succeeded
    report["still_missing_accessions"] = still_missing
    if still_missing:
        report["status"] = "incomplete"
    return report


def run_bioresearcher_safe(expid: str, target: str, conditions: str, requirements: str, model_type: str):
    if str(expid) == str(EXAMPLE_PROJECT_ID):
        write_runtime_status(
            expid,
            running=False,
            progress=100,
            checkpoint="done",
            message="Example project is read-only demo. Existing outputs are presented directly.",
            error=None,
        )
        return
    with RUNNING_LOCK:
        if expid in RUNNING_EXPERIMENTS:
            return
        RUNNING_EXPERIMENTS.add(expid)
    clear_stop_request(expid)
    write_runtime_status(
        expid,
        running=True,
        message="Starting or resuming task...",
        checkpoint="start",
        error=None,
    )
    try:
        run_bioresearcher(expid, target, conditions, requirements, model_type)
        experiments = read_experiments()
        exp_row = next((exp for exp in experiments if str(exp.get("id")) == str(expid)), None)
        if exp_row and experiment_all_done(exp_row):
            write_runtime_status(
                expid,
                running=False,
                progress=100,
                checkpoint="done",
                message="All tasks completed.",
                error=None,
            )
        else:
            write_runtime_status(
                expid,
                running=False,
                checkpoint="partial_done",
                message="Task finished with partial outputs. Please check stage flags.",
                error=None,
            )
    except ExperimentPausedError:
        write_runtime_status(
            expid,
            running=False,
            checkpoint="paused_by_user",
            message="Paused by user. You can resume later.",
            error=None,
        )
    except Exception as e:
        write_runtime_status(
            expid,
            running=False,
            message="Task interrupted.",
            error=str(e),
        )
        raise
    finally:
        with RUNNING_LOCK:
            RUNNING_EXPERIMENTS.discard(expid)



def run_bioresearcher(expid: str, target: str, conditions: str, requirements: str, model_type: str):
    print("start generating protocol...")
    expid_int = int(expid)
    work_dir = data_dir / expid
    abort_if_stop_requested(expid)
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
    write_runtime_status(expid, progress=3, checkpoint="prepare_dirs", message="Workspace prepared.")
    abort_if_stop_requested(expid)

    #Literature searching module
    print("start search paper...")
    write_runtime_status(expid, progress=8, checkpoint="search_paper_start", message="Searching papers...")
    abort_if_stop_requested(expid)
    search_begin = time.time()
    input_tokens1, output_tokens1 = 0, 0
    if not os.path.exists(related_paper_path):
        queries, input_tokens1, output_tokens1, flag, full_llm_res = search_download(target, conditions, requirements, model_type, retmax=2, savedir=related_paper_savedir, retrieved_paper_info_path=retrieved_paper_path, related_paper_info_path=related_paper_path)     # retmax: 濠碘槅鍋€閸嬫挾绱掓笟鍨仾妞ゆ劕銈稿顐ゆ暜椤斿墽顦梺娲绘娇閸斿秹宕哄☉銏犵煑妞ゆ牜鍋愰崑鎾村緞婵犲嫭姣庢繛?
        write_json(full_llm_res, related_paper_search_queries_path)
        log_file.write("search_queries: " + str(queries) + "\n")
        if not flag:
            print(f"Warning: There are some papers that failed to download, please download them manually!")
    print("generating search query token_count: ", input_tokens1, output_tokens1)
    search_end = time.time()
    search_time = search_end - search_begin
    log_file.write("generating search query search_time: "+ str(search_time) + "\n")

    # Literature searching datasets 闁哄鏅滈崝姗€銆侀幋鐘亾閻熺増婀伴柣?
    exp_file = read_json(data_dir / "experiments.json")
    for tup in exp_file:
        if int(tup["id"]) == expid_int:
            tup["page_search_paper"] = True
            break
    write_json(exp_file, data_dir / "experiments.json")
    write_runtime_status(expid, progress=20, checkpoint="search_paper_done", message="Paper search finished.")
    abort_if_stop_requested(expid)


    #Data searching module
    write_runtime_status(expid, progress=24, checkpoint="search_dataset_start", message="Searching datasets...")
    abort_if_stop_requested(expid)
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

    # Literature searching datasets 闁哄鏅滈崝姗€銆侀幋鐘亾閻熺増婀伴柣?
    exp_file = read_json(data_dir / "experiments.json")
    for tup in exp_file:
        if int(tup["id"]) == expid_int:
            tup["page_search_datasets"] = True
            break
    write_json(exp_file, data_dir / "experiments.json")
    write_runtime_status(expid, progress=34, checkpoint="search_dataset_done", message="Dataset search finished.")
    abort_if_stop_requested(expid)


    # Literature processing
    write_runtime_status(expid, progress=38, checkpoint="literature_start", message="Processing literature...")
    abort_if_stop_requested(expid)
    input_tokens2, output_tokens2 = 0, 0

    # Backward compatibility: if previous runs failed all downloads,
    # regenerate fallback text files so the pipeline can continue.
    if os.path.exists(related_paper_path):
        paper_info = read_json(related_paper_path)
        if len(paper_info.get("download successfully", [])) == 0 and len(paper_info.get("download failed", [])) > 0:
            print("No downloadable PDFs found, generating fallback text files for failed papers...")
            download_paper(paper_info.get("download failed", []), related_paper_savedir, related_paper_path)

    paper_info = read_json(related_paper_path)
    # Normalize stale absolute paths (e.g., copied projects from another machine/id) to current papers dir.
    changed_paths = False
    for section in ["download successfully", "download failed"]:
        items = paper_info.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            raw_path = item.get("path", "")
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            filename = os.path.basename(raw_path.replace("\\", "/"))
            if not filename:
                continue
            current_local_path = os.path.join(related_paper_savedir, filename)
            if os.path.exists(current_local_path) and os.path.abspath(raw_path) != os.path.abspath(current_local_path):
                item["path"] = current_local_path
                changed_paths = True
    if changed_paths:
        write_json(paper_info, related_paper_path)

    papers = paper_info["download successfully"]

    reports_analysis = ""
    match_id = ""
    pending_papers = copy.deepcopy(papers)
    temp_papers = copy.deepcopy(papers)

    retry_time = 0
    while len(pending_papers) > 0 and retry_time < max_retry_times:
        for index, p in enumerate(pending_papers, start=1):
            abort_if_stop_requested(expid)
            report_begin = time.time()
            title = p["title"]
            path = p["path"]
            if not os.path.exists(path):
                filename = os.path.basename(str(path).replace("\\", "/"))
                candidate = os.path.join(related_paper_savedir, filename) if filename else ""
                if candidate and os.path.exists(candidate):
                    path = candidate
                    p["path"] = path
                else:
                    print(f"Skipping missing paper path: {path}")
                    if p in temp_papers:
                        temp_papers.remove(p)
                    continue
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
            if not os.path.exists(analysis_path):   #閻庡灚婢橀幊蹇涘极閸忓吋浜?
                analysis = analyze(target, conditions, requirements, report, analysis_path, analysis_log_path, datasets_path)
                input_tokens2 += analysis[1]
                output_tokens2 += analysis[2]
                analysis = analysis[0]
                if len(pending_papers) == len(papers):
                    papers[index - 1]['Referability'] = analysis["Referability"]
                else:
                    # retry 缂備焦顨忛崗娑氳姳閳哄倹濮?
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

    # print("\n\n11-4-闂佺缈伴崕鐢稿极婵犲洦鍊烽柣褍鎽滅粣姊妌papers: \n", json.dumps(papers, ensure_ascii=False, indent=4), "\n\n\n")
    sorted_paper = sorted(papers, key=lambda x: (x['score'], x["Referability"]))
    datasets_from_paper = {"GEO":{}, "TCGA":{}}
    results = {}
    heading_results = {}
    outlines_results = {}
    parts = ["Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6", "Part 7", "Part 8", "Part 9", "Part 10", "Part 11", "Part 12", "Part 13", "Part 14", "Part 15", "Part 16", "Part 17", "Part 18", "Part 19", "Part 20"]
    for index, p in enumerate(sorted_paper, start=1):
        abort_if_stop_requested(expid)
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
        if len(sorted_paper) > 0:
            p_progress = 38 + int((index / len(sorted_paper)) * 22)
            write_runtime_status(
                expid,
                progress=min(60, p_progress),
                checkpoint="literature_processing",
                message=f"Literature processed: {index}/{len(sorted_paper)}",
            )
        #reports_analysis += "Protocol{}: {}\n\nAnalysis{}: {}\n\n".format(index, report, index, analysis)

    # print("token_count: ", input_tokens2, output_tokens2)
    log_file.write("id match: " + match_id + "\n\n")


    # Literature processing 闁哄鏅滈崝姗€銆侀幋鐘亾閻熺増婀伴柣?
    exp_file = read_json(data_dir / "experiments.json")
    for tup in exp_file:
        if int(tup["id"]) == expid_int:
            tup["page_Literature_processing"] = True
            break
    write_json(exp_file, data_dir / "experiments.json")
    write_runtime_status(expid, progress=62, checkpoint="literature_done", message="Literature processing finished.")



    input_tokens5, output_tokens5 = 0, 0
    for version in ["1", "2", "3"]:
        abort_if_stop_requested(expid)
        try:
            v = int(version)
            write_runtime_status(expid, progress=62 + v * 2, checkpoint=f"design_v{version}_start", message=f"Design/Dry pipeline v{version} running...")
            design_savepath = os.path.join(work_dir, f"experiment_program{version}.json")
            design_log_path = os.path.join(work_dir, f"experiment_program{version}.log")

            design_translate_savepath = os.path.join(work_dir, f"experiment_program_zh{version}.txt")
            dry_experiment_savepath = os.path.join(work_dir, f"dry_experiment{version}.json")
            dry_experiment_log_path = os.path.join(work_dir, f"dry_experiment{version}.log")
            dry_tranlate_savepath = os.path.join(work_dir, f"dry_experiment_zh{version}.txt")
            code_result_log_path = os.path.join(work_dir, f"coding{version}.log")
            code_save_dir = os.path.join(work_dir, f"coding{version}")
            datasets_savepath = os.path.join(work_dir, f"final_datasets.json")
            datasets_manifest_path = os.path.join(work_dir, "datasets_manifest.json")

            #experimental design
            design_begin = time.time()
            dataset = read_json(related_dataset_path)
            datasets = {"GEO": dataset}
            datasets["GEO"].update(datasets_from_paper["GEO"])
            #datasets["TCGA"].update(datasets_from_paper["TCGA"])

            # 闁诲孩绋掕摫婵炴挸澧庣槐鎺楀醇閻斿鏆￠梺娲绘娇閸斿骸鈻撻幋锕€鏋侀柣妤€鐗嗙粊锕傛⒒?
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

            # 婵炴垶鎸撮崑鎾绘煟?Design 闁哄鏅滈崝姗€銆侀幋鐘亾閻熺増婀伴柣?
            exp_file = read_json(data_dir / "experiments.json")
            for tup in exp_file:
                if int(tup["id"]) == expid_int:
                    temp_key = "page_design_" + version
                    tup[temp_key] = True
                    break
            write_json(exp_file, data_dir / "experiments.json")
            write_runtime_status(expid, progress=68 + v * 7, checkpoint=f"design_v{version}_done", message=f"Design v{version} completed.")


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

            # 婵炴垶鎸撮崑鎾绘煟?dry experiment extractor 闁哄鏅滈崝姗€銆侀幋鐘亾閻熺増婀伴柣?
            exp_file = read_json(data_dir / "experiments.json")
            for tup in exp_file:
                if int(tup["id"]) == expid_int:
                    temp_key = "page_dry_" + version
                    tup[temp_key] = True
                    break
            write_json(exp_file, data_dir / "experiments.json")
            write_runtime_status(expid, progress=72 + v * 7, checkpoint=f"dry_v{version}_done", message=f"Dry experiment v{version} completed.")


            #translation
            dry_translation_begin = time.time()
            if not os.path.exists(dry_tranlate_savepath):
                translate(dry_experiment, dry_tranlate_savepath)
            dry_translation_end = time.time()
            dry_translation_time = dry_translation_end - dry_translation_begin
            log_file.write("dry_translation_time: "+ str(dry_translation_time) + "\n")

            total_input_tokens = input_tokens1+input_tokens2+input_tokens3+input_tokens4
            total_output_tokens = output_tokens1+output_tokens2+output_tokens3+output_tokens4
            print("total_tokens: ", total_input_tokens, total_output_tokens)


            #programming: coding
            if version == "3":
                write_runtime_status(
                    expid,
                    checkpoint="dataset_download_start",
                    message="Downloading selected datasets with storage budget limits...",
                )
                try:
                    if not os.path.exists(datasets_manifest_path):
                        geo_details = datasets.get("GEO", {})
                        GEO_API_test.geo_download_dataset(
                            geo_details,
                            str(work_dir),
                            manifest_path=datasets_manifest_path,
                        )
                    write_runtime_status(
                        expid,
                        checkpoint="dataset_download_done",
                        message="Dataset download stage completed.",
                    )
                except Exception as e:
                    write_runtime_status(
                        expid,
                        checkpoint="dataset_download_warning",
                        message=f"Dataset download warning: {e}",
                        error=str(e),
                    )

                # Preflight: confirm required GEO accessions for dry tasks before entering coding.
                write_runtime_status(
                    expid,
                    checkpoint="coding_preflight_start",
                    message="Preflight checking required datasets before coding...",
                    error=None,
                )
                preflight_report = _preflight_download_required_geo(
                    dry_experiment=dry_experiment,
                    work_dir=str(work_dir),
                    related_dataset_path=related_dataset_path,
                    datasets_manifest_path=datasets_manifest_path,
                )
                preflight_path = os.path.join(work_dir, "coding_preflight_report.json")
                write_json(preflight_report, preflight_path)
                if preflight_report.get("still_missing_accessions"):
                    write_runtime_status(
                        expid,
                        checkpoint="coding_preflight_incomplete",
                        message=(
                            "Dataset preflight incomplete. Missing accessions: "
                            + ", ".join(preflight_report.get("still_missing_accessions", []))
                        ),
                        error=preflight_report.get("error"),
                    )
                else:
                    write_runtime_status(
                        expid,
                        checkpoint="coding_preflight_done",
                        message="Dataset preflight finished. Starting coding generation...",
                        error=None,
                    )

                coding_begin = time.time()
                code = code_generator(dry_experiment, code_result_log_path, code_save_dir, model=MODEL_CODEX)
                input_tokens5 += code[1]
                output_tokens5 += code[2]
                print("coding token_count: ", input_tokens5, output_tokens5)
                coding_end = time.time()
                coding_time = coding_end-coding_begin
                log_file.write("coding time: "+ str(coding_time) + "\n")

            if version != "3":
                continue

            # 婵炴垶鎸撮崑鎾绘煟?coding 闁哄鏅滈崝姗€銆侀幋鐘亾閻熺増婀伴柣?
            exp_file = read_json(data_dir / "experiments.json")
            for tup in exp_file:
                if int(tup["id"]) == expid_int:
                    temp_key = "page_coding_" + version
                    tup[temp_key] = True
                    break
            write_json(exp_file, data_dir / "experiments.json")
            write_runtime_status(expid, progress=min(98, 78 + v * 7), checkpoint=f"coding_v{version}_done", message=f"Coding v{version} completed.")


        except Exception as e:
            print(e)
            write_runtime_status(expid, checkpoint=f"version_{version}_warning", message=f"Warning on version {version}: {e}", error=str(e))

    # After run, merge any project-local GEO downloads into shared repo and
    # clear local duplicates from `<project>/data`.
    try:
        consolidate_report = GEO_API_test.consolidate_project_data_to_shared(str(work_dir), remove_local=True)
        log_file.write("consolidate_project_data_to_shared: " + json.dumps(consolidate_report, ensure_ascii=False) + "\n")
    except Exception as e:
        log_file.write(f"consolidate_project_data_to_shared failed: {e}\n")

    log_file.close()

def grant_project_to_user(user_id: int, project_id: int, alias_name: str | None = None):
    now = int(time.time())
    conn = _db_conn()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_project_access (user_id, project_id, alias_name, granted_at)
            VALUES (?, ?, ?, ?)
            """,
            (int(user_id), int(project_id), alias_name, now),
        )
        conn.commit()
    finally:
        conn.close()

@router.get("/{id}/experiment")
async def get_experiment(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    experiments = read_experiments()
    experiment = next((exp for exp in experiments if exp["id"] == id), None)
    if experiment is None:
        return {"message": f"Experiment {id} not found"}
    return experiment


@router.post("/addExperiment")
async def add_experiment(
    experiment: Experiment,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
):
    user = require_user(authorization)
    try:
        experiment_dict = with_progress_defaults(experiment.model_dump())
        experiments = read_experiments()
        existing = {int(x.get("id")) for x in experiments if isinstance(x, dict) and "id" in x}
        experiment_dict["id"] = generate_unique_experiment_id(existing)
        experiment_dict["owner_username"] = user.get("username")
        experiments = read_experiments()
        experiments.append(experiment_dict)
        write_experiments(experiments)
        grant_project_to_user(int(user["id"]), int(experiment_dict["id"]))


        # 闁哄鏅滈崝姗€銆?BioResearcher
        model_type = resolve_model_type(experiment_dict.get("llmModel", "chatgpt5.x"))
        
        target = experiment_dict["expName"] + "\n" + experiment_dict["expPurpose"]
        conditions = experiment_dict["expCondition"]
        requirements = experiment_dict["expRequirement"]

        write_runtime_status(
            str(experiment_dict["id"]),
            running=True,
            progress=1,
            checkpoint="queued",
            message="Task queued...",
            error=None,
        )
        background_tasks.add_task(run_bioresearcher_safe, str(experiment_dict["id"]), target, conditions, requirements, model_type)



        return {"message": "Experiment added successfully", "id": experiment_dict["id"]}
    except Exception as e:
        return {"error": str(e)}


@router.post("/{id}/resume")
async def resume_experiment(id: int, background_tasks: BackgroundTasks, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    if int(id) == int(EXAMPLE_PROJECT_ID):
        write_runtime_status(
            str(id),
            running=False,
            progress=100,
            checkpoint="done",
            message="Example project is read-only demo. Existing outputs are presented directly.",
            error=None,
        )
        return {"message": "Example project is demo-only; no backend execution triggered.", "running": False}
    experiments = read_experiments()
    experiment = next((exp for exp in experiments if exp["id"] == id), None)
    if experiment is None:
        return {"error": f"Experiment {id} not found"}

    expid = str(id)
    is_done = (
        bool(experiment.get("page_search_paper", False))
        and bool(experiment.get("page_search_datasets", False))
        and bool(experiment.get("page_Literature_processing", False))
        and all(bool(experiment.get(k, False)) for k in ["page_design_1", "page_design_2", "page_design_3"])
        and all(bool(experiment.get(k, False)) for k in ["page_dry_1", "page_dry_2", "page_dry_3"])
        and bool(experiment.get("page_coding_3", False))
    )
    if is_done:
        return {"message": "Experiment already completed", "running": False}

    status = read_runtime_status(expid)
    if is_runtime_stale(status):
        write_runtime_status(
            expid,
            running=False,
            message="Detected stale runtime status. Ready to resume.",
            checkpoint="stale_reset",
            error=status.get("error"),
        )
        status = read_runtime_status(expid)
    with RUNNING_LOCK:
        already_running = expid in RUNNING_EXPERIMENTS
    if already_running or status.get("running"):
        return {"message": "Experiment is already running", "running": True}

    model_type = resolve_model_type(experiment.get("llmModel", "chatgpt5.x"))
    target = experiment["expName"] + "\n" + experiment["expPurpose"]
    conditions = experiment["expCondition"]
    requirements = experiment["expRequirement"]
    clear_stop_request(expid)
    write_runtime_status(expid, running=True, checkpoint="queued", message="Resume queued...", error=None)
    background_tasks.add_task(run_bioresearcher_safe, expid, target, conditions, requirements, model_type)
    return {"message": "Experiment resume started", "running": True}


@router.post("/{id}/pause")
async def pause_experiment(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    experiments = read_experiments()
    experiment = next((exp for exp in experiments if exp["id"] == id), None)
    if experiment is None:
        return {"error": f"Experiment {id} not found"}

    expid = str(id)
    request_stop(expid)
    status = read_runtime_status(expid)
    if status.get("running"):
        write_runtime_status(
            expid,
            running=False,
            checkpoint="pause_requested",
            message="Pause requested. Current stage will stop safely.",
            error=None,
        )
        return {"message": "Pause requested", "running": False}

    write_runtime_status(
        expid,
        running=False,
        checkpoint="paused_by_user",
        message="Paused by user. You can resume later.",
        error=None,
    )
    return {"message": "Experiment paused", "running": False}

@router.get("/getExperiments")
async def get_experiments(authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    try:
        experiments = read_experiments()
        return list_projects_for_user(user, experiments)
    except Exception as e:
        return {"error": str(e)}

# 闂佸搫娲ら悺銊╁蓟婵犲洤钃熼柟閭︿邯閸ゅ鎮楅崷顓炰槐闁绘稒鐟︾粚閬嶅焺閸愌呯
@router.put("/updateExperiment")
async def update_experiment(experiment: Experiment, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, int(experiment.id))
    try:
        experiments = read_experiments()
        updated_experiment = experiment.model_dump()
        for i in range(len(experiments)):
            if experiments[i]["id"] == experiment.id:
                merged_experiment = {**experiments[i], **updated_experiment}
                merged_experiment["owner_username"] = experiments[i].get("owner_username") or user.get("username")
                experiments[i] = with_progress_defaults(merged_experiment)
                write_experiments(experiments)
                return {"message": "Experiment updated successfully"}
        return {"error": "Experiment not found"}
    except Exception as e:
        return {"error": str(e)}


# 闂佸憡甯炴繛鈧繛鍛叄瀵骞囬鍫濇疂闁诲骸婀遍崑銈夋偘?
@router.delete("/deleteExperiment")
async def delete_experiment(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    try:
        experiments = read_experiments()
        for i in range(len(experiments)):
            if experiments[i]["id"] == id:
                experiments.pop(i)
                write_experiments(experiments)
                return {"message": "Experiment deleted successfully"}
        return {"error": "Experiment not found"}
    except Exception as e:
        return {"error": str(e)}

def read_experiments():
    with open(Experiments_File, "r", encoding="utf-8-sig") as f:
        json_data = json.load(f)
    if isinstance(json_data, dict):
        json_data = [json_data]
    elif not isinstance(json_data, list):
        json_data = []

    updated = False
    filtered = []
    # get the existing ids
    for item in json_data:
        pid = item.get("id")
        pid_int = None
        project_dir_exists = False
        try:
            pid_int = int(pid)
            project_dir_exists = (data_dir / str(pid_int)).exists()
        except Exception:
            project_dir_exists = False
        # Keep Example project even if data folder is temporarily missing.
        if not project_dir_exists and pid_int != int(EXAMPLE_PROJECT_ID):
            updated = True
            continue
        filtered.append(item)
        existing_ids.add(item["id"])
        before_len = len(item)
        with_progress_defaults(item)
        if "owner_username" not in item:
            item["owner_username"] = "system"
        if len(item) != before_len:
            updated = True

    json_data = filtered
    if updated:
        write_experiments(json_data)
    return json_data


def write_experiments(experiments):
    with open(Experiments_File, "w", encoding="utf-8") as f:
        json.dump(experiments, f, indent=4)


def generate_id():
    while True:
        new_id = random.randint(10000, 99999)
        if new_id not in existing_ids:
            existing_ids.add(new_id)
            return new_id

