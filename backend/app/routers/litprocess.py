from fastapi import APIRouter, HTTPException, Header
from pathlib import Path
import json
import re
from app.auth_core import ensure_project_access, require_user

router = APIRouter()


@router.get("/{id}/paperinfo")
async def get_paperinfo(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    return get_related_papers_info(id)


@router.get("/{id}/paper-report-analysis")
async def get_paper_report_analysis(id: int, index: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    paper_info = get_related_papers_info(id)
    if len(paper_info) == 0:
        raise HTTPException(status_code=404, detail="No processed paper reports available yet.")
    if index < 0 or index >= len(paper_info):
        raise HTTPException(status_code=400, detail=f"Invalid paper index: {index}. valid range is 0..{len(paper_info)-1}")
    file_name = paper_info[index]['file_name']
    report = get_report(id, file_name)
    analysis = get_analysis(id, file_name)
    response = merge_report_analysis(report, analysis)
    # response 闁插秵甯撴惔?
    response = sortPartObj(response)
    title = paper_info[index]['title']
    return {
        'title': title,
        'data': response
    }

def sortPartObj(partObj):
    def _sort_key(k: str):
        m = re.search(r"\d+", k or "")
        # Keys with digits first by numeric order, others fall back to lexical order.
        if m:
            return (0, int(m.group()), k)
        return (1, 10**9, k)

    sorted_keys = sorted(partObj.keys(), key=_sort_key)
    sorted_dict = {key: partObj[key] for key in sorted_keys}
    return sorted_dict

def get_existed_files(id: int):
    file_path = Path(__file__).parent.parent / "data" / str(id) / "reports"
    files = [
        re.sub(r'_report\.json$', '', f.name)
        for f in file_path.glob('*report.json')
    ]
    return files


def get_related_papers_info(id: int):
    files = get_existed_files(id)
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    related_file = DataFile / "papers" / "related_papers_info.json"
    if not related_file.exists():
        return []
    with open(related_file, 'r', encoding='utf-8') as f:
        related_papers = json.load(f)
    paper_info = []
    for paper in related_papers.get("download successfully", []):
        paper_path = str(paper.get("path") or "")
        if not paper_path:
            continue
        item = {
            'title': re.sub(r'<[^>]*>', '', paper.get('title', '')),
            'file_name': Path(paper_path).stem.strip(),
        }
        if item['file_name'] in files:
            paper_info.append(item)
    return paper_info



def get_report(id, file_name):
    report_path = Path(__file__).parent.parent / "data" / str(id) / "reports" / f"{file_name}_report.json"
    report = clean_json_file(report_path)
    return report


def get_analysis(id, file_name):
    analysis_path = Path(__file__).parent.parent / "data" / str(id) / "reports" / f"{file_name}_analysis.json"
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis_json = json.load(f)
    return analysis_json


def clean_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        json_string = f.read()
    """
    report = re.sub(r'\\\\n', '', report)
    report = re.sub(r'\\\\\\"', "'", report)
    report = re.sub(r'\\n', '', report)
    report = re.sub(r'\\"', '"', report)
    report = re.sub(r'"{', '{', report)
    report = re.sub(r'}"', '}', report)
    report = json.loads(report)
    """
    json_string = re.sub(r'\\\\n', '', json_string)
    json_string = re.sub(r'\\\\\\"', "'", json_string)
    json_string = re.sub(r'\\n', '', json_string)
    json_string = re.sub(r'\\"', '"', json_string)
    json_string = re.sub(r'"{', '{', json_string)
    json_string = re.sub(r'}"', '}', json_string)
    json_string = json.loads(json_string)
    return json_string

def merge_report_analysis(report, analysis):
    fields_to_insert = ["Reason", "Suggestions", "Referability"]
    for part, part_data in report.items():
        if part in analysis:
            for field in fields_to_insert:
                if field in analysis[part]:
                    part_data[field] = analysis[part][field]
    return report
