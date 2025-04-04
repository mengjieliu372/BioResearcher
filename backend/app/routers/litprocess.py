from fastapi import APIRouter
from pathlib import Path
import json
import re

router = APIRouter()


@router.get("/{id}/paperinfo")
async def get_paperinfo(id: int):
    return get_related_papers_info(id)


@router.get("/{id}/paper-report-analysis")
async def get_paper_report_analysis(id: int, index: int):
    paper_info = get_related_papers_info(id)
    file_name = paper_info[index]['file_name']
    report = get_report(id, file_name)
    analysis = get_analysis(id, file_name)
    response = merge_report_analysis(report, analysis)
    # response 重排序
    response = sortPartObj(response)
    title = paper_info[index]['title']
    return {
        'title': title,
        'data': response
    }

def sortPartObj(partObj):
    sorted_keys = sorted(partObj.keys(), key=lambda x: int(re.search(r'\d+', x).group()))
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
    with open(DataFile / "papers" / "related_papers_info.json", 'r', encoding='utf-8') as f:
        related_papers = json.load(f)
    paper_info = []
    for paper in related_papers.get("download successfully", []):
        item = {
            'title': re.sub(r'<[^>]*>', '', paper['title']),  # 去除 HTML 标签
            'file_name': re.search(r'([^/]+)(?=\.[^.]+$)', paper['path']).group(1).strip()  # 获取文件名
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