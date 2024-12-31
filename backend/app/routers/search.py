from fastapi import APIRouter
from pathlib import Path
import json
import re
router = APIRouter()



@router.get("/{id}/papersets")
async def get_papersets(id: int):
    return process_papersets(id)


@router.get("/{id}/datasets")
async def get_datasets(id: int):
    return process_datasets(id)


def process_papersets(id: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    with open(DataFile / "papers" / "retrieved_papers_info.json", 'r', encoding='utf-8') as f:
        retrieved_papers = json.load(f)
    with open(DataFile / "papers" / "related_papers_info.json", 'r', encoding='utf-8') as f:
        related_papers = json.load(f)
    

    # 要改 search 那里，保留下 query 检索到的 papers
    # with open(DataFile / "papers" / "related_paper_search_queries_llm_res.json", 'r', encoding='utf-8') as f:
    #     search_queries_of_related_papers = json.load(f)
    # queries = search_queries_of_related_papers["0"]["search"]["search_queries"]
    queries = ['query1', 'query2', 'query3', 'query4', 'query5']

    classified_data = []

    # 初始化查询列表
    for query in queries:
        classified_data.append({
            'query': query,
            'papers': []
        })
    downloaded_titles = {item['title'] for item in related_papers["download successfully"]}
    undownloaded_titles = {item['title'] for item in related_papers["download failed"]}
     # 遍历检索的论文
    for index, paper in enumerate(retrieved_papers):
        query_index = index % len(queries)
        
        flag = 1
        if paper['title'] in downloaded_titles:
            flag = 3
        elif paper['title'] in undownloaded_titles:
            flag = 2

        clean_title = re.sub(r'<[^>]*>', '', paper['title'])
        clean_abstract = re.sub(r'<[^>]*>', '', paper['abstract'])
        cleaned_paper = {**paper, 'title': clean_title, 'abstract': clean_abstract, 'flag': flag}
        classified_data[query_index]['papers'].append(cleaned_paper)

    # 按照 flag 从大到小排序
    for query in classified_data:
        query['papers'].sort(key=lambda x: x['flag'], reverse=True)
    
    return classified_data


def process_datasets(id: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    with open(DataFile / "dataset" / "retrieved_datasets_info.json", 'r', encoding='utf-8') as f:
        retrieved_datasets = json.load(f)
    with open(DataFile / "dataset" / "related_datasets_info.json", 'r', encoding='utf-8') as f:
        related_datasets = json.load(f)
    
    queries = ['query1', 'query2', 'query3', 'query4', 'query5']
    classified_data = []

    # 初始化查询列表
    for query in queries:
        classified_data.append({
            'query': query,
            'datasets': {}
        })
    downloaded_datasets = list(related_datasets.keys())

    inner_index = 0
    for category, datasets in retrieved_datasets.items():
        for dataset, info in datasets.items():
            query_index = inner_index % len(queries)
            inner_index += 1
            is_related = dataset in downloaded_datasets
            cleaned_dataset = {**info, 'isRelated': is_related}
            classified_data[query_index]['datasets'][dataset] = cleaned_dataset

    # Sort datasets by 'isRelated' (True comes first)
    for query_data in classified_data:
        query_data['datasets'] = dict(sorted(query_data['datasets'].items(), key=lambda item: not item[1]['isRelated']))

    return classified_data