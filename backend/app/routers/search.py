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
    downloaded_titles = {item['title'] for item in related_papers["download successfully"]}
    undownloaded_titles = {item['title'] for item in related_papers["download failed"]}
    """
    with open(DataFile / "papers" / "related_paper_search_queries_llm_res.json", 'r', encoding='utf-8') as f:
        search_queries_of_related_papers = json.load(f)
    queries = search_queries_of_related_papers["0"]["search"]["search_queries"]
    """

    # query = "(\"well-differentiated liposarcoma\" OR \"dedifferentiated liposarcoma\") AND (\"gene expression\" OR \"RNA sequencing\") AND (\"prognosis\" OR \"outcome\")"
    for paper in retrieved_papers:
        title = paper['title']
        abstract = paper['abstract']
        clean_title = re.sub(r'<[^>]*>', '', title)
        clean_abstract = re.sub(r'<[^>]*>', '', abstract)

        flag = 1
        if title in downloaded_titles:
            flag = 3
        elif title in undownloaded_titles:
            flag = 2
        paper['flag'] = flag
        paper['title'] = clean_title
        paper['abstract'] = clean_abstract
        # paper['search_query'] = query
    retrieved_papers = sorted(retrieved_papers, key=lambda x: x['flag'], reverse=True)
    return retrieved_papers


def process_datasets(id: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    with open(DataFile / "dataset_1" / "retrieved_datasets_info.json", 'r', encoding='utf-8') as f:
        retrieved_datasets = json.load(f)
    with open(DataFile / "dataset_1" / "related_datasets_info.json", 'r', encoding='utf-8') as f:
        related_datasets = json.load(f)
    response = []
    related_datasets_set = set(related_datasets.keys())
    
    # temp
    # query = "liposarcoma AND gene expression"

    for category, datasets in retrieved_datasets.items():
        for dataset, info in datasets.items():
            is_related = dataset in related_datasets_set
            obj = {
                'dataset_id': dataset ,
                **info, 
                'isRelated': is_related, 
                'search_query': info["search_query"]
            }
            response.append(obj)


    # Sort datasets by 'isRelated' (True comes first)
    response.sort(key=lambda x: x['isRelated'], reverse=True)
    return response