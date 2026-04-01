from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from pathlib import Path
import json
import os
import math
from collections import defaultdict

import re
from app.auth_core import ensure_project_access, require_user
router = APIRouter()
MIN_MANUAL_UPLOAD_TEXT_CHARS = int(os.getenv("MIN_MANUAL_UPLOAD_TEXT_CHARS", "6000"))

try:
    import fitz
except ImportError:
    fitz = None



@router.get("/{id}/papersets")
async def get_papersets(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    return process_papersets(id)


@router.get("/{id}/datasets")
async def get_datasets(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    return process_datasets(id)


def process_papersets(id: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    retrieved_path = DataFile / "papers" / "retrieved_papers_info.json"
    related_path = DataFile / "papers" / "related_papers_info.json"
    if not retrieved_path.exists():
        return {
            'retrieved_papers': {},
            'count': [0, 0, 0, 0, 0],
            'manual_upload_needed': [],
            'manual_upload_threshold_chars': MIN_MANUAL_UPLOAD_TEXT_CHARS,
            'pending': True,
        }

    with open(retrieved_path, 'r', encoding='utf-8') as f:
        retrieved_papers = json.load(f)
    if related_path.exists():
        with open(related_path, 'r', encoding='utf-8') as f:
            related_papers = json.load(f)
    else:
        related_papers = {"download successfully": [], "download failed": []}
    downloaded_titles = {str(item.get('title', '')) for item in related_papers["download successfully"]}
    undownloaded_titles = {str(item.get('title', '')) for item in related_papers["download failed"]}
    count = [0, 0, 0, 0, 0]
    total = len(retrieved_papers)
    for paper in retrieved_papers:
        # 缂佺喕顓搁崚鍡樻殶
        score_idx = _score_to_bucket_index(paper.get("score"))
        count[score_idx] += 1

        title = str(paper.get('title', ''))
        abstract = str(paper.get('abstract', ''))
        search_query = str(paper.get('search_query', ''))
        clean_title = re.sub(r'<[^>]*>', '', title)
        clean_abstract = re.sub(r'<[^>]*>', '', abstract)
        clean_query = re.sub(r'"', '', search_query)
    
        flag = 1
        if title in downloaded_titles:
            flag = 3
        elif title in undownloaded_titles:
            flag = 2

        paper['flag'] = flag
        paper['title'] = clean_title
        paper['abstract'] = clean_abstract
        paper['search_query'] = clean_query
        # 婵″倹鐏夐張澶涚礉閸掔姵甯€path鐎涙顔?
        if 'path' in paper:
            del paper['path']
    # count 閸氬嫰銆嶉梽銈勪簰閹粯鏆?
    for i in range(len(count)):
        count[i] = round(count[i] / total, 3) if total > 0 else 0
    retrieved_papers = sorted(retrieved_papers, key=lambda x: x.get('flag', 0), reverse=True)
    grouped = defaultdict(list)
    for paper in retrieved_papers:
        grouped[str(paper.get("search_query", ""))].append(paper)
    retrieved_papers = dict(grouped)
    retrieved_papers = _sanitize_for_json(retrieved_papers)

    manual_upload_needed = _collect_manual_upload_needed(related_papers)
    return {
        'retrieved_papers': retrieved_papers,
        'count': count,
        'manual_upload_needed': manual_upload_needed,
        'manual_upload_threshold_chars': MIN_MANUAL_UPLOAD_TEXT_CHARS,
        'pending': False,
    }



def _score_to_bucket_index(score) -> int:
    # Bucket into [0..4] corresponding to score [1..5].
    try:
        s = float(score)
    except Exception:
        s = 1.0
    s_int = int(round(s))
    if s_int < 1:
        s_int = 1
    if s_int > 5:
        s_int = 5
    return s_int - 1

def _safe_stem_from_paper(paper: dict) -> str:
    if paper.get("pmcid"):
        return str(paper["pmcid"]).strip()
    if paper.get("doi"):
        return str(paper["doi"]).replace("/", "_").strip()
    title = re.sub(r"<[^>]*>", "", paper.get("title", "")).strip()
    title = re.sub(r'[\\/:*?"<>|]+', "_", title)
    return (title or "paper")[:120]


def _paper_uid(paper: dict) -> str:
    doi = (paper.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    pmcid = str(paper.get("pmcid") or "").strip().lower()
    if pmcid:
        return f"pmcid:{pmcid}"
    title = re.sub(r"<[^>]*>", "", paper.get("title", "")).strip().lower()
    return f"title:{title}"


def _read_text_chars(path_str: str) -> int:
    if not path_str:
        return 0
    p = Path(path_str)
    if not p.exists():
        return 0
    suffix = p.suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            return len(p.read_text(encoding="utf-8", errors="ignore").strip())
        except Exception:
            return 0
    return 0


def _collect_manual_upload_needed(related_papers: dict):
    needed = []
    seen = set()
    for paper in related_papers.get("download failed", []):
        uid = _paper_uid(paper)
        if uid in seen:
            continue
        seen.add(uid)
        needed.append({
            "uid": uid,
            "title": re.sub(r"<[^>]*>", "", paper.get("title", "")),
            "doi": paper.get("doi"),
            "pmcid": paper.get("pmcid"),
            "reason": "download_failed",
            "text_chars": 0,
            "threshold_chars": MIN_MANUAL_UPLOAD_TEXT_CHARS,
        })

    for paper in related_papers.get("download successfully", []):
        path = str(paper.get("path") or "")
        chars = _read_text_chars(path)
        if chars > 0 and chars < MIN_MANUAL_UPLOAD_TEXT_CHARS:
            uid = _paper_uid(paper)
            if uid in seen:
                continue
            seen.add(uid)
            needed.append({
                "uid": uid,
                "title": re.sub(r"<[^>]*>", "", paper.get("title", "")),
                "doi": paper.get("doi"),
                "pmcid": paper.get("pmcid"),
                "reason": "text_too_short",
                "text_chars": chars,
                "threshold_chars": MIN_MANUAL_UPLOAD_TEXT_CHARS,
            })
    return needed


def _validate_pdf(path: Path):
    if fitz is None:
        raise HTTPException(status_code=500, detail="PyMuPDF is not installed on backend.")
    try:
        doc = fitz.open(path)
        page_count = doc.page_count
        text = ""
        for i in range(min(page_count, 5)):
            text += doc[i].get_text()
        doc.close()
        text_chars = len((text or "").strip())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF file: {e}")
    if page_count <= 0:
        raise HTTPException(status_code=400, detail="Invalid PDF: empty page count.")
    if text_chars < 200:
        raise HTTPException(status_code=400, detail="PDF text is too short, possibly scanned/invalid.")
    return page_count, text_chars


@router.post("/{id}/papers/upload-manual")
async def upload_manual_paper(
    id: int,
    authorization: str | None = Header(default=None),
    file: UploadFile = File(...),
    doi: str = Form(default=""),
    pmcid: str = Form(default=""),
    title: str = Form(default=""),
 ):
    user = require_user(authorization)
    ensure_project_access(user, id)
    data_dir = Path(__file__).parent.parent / "data" / str(id)
    paper_dir = data_dir / "papers"
    related_path = paper_dir / "related_papers_info.json"
    if not related_path.exists():
        raise HTTPException(status_code=404, detail="related_papers_info.json not found.")

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    related = json.loads(related_path.read_text(encoding="utf-8"))
    all_papers = related.get("download successfully", []) + related.get("download failed", [])

    target = None
    doi_norm = (doi or "").strip().lower()
    pmcid_norm = str(pmcid or "").strip().lower()
    title_norm = re.sub(r"<[^>]*>", "", (title or "")).strip().lower()
    for p in all_papers:
        if doi_norm and (str(p.get("doi") or "").strip().lower() == doi_norm):
            target = p
            break
        if pmcid_norm and (str(p.get("pmcid") or "").strip().lower() == pmcid_norm):
            target = p
            break
        if title_norm and (re.sub(r"<[^>]*>", "", str(p.get("title") or "")).strip().lower() == title_norm):
            target = p
            break
    if target is None:
        raise HTTPException(status_code=404, detail="Cannot match uploaded paper to project paper record.")

    stem = _safe_stem_from_paper(target)
    save_path = paper_dir / f"{stem}.pdf"
    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)

    page_count, text_chars = _validate_pdf(save_path)

    target["path"] = str(save_path)
    target["fallback_text"] = False
    target["recovered_via"] = "manual_upload_pdf"

    failed = related.get("download failed", [])
    success = related.get("download successfully", [])
    failed = [p for p in failed if _paper_uid(p) != _paper_uid(target)]
    success = [p for p in success if _paper_uid(p) != _paper_uid(target)]
    success.append(target)
    related["download failed"] = failed
    related["download successfully"] = success
    related_path.write_text(json.dumps(related, ensure_ascii=False, indent=4), encoding="utf-8")

    return {
        "message": "Manual PDF uploaded and validated.",
        "paper": {
            "title": re.sub(r"<[^>]*>", "", target.get("title", "")),
            "doi": target.get("doi"),
            "pmcid": target.get("pmcid"),
            "path": str(save_path),
            "page_count": page_count,
            "preview_text_chars": text_chars,
        },
        "manual_upload_needed": _collect_manual_upload_needed(related),
    }

def process_datasets(id: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id)
    retrieved_path = DataFile / "dataset_1" / "retrieved_datasets_info.json"
    related_path = DataFile / "dataset_1" / "related_datasets_info.json"
    if not retrieved_path.exists():
        return {"pending": True}
    with open(retrieved_path, 'r', encoding='utf-8') as f:
        retrieved_datasets = json.load(f)
    if related_path.exists():
        with open(related_path, 'r', encoding='utf-8') as f:
            related_datasets = json.load(f)
    else:
        related_datasets = {}
    response = []
    related_datasets_set = set(related_datasets.keys())
    
    for category, datasets in retrieved_datasets.items():
        for dataset, info in datasets.items():
            is_related = dataset in related_datasets_set
            obj = {
                'dataset_id': dataset ,
                **info, 
                'isRelated': is_related, 
                'search_query': str(info.get("search_query", ""))
            }
            response.append(obj)


    # Sort datasets by 'isRelated' (True comes first)
    response.sort(key=lambda x: x.get('isRelated', False), reverse=True)
    grouped = defaultdict(list)
    for item in response:
        grouped[str(item.get("search_query", ""))].append(item)
    response = dict(grouped)
    response = _sanitize_for_json(response)
    response["pending"] = False
    return response


def _sanitize_for_json(obj):
    """Recursively replace NaN/Inf with None for strict JSON serialization."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    return obj

