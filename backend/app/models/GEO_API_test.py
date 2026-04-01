import time

import requests
import json
import os
import bs4
import random
import re
import shutil
from datetime import datetime
from urllib.request import getproxies
from pathlib import Path

from app.models.dataset_budget import (
    DownloadBudgetTracker,
    max_single_dataset_bytes,
    max_total_download_bytes,
    parse_size_to_bytes,
)

ncbi_api = 'ca7d6c6adb62c9ad9571230ba66728f54f08'
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
DOWNLOAD_MAX_RETRY = 3
DOWNLOAD_TIMEOUT = 60
FAST_PROBE_TIMEOUT = 6
PROBE_URL = "https://www.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=gds"
_NETWORK_MODE = None
_NETWORK_PROXIES = None
APP_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_GEO_SHARED_REPO = APP_DATA_DIR / "_geo_shared_repo"


def search_geo_accession(keyword, dbs=None, retmax=10):
    """通过关键词在多个数据库中搜索，并返回相关的访问号"""
    if dbs is None:
        dbs = ["gds"]

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    found_results = []

    retry_time = 10

    for db in dbs:
        print(f"Searching in database: {db}")
        params = {
            "db": db,
            "term": keyword,
            "retmode": "json",
            "retmax": retmax,
            'api_key': ncbi_api
        }

        for i in range(retry_time):
            response = _requests_get(base_url, params=params)
            print(f"URL: {response.url}")
            # print(f"Response: {response.text}")

            try:
                search_results = response.json()
                if search_results.get("esearchresult", {}).get("idlist"):
                    found_results.extend((db, geo_id) for geo_id in search_results["esearchresult"]["idlist"])
                break
            except Exception as e:
                print(f"\n\n报错关键词 ({i}次)：", db, keyword)
                print("报错信息：", e, "\n")
                print("报错输出：", response, "\n\n")

    if not found_results:
        print("No results found in the specified databases.\n")
    else:
        print(f"found {len(found_results)} results in geo database.\n")

    return found_results


def fetch_geo_summary(db, id):
    """获取详细信息以提取GEO访问号"""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": db,
        "id": id,
        "retmode": "json",
        'api_key': ncbi_api
    }
    response = _requests_get(url, params=params)
    return response.json()


def generate_geo_accession(found_results):
    """获取 GEO accession number"""
    retry = 0
    while retry < 10:
        try:
            accessions = []

            for db, geo_id in found_results:
                summary = fetch_geo_summary(db, geo_id)
                doc_summary = summary.get("result", {}).get(geo_id, {})
                accession = doc_summary.get("accession", None)
                if accession:
                    accessions.append(accession)

            print("got accession numbers:", accessions)
            break
        except Exception as e:
            retry += 1
            print("Exception:", e)
    return accessions


def get_details_and_download_links(accession_number):
    geo_base_url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc="
    geo_url = geo_base_url + accession_number

    response = _requests_get(geo_url)
    content = bs4.BeautifulSoup(response.content, "html.parser")
    tables = content.find_all('table', width="740", border="0", cellspacing="0", cellpadding="0", align="center")
    tables = tables[0].find_all('table', width="100%", border="0", cellspacing="0", cellpadding="0", align="center")
    table = tables[5]
    tds = table.find_all('td', width="100%", bgcolor="White")
    table1 = tds[0].find_all('table', cellpadding="2", cellspacing="0", width="600")
    table2 = tds[0].find_all('table', cellpadding="2", cellspacing="2", width="600")

    details = dict()

    trs = table1[0].find_all('tr', valign="top", recursive=False)
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 2:
            if "Status" in tds[0].text:
                td = tds[1].text
                details["Status"] = td
            if "Title" in tds[0].text:
                td = tds[1].text
                details["Title"] = td
            if "Organism" in tds[0].text:
                td = tds[1].text
                details["Organism"] = td
            if "Experiment type" in tds[0].text:
                td = tds[1].text
                details["Experiment type"] = td
            if "Summary" in tds[0].text:
                td = tds[1].text
                details["Summary"] = td
            if "Overall design" in tds[0].text:
                td = tds[1].text
                details["Overall design"] = td
        if "Platforms" in tds[0].text:
            texts = ", ".join(tr.text.strip().split("\n"))
            details["Platforms"] = texts
        if "Samples" in tds[0].text:
            Samples = dict()
            texts = tr.text.strip().split("\n")
            for i in range(len(texts)):
                texts[i] = texts[i].strip()
            alinks = tr.find_all("a")
            for a in alinks:
                link = a.get('href')
                if "/geo/query/acc.cgi?acc=" in link:
                    sample_accession = a.text.strip()
                    if not sample_accession in texts:
                        continue
                    Samples[sample_accession] = dict()
                    Samples[sample_accession]["link"] = link
                    Samples[sample_accession]["name"] = texts[texts.index(sample_accession) + 1]
                    sample_detail = get_sample_details_and_dowload_links(sample_accession, link)
                    Samples[sample_accession].update(sample_detail)
                    break  # 只取第一个

            if Samples:
                details["Samples"] = Samples

    if table2:
        details["Supplementary file"] = list()
        alinks = table2[0].find_all("a")
        download_links = list()
        for a in alinks:
            link = a.get('href')
            if "/geo/download" in link:
                download_links.append(link)

        if download_links:
            supp_files = table2[0].text.strip().split("\n\n")[1:-1]
            for i, file in enumerate(supp_files):
                attrs = file.strip().split("\n")
                details["Supplementary file"].append({
                    "file_name": attrs[0].strip(),
                    "file_size": attrs[1].strip(),
                    "file_type": attrs[3].strip(),
                    "download_link": download_links[i]
                })

    print(f"Details and download links of {accession_number} have got.")

    return details


def search_details(queries):
    # search datasets id and details in GEO
    details = dict()

    for keyword in queries:
        print(f"start search keyword {keyword} in GEO!\n")
        #keyword = keyword.replace(" ","+")
        try:
            found_results = search_geo_accession(keyword)  # [(db, id), ...]
            if found_results:
                accessions = generate_geo_accession(found_results)  # [accession, ...]
                for accession in accessions:
                    details[accession] = get_details_and_download_links(accession)
                    details[accession]["search_query"] = keyword    # 存入检索用的 query
        except Exception as e:
            print(f"Exception out: {e}")
        time.sleep(1)
        print(f"search keyword {keyword} in GEO over!\n\n\n")

    return details


# @with_requirements(python_packages=["requests", "bs4"], global_imports=["requests", "bs4"])
def _normalize_proxy_url(url):
    if not url:
        return url
    if "://" in url:
        return url
    return f"http://{url}"


def _get_requests_proxies_from_system():
    try:
        raw = getproxies() or {}
        proxies = {}
        if raw.get("http"):
            proxies["http"] = _normalize_proxy_url(raw.get("http"))
        if raw.get("https"):
            proxies["https"] = _normalize_proxy_url(raw.get("https"))
        if proxies:
            return proxies
    except Exception:
        pass

    # Manual env fallback
    manual_http = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    manual_https = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if manual_http or manual_https:
        return {
            "http": _normalize_proxy_url(manual_http or manual_https),
            "https": _normalize_proxy_url(manual_https or manual_http),
        }
    return {}


def _quick_probe_url(url: str, headers: dict, proxies: dict = None):
    try:
        r = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=FAST_PROBE_TIMEOUT,
            proxies=proxies if proxies else None,
            allow_redirects=True,
        )
        status = r.status_code
        r.close()
        if status >= 500:
            return False, f"http_status_{status}"
        return True, None
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def _ensure_network_mode():
    global _NETWORK_MODE, _NETWORK_PROXIES
    if _NETWORK_MODE is not None:
        return _NETWORK_MODE, _NETWORK_PROXIES

    probe_headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    direct_ok, direct_err = _quick_probe_url(PROBE_URL, probe_headers, proxies=None)
    if direct_ok:
        _NETWORK_MODE = "direct"
        _NETWORK_PROXIES = None
        print("[GEO] network mode selected: direct")
        return _NETWORK_MODE, _NETWORK_PROXIES

    proxies = _get_requests_proxies_from_system()
    if not proxies:
        raise RuntimeError(
            f"Direct probe failed ({direct_err}) and no proxy is configured. probe={PROBE_URL}"
        )
    proxy_ok, proxy_err = _quick_probe_url(PROBE_URL, probe_headers, proxies=proxies)
    if not proxy_ok:
        raise RuntimeError(
            f"Direct probe failed ({direct_err}); proxy probe failed ({proxy_err}). probe={PROBE_URL}"
        )
    _NETWORK_MODE = "proxy"
    _NETWORK_PROXIES = proxies
    print(f"[GEO] network mode selected: proxy {proxies}")
    return _NETWORK_MODE, _NETWORK_PROXIES


def _requests_get(url, **kwargs):
    mode, proxies = _ensure_network_mode()
    kwargs.setdefault("timeout", DOWNLOAD_TIMEOUT)
    if mode == "proxy" and "proxies" not in kwargs:
        kwargs["proxies"] = proxies
    return requests.get(url, **kwargs)


def _geo_repo_root() -> Path:
    custom = os.getenv("GEO_SHARED_REPO_ROOT", "").strip()
    if custom:
        return Path(custom)
    return DEFAULT_GEO_SHARED_REPO


def _geo_repo_files_dir() -> Path:
    return _geo_repo_root() / "files"


def _geo_repo_index_path() -> Path:
    return _geo_repo_root() / "index.json"


def _load_geo_repo_index() -> dict:
    idx_path = _geo_repo_index_path()
    if not idx_path.exists():
        return {"entries": []}
    try:
        with open(idx_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data
    except Exception:
        pass
    return {"entries": []}


def _save_geo_repo_index(index_data: dict) -> None:
    root = _geo_repo_root()
    root.mkdir(parents=True, exist_ok=True)
    with open(_geo_repo_index_path(), "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def _sanitize_filename(name: str) -> str:
    keep = []
    for ch in (name or "file.bin"):
        if ch.isalnum() or ch in ("-", "_", ".", "+"):
            keep.append(ch)
        else:
            keep.append("_")
    out = "".join(keep).strip("._")
    return out or "file.bin"


def _guess_accession(file_name: str = "", download_url: str = "") -> str:
    for source in (file_name or "", download_url or ""):
        m = re.search(r"(GSE\d{4,})", source, flags=re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return "UNKNOWN"


def _repo_relpath_for_file(file_name: str, download_url: str = "") -> str:
    accession = _guess_accession(file_name=file_name, download_url=download_url)
    safe_name = _sanitize_filename(file_name)
    return str(Path("files") / accession / safe_name)


def _repo_path_for_file(file_name: str, download_url: str = "") -> Path:
    return _geo_repo_root() / _repo_relpath_for_file(file_name=file_name, download_url=download_url)


def _link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(str(src), str(dst))
    except Exception:
        shutil.copy2(str(src), str(dst))


def _register_repo_entry(index_data: dict, *, file_name: str, download_url: str, repo_relpath: str, file_size: int) -> None:
    entries = index_data.setdefault("entries", [])
    for e in entries:
        if e.get("download_url") == download_url and e.get("repo_relpath") == repo_relpath:
            e["file_size"] = file_size
            e["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return
    entries.append(
        {
            "file_name": file_name,
            "download_url": download_url,
            "repo_relpath": repo_relpath,
            "file_size": int(file_size),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def _find_repo_cached_file(index_data: dict, *, file_name: str, download_url: str, expected_size: int = None) -> Path:
    repo_root = _geo_repo_root()
    entries = index_data.get("entries", [])

    # Priority 1: exact url match.
    for e in entries:
        if e.get("download_url") != download_url:
            continue
        p = repo_root / e.get("repo_relpath", "")
        if p.exists():
            return p

    # Priority 2: same filename + same size (if known).
    for e in entries:
        if e.get("file_name") != file_name:
            continue
        if expected_size is not None and int(e.get("file_size", -1)) != int(expected_size):
            continue
        p = repo_root / e.get("repo_relpath", "")
        if p.exists():
            return p

    return None


def _ingest_file_into_repo(local_file: Path, *, file_name: str, download_url: str, index_data: dict) -> Path:
    repo_path = _repo_path_for_file(file_name=file_name, download_url=download_url)
    repo_relpath = _repo_relpath_for_file(file_name=file_name, download_url=download_url)
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    if not repo_path.exists():
        os.replace(str(local_file), str(repo_path))
        _register_repo_entry(
            index_data,
            file_name=file_name,
            download_url=download_url,
            repo_relpath=repo_relpath,
            file_size=repo_path.stat().st_size,
        )
    _save_geo_repo_index(index_data)
    _link_or_copy(repo_path, local_file)
    return repo_path


def _stream_download_with_resume(url: str, headers: dict, final_path: str):
    temp_path = final_path + ".part"
    initial_partial_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
    _, chosen_proxies = _ensure_network_mode()

    for attempt in range(1, DOWNLOAD_MAX_RETRY + 1):
        partial_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
        req_headers = dict(headers)
        if partial_size > 0:
            req_headers["Range"] = f"bytes={partial_size}-"

        try:
            response = requests.get(
                url,
                headers=req_headers,
                stream=True,
                timeout=DOWNLOAD_TIMEOUT,
                proxies=chosen_proxies if chosen_proxies else None,
            )
            if response.status_code not in (200, 206):
                return False, 0, f"http_status_{response.status_code}"

            # If server ignores Range and returns 200, restart the partial file.
            if partial_size > 0 and response.status_code == 200:
                partial_size = 0
                with open(temp_path, "wb"):
                    pass

            mode = "ab" if partial_size > 0 else "wb"
            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

            final_size = os.path.getsize(temp_path)
            os.replace(temp_path, final_path)
            downloaded_incremental = max(final_size - initial_partial_size, 0)
            return True, downloaded_incremental, None
        except Exception as e:
            print(f"download attempt {attempt}/{DOWNLOAD_MAX_RETRY} failed: {e}")
            if attempt == DOWNLOAD_MAX_RETRY:
                return False, 0, str(e)
            time.sleep(min(2 ** attempt, 8))

    return False, 0, "download_failed_unknown"


def geo_download_dataset(
    details: dict,
    download_dir: str,
    manifest_path: str = None,
    single_limit_bytes: int = None,
    total_limit_bytes: int = None,
):
    """Download datasets for a project workdir.

    Policy:
    - Prefer copying from shared GEO repo if file exists.
    - Otherwise download into project-local `data/`.
    - Shared repo ingestion can be done after project run completes
      via `consolidate_project_data_to_shared`.
    """
    head = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
    base_download_url = f"https://www.ncbi.nlm.nih.gov"

    data_local_paths = dict()
    dl_data_dir = os.path.join(download_dir, "data")
    os.makedirs(dl_data_dir, exist_ok=True)
    repo_index = _load_geo_repo_index()

    if single_limit_bytes is None:
        single_limit_bytes = max_single_dataset_bytes()
    if total_limit_bytes is None:
        total_limit_bytes = max_total_download_bytes()

    tracker = DownloadBudgetTracker(
        single_limit_bytes=single_limit_bytes,
        total_limit_bytes=total_limit_bytes,
    )
    manifest = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "limits": {
            "single_dataset_bytes": single_limit_bytes,
            "total_download_bytes": total_limit_bytes,
        },
        "total_downloaded_bytes": 0,
        "datasets": [],
    }

    for accession_number in details:
        dataset_files = details.get(accession_number, {}).get("Supplementary file", [])
        if dataset_files:
            data_local_paths[accession_number] = []
            dataset_manifest = {
                "accession": accession_number,
                "status": "planned",
                "dataset_estimated_bytes": 0,
                "dataset_downloaded_bytes": 0,
                "files": [],
            }
            estimated_sum = 0
            unknown_size = False
            for file in dataset_files:
                s = parse_size_to_bytes(file.get("file_size", ""))
                if s is None:
                    unknown_size = True
                else:
                    estimated_sum += s
            dataset_manifest["dataset_estimated_bytes"] = estimated_sum

            if estimated_sum > single_limit_bytes:
                dataset_manifest["status"] = "blocked_by_single_dataset_budget"
                manifest["datasets"].append(dataset_manifest)
                print(f"Skip {accession_number}: estimated size {estimated_sum} > single limit {single_limit_bytes}")
                continue
            if (not unknown_size) and (not tracker.can_add(estimated_sum)):
                dataset_manifest["status"] = "blocked_by_total_budget"
                manifest["datasets"].append(dataset_manifest)
                print(f"Skip {accession_number}: total budget would be exceeded.")
                continue

            print(f"start download data {accession_number}")
            for file in dataset_files:
                file_name = file["file_name"]
                download_link = file["download_link"]
                est_bytes = parse_size_to_bytes(file.get("file_size", ""))
                file_entry = {
                    "file_name": file_name,
                    "file_size_text": file.get("file_size", ""),
                    "estimated_bytes": est_bytes,
                    "status": "planned",
                    "local_path": None,
                    "actual_bytes": None,
                }
                if est_bytes is not None and not tracker.can_add(est_bytes):
                    file_entry["status"] = "blocked_by_total_budget"
                    dataset_manifest["files"].append(file_entry)
                    dataset_manifest["status"] = "blocked_by_total_budget"
                    print(f"Skip file {file_name}: total budget would be exceeded.")
                    continue

                workdir_filename = "data/" + file["file_name"]
                filename = os.path.join(download_dir, workdir_filename)
                filename_path = Path(filename)
                download_url = base_download_url + download_link
                print(f"Download data file {file_name} from link {download_url}")

                if os.path.exists(filename):
                    existing_size = os.path.getsize(filename)
                    # Existing local file: ingest to shared repo for cross-project reuse.
                    try:
                        _ingest_file_into_repo(
                            filename_path,
                            file_name=file_name,
                            download_url=download_url,
                            index_data=repo_index,
                        )
                    except Exception as ingest_err:
                        print(f"warning: failed to ingest existing file into shared repo: {ingest_err}")
                    file_entry["status"] = "already_exists"
                    file_entry["local_path"] = workdir_filename
                    file_entry["actual_bytes"] = existing_size
                    data_local_paths[accession_number].append(workdir_filename)
                    print(f"Skip download for {file_name}: file exists at {filename}\n\n")
                    dataset_manifest["dataset_downloaded_bytes"] += existing_size
                    dataset_manifest["files"].append(file_entry)
                    continue

                # Reuse from shared repo if available.
                cached = _find_repo_cached_file(
                    repo_index,
                    file_name=file_name,
                    download_url=download_url,
                    expected_size=est_bytes,
                )
                if cached is not None:
                    filename_path.parent.mkdir(parents=True, exist_ok=True)
                    if not filename_path.exists():
                        shutil.copy2(str(cached), str(filename_path))
                    cached_size = filename_path.stat().st_size if filename_path.exists() else None
                    file_entry["status"] = "reused_from_shared_cache"
                    file_entry["local_path"] = workdir_filename
                    file_entry["actual_bytes"] = int(cached_size) if cached_size is not None else None
                    data_local_paths[accession_number].append(workdir_filename)
                    print(f"Reused shared GEO cache for {file_name} -> {filename}\n\n")
                    dataset_manifest["dataset_downloaded_bytes"] += int(cached_size or 0)
                    dataset_manifest["files"].append(file_entry)
                    continue

                ok, downloaded_incremental, err = _stream_download_with_resume(
                    download_url,
                    head,
                    filename,
                )
                if ok and os.path.exists(filename):
                    actual_bytes = os.path.getsize(filename)
                    print(f"Download data file {file_name} in {accession_number} to {filename}\n\n")
                    data_local_paths[accession_number].append(workdir_filename)
                    tracker.consume(downloaded_incremental)
                    file_entry["status"] = "downloaded"
                    file_entry["local_path"] = workdir_filename
                    file_entry["actual_bytes"] = actual_bytes
                    dataset_manifest["dataset_downloaded_bytes"] += actual_bytes
                else:
                    print(f"Failed to download data for {file_name} in {accession_number}: {err}\n\n")
                    file_entry["status"] = "download_failed"
                dataset_manifest["files"].append(file_entry)

            if dataset_manifest["status"] == "planned":
                if dataset_manifest["dataset_downloaded_bytes"] > single_limit_bytes:
                    dataset_manifest["status"] = "blocked_by_single_dataset_budget"
                elif any(f.get("status") in ("downloaded", "already_exists", "reused_from_shared_cache") for f in dataset_manifest["files"]):
                    if any(f.get("status") == "download_failed" for f in dataset_manifest["files"]):
                        dataset_manifest["status"] = "partial_downloaded"
                    else:
                        dataset_manifest["status"] = "downloaded"
                elif any(f.get("status") == "download_failed" for f in dataset_manifest["files"]):
                    dataset_manifest["status"] = "download_failed"
                elif any(f.get("status") == "blocked_by_total_budget" for f in dataset_manifest["files"]):
                    dataset_manifest["status"] = "blocked_by_total_budget"
                else:
                    dataset_manifest["status"] = "skipped"
            manifest["datasets"].append(dataset_manifest)

    manifest["total_downloaded_bytes"] = tracker.total_used_bytes
    if manifest_path:
        try:
            with open(manifest_path, "w", encoding="utf-8") as fw:
                json.dump(manifest, fw, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"write manifest failed: {e}")

    return data_local_paths


def consolidate_project_data_to_shared(project_work_dir: str, remove_local: bool = True) -> dict:
    """
    Ingest project-local GEO files from `<project_work_dir>/data` into shared repo.
    Optionally remove local copies afterwards to avoid duplicate storage.
    """
    project_data_dir = Path(project_work_dir) / "data"
    if not project_data_dir.exists():
        return {
            "project_data_dir": str(project_data_dir),
            "ingested_files": 0,
            "failed_files": 0,
            "removed_local_files": 0,
            "indexed_entries": len(_load_geo_repo_index().get("entries", [])),
        }

    repo_index = _load_geo_repo_index()
    ingested = 0
    failed = 0
    removed = 0

    for f in project_data_dir.iterdir():
        if not f.is_file():
            continue
        name = f.name
        if not re.match(r"^GSE\d{4,}", name, flags=re.IGNORECASE):
            continue
        download_url = f"project_local://{name}"
        try:
            _ingest_file_into_repo(
                f,
                file_name=name,
                download_url=download_url,
                index_data=repo_index,
            )
            ingested += 1
            if remove_local and f.exists():
                try:
                    f.unlink()
                    removed += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"consolidate failed for {f}: {e}")
            failed += 1

    return {
        "project_data_dir": str(project_data_dir),
        "ingested_files": ingested,
        "failed_files": failed,
        "removed_local_files": removed,
        "indexed_entries": len(_load_geo_repo_index().get("entries", [])),
    }


def migrate_geo_repo_to_plain_layout(remove_legacy_prefixed: bool = True) -> dict:
    """
    Normalize shared GEO repo paths to:
      files/<ACCESSION>/<original_file_name>
    and optionally remove legacy prefixed files like:
      files/<hash>__<filename>
    """
    repo_root = _geo_repo_root()
    index_data = _load_geo_repo_index()
    entries = index_data.get("entries", [])
    moved = 0
    removed_legacy = 0
    missing_sources = 0

    for e in entries:
        file_name = str(e.get("file_name", "") or "")
        download_url = str(e.get("download_url", "") or "")
        old_rel = str(e.get("repo_relpath", "") or "")
        old_path = repo_root / old_rel
        new_rel = _repo_relpath_for_file(file_name=file_name, download_url=download_url)
        new_path = repo_root / new_rel
        new_path.parent.mkdir(parents=True, exist_ok=True)

        if old_rel and old_rel != new_rel:
            if old_path.exists():
                if not new_path.exists():
                    os.replace(str(old_path), str(new_path))
                    moved += 1
            elif new_path.exists():
                pass
            else:
                missing_sources += 1

        e["repo_relpath"] = new_rel
        if new_path.exists():
            e["file_size"] = int(new_path.stat().st_size)

    # Deduplicate entries by (download_url, repo_relpath), keep latest record.
    dedup = {}
    for e in entries:
        key = (str(e.get("download_url", "")), str(e.get("repo_relpath", "")))
        dedup[key] = e
    index_data["entries"] = list(dedup.values())
    _save_geo_repo_index(index_data)

    if remove_legacy_prefixed:
        legacy_root = _geo_repo_files_dir()
        if legacy_root.exists():
            for p in legacy_root.glob("*__*"):
                if p.is_file():
                    try:
                        p.unlink()
                        removed_legacy += 1
                    except Exception:
                        pass

    return {
        "repo_root": str(repo_root),
        "moved_entries": moved,
        "removed_legacy_prefixed_files": removed_legacy,
        "missing_sources": missing_sources,
        "indexed_entries": len(index_data.get("entries", [])),
    }


def migrate_existing_geo_files_to_shared_repo(projects_data_root: str = None) -> dict:
    """
    Migrate existing files under app/data/*/data into shared GEO repo.
    - Move source file into shared repo if repo copy is missing.
    - Recreate source path as hardlink/copy to shared file.
    """
    root = Path(projects_data_root) if projects_data_root else APP_DATA_DIR
    repo_index = _load_geo_repo_index()
    migrated = 0
    skipped = 0
    failed = 0

    for project_dir in root.iterdir():
        if not project_dir.is_dir():
            continue
        if project_dir.name.startswith("_geo_shared_repo"):
            continue
        data_dir = project_dir / "data"
        if not data_dir.exists() or not data_dir.is_dir():
            continue

        for f in data_dir.iterdir():
            if not f.is_file():
                continue
            file_name = f.name
            fake_download_url = f"local_migration://{file_name}"
            try:
                _ingest_file_into_repo(
                    f,
                    file_name=file_name,
                    download_url=fake_download_url,
                    index_data=repo_index,
                )
                migrated += 1
            except Exception as e:
                print(f"migrate failed for {f}: {e}")
                failed += 1

    layout_report = migrate_geo_repo_to_plain_layout(remove_legacy_prefixed=True)

    # Count how many indexed entries now exist.
    try:
        index_now = _load_geo_repo_index()
        skipped = len(index_now.get("entries", [])) - migrated
    except Exception:
        skipped = 0

    return {
        "repo_root": str(_geo_repo_root()),
        "migrated_files": migrated,
        "failed_files": failed,
        "indexed_entries": len(_load_geo_repo_index().get("entries", [])),
        "layout_report": layout_report,
        "note": "Source files are linked/copied back to original project paths.",
    }


def get_sample_details_and_dowload_links(sample_accession_number, sample_link):
    base_url = "https://www.ncbi.nlm.nih.gov"

    geo_sample_url = base_url + sample_link

    response = _requests_get(geo_sample_url)
    content = bs4.BeautifulSoup(response.content, "html.parser")
    tables = content.find_all('table', width="740", border="0", cellspacing="0", cellpadding="0", align="center")
    tables = tables[0].find_all('table', width="100%", border="0", cellspacing="0", cellpadding="0", align="center")
    table = tables[5]
    tds = table.find_all('td', width="100%", bgcolor="White")

    table1 = tds[0].find_all('table', cellpadding="2", cellspacing="0", width="600")
    table2 = tds[0].find_all('table', cellpadding="2", cellspacing="2", width="600")

    details = dict()

    trs = table1[0].find_all('tr', valign="top", recursive=False)
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) == 2:
            if "Status" in tds[0].text:
                td = tds[1].text
                details["Status"] = td
            if "Title" in tds[0].text:
                td = tds[1].text
                details["Title"] = td
            if "Sample type" in tds[0].text:
                td = tds[1].text
                details["Sample type"] = td
            if "Organism" in tds[0].text:
                td = tds[1].text
                details["Organism"] = td
            if "Characteristics" in tds[0].text:
                td = tds[1].text
                details["Characteristics"] = td
            if "Treatment protocol" in tds[0].text:
                td = tds[1].text
                details["Treatment protocol"] = td
            if "Growth protocol" in tds[0].text:
                td = tds[1].text
                details["Growth protocol"] = td
            if "Extracted molecule" in tds[0].text:
                td = tds[1].text
                details["Extracted molecule"] = td
            if "Extraction protocol" in tds[0].text:
                td = tds[1].text
                details["Extraction protocol"] = td
            if "Library strategy" in tds[0].text:
                td = tds[1].text
                details["Library strategy"] = td
            if "Library source" in tds[0].text:
                td = tds[1].text
                details["Library source"] = td
            if "Library selection" in tds[0].text:
                td = tds[1].text
                details["Extracted molecule"] = td
            if "Instrument model" in tds[0].text:
                td = tds[1].text
                details["Instrument model"] = td
            if "Description" in tds[0].text:
                td = tds[1].text
                details["Description"] = td
            if "Data processing" in tds[0].text:
                td = tds[1].text
                details["Data processing"] = td

        if "Platform ID" in tds[0].text:
            texts = ", ".join(tr.text.replace("Platform ID", "").strip().split("\n"))
            details["Platform ID"] = texts

        if table2:
            details["Supplementary file"] = list()
            alinks = table2[0].find_all("a")
            download_links = list()
            for a in alinks:
                link = a.get('href')
                if "/geo/download" in link:
                    download_links.append(link)

            supp_files = table2[0].text.split("\n\n")[1:-1]
            for i, file in enumerate(supp_files):
                attrs = file.split("\n")

                details["Supplementary file"].append({
                    "file_name": attrs[0],
                    "file_size": attrs[1],
                    "file_type": attrs[3],
                    "download_link": download_links[i]
                })

    return details


