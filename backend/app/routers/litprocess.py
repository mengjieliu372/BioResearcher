from fastapi import APIRouter
from pathlib import Path
import json
import re

router = APIRouter()

files = [
    "cancers-15-03360",
    "1-s2.0-S104366182200408X-main",
    "41467_2024_Article_52067",
]

@router.get("/{id}/paperinfo")
async def get_paperinfo(id: int):
    return get_related_papers_info(id)


@router.get("/{id}/paper-report-analysis")
async def get_paper_report_analysis(id: int, index: int):
    paper_info = get_related_papers_info(id)
    file_name = paper_info[index]['file_name']
    report = get_report(id, file_name)
    analysis = get_analysis(id, file_name)
    return {
        'report': report,
        'analysis': analysis
    }


def get_related_papers_info(id: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    with open(DataFile / "papers" / "related_papers_info.json", 'r', encoding='utf-8') as f:
        related_papers = json.load(f)
    paper_info = []
    for paper in related_papers.get("download successfully", []):
        item = {
            'title': re.sub(r'<[^>]*>', '', paper['title']),  # 去除 HTML 标签
            'file_name': re.search(r'([^/]+)(?=\.[^.]+$)', paper['path']).group(1).strip()  # 获取文件名
        }
        print(item['file_name'])
        if item['file_name'] in files:
            paper_info.append(item)
    return paper_info



def get_report(id, file_name):
    # report_path = os.path.join('../data/reports', f"{file_name}_report.json")
    report_path = Path(__file__).parent.parent / "data" / str(id) / "reports" / f"{file_name}_report.json"
    with open(report_path, 'r', encoding='utf-8') as f:
        report_json = json.load(f)
    json_string = json.dumps(report_json)
    json_string = json_string.replace('\\"', '"').replace('\\n', '').replace('\\u', ' ').replace('\\', '')
    json_string = json_string.replace('"{', '{').replace('}"', '}')
    
    report_json2 = json.loads(json_string)
    return report_json2


def get_analysis(id, file_name):
    # analysis_path = os.path.join('../data/reports', f"{file_name}_analysis.json")
    analysis_path = Path(__file__).parent.parent / "data" / str(id) / "reports" / f"{file_name}_analysis.json"
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis_json = json.load(f)
    
    return analysis_json