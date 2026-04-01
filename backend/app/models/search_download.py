import requests
import xml.etree.ElementTree as ET
from typing_extensions import Annotated
from urllib.request import getproxies
from urllib.parse import urljoin, quote_plus, urlparse
import socket
from concurrent.futures import ThreadPoolExecutor
import json
import re
from datetime import datetime
from pathlib import Path
from app.models.downpmc import *
from app.models.our_utils import *
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# from downpmc import *
# from our_utils import *

import os
ncbi_api = 'ca7d6c6adb62c9ad9571230ba66728f54f08'


filter_prompt = prompts["filter"]
query_generator_prompt = prompts["query_generator"]

BYPASS_PROXY_SUFFIXES = (".cn", ".com.cn", ".edu.cn", ".gov.cn")
head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}  #锛岄槻姝TTP403閿欒
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
        if "http" in raw:
            proxies["http"] = _normalize_proxy_url(raw.get("http"))
        if "https" in raw:
            proxies["https"] = _normalize_proxy_url(raw.get("https"))
        if proxies:
            return proxies
    except Exception as e:
        print(f"[proxy] requests proxy load failed: {e}", flush=True)

    # Fallback for Clash rule mode: common local proxy ports.
    for host, port in [("127.0.0.1", 7890), ("127.0.0.1", 7897), ("127.0.0.1", 10809)]:
        try:
            with socket.create_connection((host, port), timeout=0.8):
                proxy = f"http://{host}:{port}"
                return {"http": proxy, "https": proxy}
        except Exception:
            continue

    try:
        manual = os.getenv("DOWNLOAD_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
        if manual:
            proxy = _normalize_proxy_url(manual)
            return {"http": proxy, "https": proxy}
    except Exception:
        pass

    return {}


REQUESTS_PROXIES = _get_requests_proxies_from_system()
if REQUESTS_PROXIES:
    print(f"[proxy] requests using system proxies: {REQUESTS_PROXIES}", flush=True)
else:
    print("[proxy] requests found no system proxy.", flush=True)


def _requests_get(url, **kwargs):
    kwargs.setdefault("timeout", 60)
    if REQUESTS_PROXIES and "proxies" not in kwargs and not _should_bypass_proxy(url):
        kwargs["proxies"] = REQUESTS_PROXIES
    return requests.get(url, **kwargs)


def _should_bypass_proxy(url):
    try:
        host = (urlparse(url).hostname or "").lower().strip()
    except Exception:
        return False
    if not host:
        return False
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    if host.endswith(BYPASS_PROXY_SUFFIXES):
        return True
    return False


def _mojibake_score(text):
    if not text:
        return 0
    markers = ["脙", "芒聙", "鈥", "锟", "聙", "聯"]
    return sum(text.count(m) for m in markers)


def _fix_mojibake_text(text):
    if not text:
        return text
    base_score = _mojibake_score(text)
    if base_score == 0:
        return text

    best = text
    best_score = base_score
    for src in ("latin-1", "cp1252"):
        try:
            cand = text.encode(src, errors="ignore").decode("utf-8", errors="ignore")
            score = _mojibake_score(cand)
            if score < best_score and len(cand.strip()) > 100:
                best = cand
                best_score = score
        except Exception:
            continue
    return best


def _extract_bioc_plain_text(xml_text):
    try:
        soup = BeautifulSoup(xml_text or "", "xml")
        blocks = []
        for t in soup.find_all("text"):
            v = " ".join((t.get_text(" ", strip=True) or "").split())
            if v:
                blocks.append(v)
        if blocks:
            return "\n\n".join(blocks)
    except Exception:
        pass
    return ""


FAST_FETCH_TIMEOUT = 4
MAX_RECOVER_WORKERS = 6
DOWNLOAD_RETRY = 1
ENABLE_LLM_PDF_LINK_FINDER = os.getenv("ENABLE_LLM_PDF_LINK_FINDER", "1") == "1"
MIRROR_SOURCE_URL = "https://www.sssam.com/tool/ggscholar/"
SCHOLAR_MIRROR_CACHE = Path(__file__).parent.parent / "data" / "scholar_mirrors_cache.json"
SCIHUB_MIRROR_SOURCE_URL = "https://www.sssam.com/tool/scihub/"
SCIHUB_MIRROR_CACHE = Path(__file__).parent.parent / "data" / "scihub_mirrors_cache.json"
# Testing-only hardcoded key per user request.
ELSEVIER_API_KEY = "69852a18048e8e1ee323a435769602d0"
GENERATE_PDF_FROM_XML = False


def _safe_name_from_paper(paper):
    if paper.get("pmcid"):
        return str(paper["pmcid"])
    if paper.get("doi"):
        return str(paper["doi"]).replace("/", "_")
    title = re.sub(r"<[^>]*>", "", paper.get("title", "paper"))
    title = re.sub(r'[\\/:*?"<>|]+', "_", title).strip()
    if not title:
        title = "paper"
    return title[:120]


def _build_fallback_text(paper):
    clean_title = re.sub(r"<[^>]*>", "", paper.get("title", "Unknown Title"))
    abstract = paper.get("abstract", "No abstract available.")
    doi = paper.get("doi", "None")
    pmid = paper.get("pmid", "None")
    pmcid = paper.get("pmcid", "None")
    query = paper.get("search_query", "None")
    return (
        f"Title: {clean_title}\n"
        f"DOI: {doi}\n"
        f"PMID: {pmid}\n"
        f"PMCID: {pmcid}\n"
        f"Search Query: {query}\n\n"
        f"Abstract:\n{abstract}\n"
    )


def _create_fallback_text_file(paper, save_dir):
    try:
        name = _safe_name_from_paper(paper)
        path = os.path.join(save_dir, f"{name}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(_build_fallback_text(paper))
        return path
    except Exception as e:
        print(f"fallback text generation failed: {e}", flush=True)
        return None


def _save_bytes(content, path):
    with open(path, "wb") as f:
        f.write(content)


def _extract_urls_from_text(text):
    urls = re.findall(r"https?://[^\s\"'<>]+", text or "")
    cleaned = []
    seen = set()
    for u in urls:
        u = u.strip().rstrip(").,;")
        if u in seen:
            continue
        seen.add(u)
        cleaned.append(u)
    return cleaned


def _is_likely_scholar_mirror(url):
    u = (url or "").lower()
    keywords = [
        "scholar",
        "guge",
        "xueshu",
        "ac.scmor",
        "googlescholar",
    ]
    return any(k in u for k in keywords)


def _is_likely_scihub_mirror(url):
    u = (url or "").lower()
    return ("sci-hub" in u or "scihub" in u) and "sssam.com/tool/scihub" not in u


def _load_cached_mirrors():
    if not SCHOLAR_MIRROR_CACHE.exists():
        return None
    try:
        with open(SCHOLAR_MIRROR_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cached_mirrors(mirrors):
    try:
        SCHOLAR_MIRROR_CACHE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "mirrors": mirrors,
        }
        with open(SCHOLAR_MIRROR_CACHE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[scholar-mirror] cache save failed: {e}", flush=True)


def _fetch_scholar_mirrors_from_source():
    try:
        r = _requests_get(MIRROR_SOURCE_URL, headers=head, timeout=FAST_FETCH_TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            return []
        html = r.text or ""
        urls = _extract_urls_from_text(html)
        candidates = [u for u in urls if _is_likely_scholar_mirror(u)]
        # remove source page itself
        candidates = [u for u in candidates if "sssam.com/tool/ggscholar" not in u.lower()]
        # keep unique and first few
        uniq = []
        seen = set()
        for u in candidates:
            root = u.split("?")[0].rstrip("/")
            if root in seen:
                continue
            seen.add(root)
            uniq.append(root)
        return uniq[:6]
    except Exception as e:
        print(f"[scholar-mirror] source fetch failed: {e}", flush=True)
        return []


def _get_scholar_mirrors_daily():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cache = _load_cached_mirrors()
    if cache and cache.get("updated_date") == today and cache.get("mirrors"):
        return cache["mirrors"][:3]

    mirrors = _fetch_scholar_mirrors_from_source()
    if mirrors:
        _save_cached_mirrors(mirrors)
        return mirrors[:3]

    # fallback to old cache if today update failed
    if cache and cache.get("mirrors"):
        return cache["mirrors"][:3]
    return []


def _load_cached_scihub_mirrors():
    if not SCIHUB_MIRROR_CACHE.exists():
        return None
    try:
        with open(SCIHUB_MIRROR_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cached_scihub_mirrors(mirrors):
    try:
        SCIHUB_MIRROR_CACHE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "mirrors": mirrors,
        }
        with open(SCIHUB_MIRROR_CACHE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[scihub-mirror] cache save failed: {e}", flush=True)


def _fetch_scihub_mirrors_from_source():
    try:
        r = _requests_get(SCIHUB_MIRROR_SOURCE_URL, headers=head, timeout=FAST_FETCH_TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            return []
        html = r.text or ""
        urls = _extract_urls_from_text(html)
        candidates = [u for u in urls if _is_likely_scihub_mirror(u)]
        uniq = []
        seen = set()
        for u in candidates:
            root = u.split("?")[0].rstrip("/")
            if root in seen:
                continue
            seen.add(root)
            uniq.append(root)
        return uniq[:6]
    except Exception as e:
        print(f"[scihub-mirror] source fetch failed: {e}", flush=True)
        return []


def _get_scihub_mirrors_daily():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cache = _load_cached_scihub_mirrors()
    if cache and cache.get("updated_date") == today and cache.get("mirrors"):
        return cache["mirrors"][:3]

    mirrors = _fetch_scihub_mirrors_from_source()
    if mirrors:
        _save_cached_scihub_mirrors(mirrors)
        return mirrors[:3]

    if cache and cache.get("mirrors"):
        return cache["mirrors"][:3]
    return []


def _extract_html_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text


def _extract_elsevier_fulltext_markdown(xml_text):
    soup = BeautifulSoup(xml_text, "xml")

    def _name(tag):
        n = getattr(tag, "name", "") or ""
        return n.split(":")[-1].lower()

    def _t(tag):
        return " ".join(tag.get_text(" ", strip=True).split()) if tag else ""

    title_tag = soup.find("dc:title")
    title = _t(title_tag) or "Elsevier Full Text"

    lines = [f"# {title}", ""]

    # Abstract
    abstract_blocks = []
    for ab in soup.find_all(lambda x: _name(x) == "abstract"):
        paras = ab.find_all(lambda x: _name(x) in ("para", "simple-para"))
        if paras:
            abstract_blocks.extend([_t(p) for p in paras if _t(p)])
        else:
            text = _t(ab)
            if text:
                abstract_blocks.append(text)
    if abstract_blocks:
        lines.append("## Abstract")
        lines.append("")
        for p in abstract_blocks:
            lines.append(p)
            lines.append("")

    # Body sections
    body = soup.find(lambda x: _name(x) == "body")
    if body:
        section_idx = 0
        for sec in body.find_all(lambda x: _name(x) == "section"):
            heading = _t(sec.find(lambda x: _name(x) == "section-title"))
            paras = sec.find_all(lambda x: _name(x) in ("para", "simple-para"))
            para_texts = [_t(p) for p in paras if _t(p)]
            if not heading and not para_texts:
                continue
            section_idx += 1
            lines.append(f"## {heading or f'Section {section_idx}'}")
            lines.append("")
            for p in para_texts:
                lines.append(p)
                lines.append("")

    # References
    refs = []
    for ref in soup.find_all(lambda x: _name(x) == "bib-reference"):
        rt = _t(ref)
        if rt:
            refs.append(rt)
    if refs:
        lines.append("## References")
        lines.append("")
        for i, r in enumerate(refs, 1):
            lines.append(f"{i}. {r}")
        lines.append("")

    md = "\n".join(lines).strip()
    return md


def _markdown_to_clean_text(md_text):
    text = re.sub(r"^#{1,6}\s*", "", md_text or "", flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _write_txt_and_md(clean_text, save_dir, paper, title="Recovered Full Text"):
    name = _safe_name_from_paper(paper)
    txt_path = os.path.join(save_dir, f"{name}.txt")
    md_path = os.path.join(save_dir, f"{name}.md")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{clean_text.strip()}\n")
    paper["fulltext_text_path"] = txt_path
    paper["fulltext_markdown_path"] = md_path
    return txt_path


def _markdown_to_pdf_file(md_text, pdf_path):
    if fitz is None:
        return False
    try:
        doc = fitz.open()
        page_width = 595
        page_height = 842
        margin = 45
        usable_width = page_width - 2 * margin
        y = margin
        page = doc.new_page(width=page_width, height=page_height)

        def _new_page():
            nonlocal page, y
            page = doc.new_page(width=page_width, height=page_height)
            y = margin

        lines = (md_text or "").splitlines()
        for raw in lines:
            line = raw.rstrip()
            if not line:
                y += 10
                if y > page_height - margin - 20:
                    _new_page()
                continue

            if line.startswith("# "):
                fontsize = 18
                text = line[2:].strip()
            elif line.startswith("## "):
                fontsize = 14
                text = line[3:].strip()
            else:
                fontsize = 11
                text = line

            rect = fitz.Rect(margin, y, margin + usable_width, page_height - margin)
            consumed = page.insert_textbox(
                rect,
                text,
                fontsize=fontsize,
                fontname="helv",
                lineheight=1.35,
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )

            # If not enough room, start a new page and write again.
            if consumed < 0:
                _new_page()
                rect = fitz.Rect(margin, y, margin + usable_width, page_height - margin)
                page.insert_textbox(
                    rect,
                    text,
                    fontsize=fontsize,
                    fontname="helv",
                    lineheight=1.35,
                    color=(0, 0, 0),
                    align=fitz.TEXT_ALIGN_LEFT,
                )

            # Rough vertical advance per paragraph; keeps layout readable.
            y += max(16, fontsize * 1.8)
            if y > page_height - margin - 30:
                _new_page()

        doc.save(pdf_path)
        doc.close()
        return True
    except Exception as e:
        print(f"[pdf] markdown to pdf failed: {e}", flush=True)
        return False


def _fetch_elsevier_fulltext_via_api(doi, save_dir, paper):
    if not doi or not ELSEVIER_API_KEY:
        return None
    try:
        url = f"https://api.elsevier.com/content/article/doi/{quote_plus(doi)}?view=FULL&httpAccept=text/xml"
        r = _requests_get(
            url,
            headers={
                "X-ELS-APIKey": ELSEVIER_API_KEY,
                "Accept": "text/xml",
                "User-Agent": head["user-agent"],
            },
            timeout=15,
            allow_redirects=True,
        )
        if r.status_code != 200:
            return None
        xml_text = r.text or ""
        if "<full-text-retrieval-response" not in xml_text:
            return None

        md = _extract_elsevier_fulltext_markdown(xml_text)
        clean_txt = _markdown_to_clean_text(md)
        if len(clean_txt) < 5000:
            return None

        name = _safe_name_from_paper(paper)
        md_path = os.path.join(save_dir, f"{name}.md")
        txt_path = os.path.join(save_dir, f"{name}.txt")
        pdf_path = os.path.join(save_dir, f"{name}.pdf")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(clean_txt)
        pdf_ok = False
        if GENERATE_PDF_FROM_XML:
            pdf_ok = _markdown_to_pdf_file(md, pdf_path)
        paper["fulltext_markdown_path"] = md_path
        paper["fulltext_text_path"] = txt_path
        if pdf_ok and os.path.exists(pdf_path):
            return pdf_path
        return txt_path
    except Exception as e:
        print(f"[elsevier] fulltext api fetch failed for {doi}: {e}", flush=True)
        return None


def _clean_title_text(title):
    t = re.sub(r"<[^>]*>", " ", title or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _title_keywords(title, max_k=6):
    t = _clean_title_text(title).lower()
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{3,}", t)
    stop = {
        "articletitle", "study", "analysis", "based", "through", "with",
        "from", "that", "this", "their", "into", "using", "triple",
        "negative", "breast", "cancer",
    }
    kws = []
    for tok in tokens:
        if tok in stop:
            continue
        if tok not in kws:
            kws.append(tok)
        if len(kws) >= max_k:
            break
    return kws


def _looks_like_placeholder_page(text):
    if not text:
        return True
    t = text.lower()
    bad_phrases = [
        "正在加载",
        "系统目前无法执行此操作",
        "请稍后再试",
        "热门出版物",
        "学术资源搜索",
        "暂时不可用",
        "service unavailable",
        "access denied",
        "cloudflare",
        "captcha",
    ]
    return any(p in t for p in bad_phrases)


def _is_plausible_fulltext(text, doi="", title=""):
    if not text or len(text) < 3000:
        return False
    if _looks_like_placeholder_page(text):
        return False

    low = text.lower()
    if doi and doi.lower() in low:
        return True

    kws = _title_keywords(title)
    if not kws:
        # fallback structural check
        sections = ["abstract", "introduction", "methods", "results", "discussion", "references"]
        hit = sum(1 for s in sections if s in low)
        return hit >= 3

    hit = sum(1 for k in kws if k in low)
    return hit >= max(2, min(4, len(kws)))


def _extract_pdf_candidates_from_html(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    # High-confidence publisher meta tags
    for attr in ["citation_pdf_url", "dc.identifier", "pdf_url"]:
        tag = soup.find("meta", attrs={"name": attr}) or soup.find("meta", attrs={"property": attr})
        if tag and tag.get("content"):
            candidates.append(urljoin(base_url, tag.get("content").strip()))

    # Generic link scan
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        href_low = href.lower()
        text_low = (a.get_text() or "").lower()
        if ".pdf" in href_low or "pdf" in text_low:
            candidates.append(urljoin(base_url, href))

    uniq = []
    seen = set()
    for u in candidates:
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq[:10]


def _try_download_pdf_from_candidates(candidates, save_path):
    for u in candidates:
        try:
            r = _requests_get(
                u,
                headers={
                    "user-agent": head["user-agent"],
                    "accept": "application/pdf,*/*;q=0.8",
                    "referer": u,
                },
                timeout=FAST_FETCH_TIMEOUT,
                allow_redirects=True,
            )
            if r.status_code >= 400:
                continue
            ctype = (r.headers.get("content-type") or "").lower()
            if "application/pdf" in ctype or r.content[:5] == b"%PDF-":
                _save_bytes(r.content, save_path)
                return save_path
        except Exception:
            continue
    return None


def _try_download_pdf_from_scholar_mirrors(doi, title, save_path):
    mirrors = _get_scholar_mirrors_daily()
    if not mirrors:
        return None

    query = doi or title
    if not query:
        return None

    for base in mirrors:
        try:
            scholar_url = urljoin(base.rstrip("/") + "/", "scholar")
            r = _requests_get(
                scholar_url,
                params={"q": query, "hl": "zh-CN"},
                headers=head,
                timeout=FAST_FETCH_TIMEOUT,
                allow_redirects=True,
            )
            if r.status_code >= 400:
                continue
            links = _extract_pdf_candidates_from_html(r.url or scholar_url, r.text or "")
            got = _try_download_pdf_from_candidates(links, save_path)
            if got:
                return got
        except Exception:
            continue
    return None


def _extract_pdf_links_from_scihub_page(base_url, html):
    soup = BeautifulSoup(html or "", "html.parser")
    candidates = []

    for tag_name in ["embed", "iframe"]:
        for t in soup.find_all(tag_name):
            src = (t.get("src") or "").strip()
            if src:
                candidates.append(urljoin(base_url, src))

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        text_low = (a.get_text() or "").lower()
        href_low = href.lower()
        if ".pdf" in href_low or "pdf" in text_low or "download" in text_low:
            candidates.append(urljoin(base_url, href))

    uniq = []
    seen = set()
    for u in candidates:
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(u)
    return uniq[:12]


def _try_download_pdf_from_scihub_mirrors(doi, save_path, max_mirrors=1):
    if not doi:
        return None
    mirrors = _get_scihub_mirrors_daily()
    if not mirrors:
        return None

    for base in mirrors[:max_mirrors]:
        try:
            page_url = urljoin(base.rstrip("/") + "/", doi)
            r = _requests_get(
                page_url,
                headers={
                    "user-agent": head["user-agent"],
                    "accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
                    "referer": base,
                },
                timeout=FAST_FETCH_TIMEOUT,
                allow_redirects=True,
            )
            if r.status_code >= 400:
                continue
            ctype = (r.headers.get("content-type") or "").lower()
            if "application/pdf" in ctype or r.content[:5] == b"%PDF-":
                _save_bytes(r.content, save_path)
                return save_path

            links = _extract_pdf_links_from_scihub_page(r.url or page_url, r.text or "")
            got = _try_download_pdf_from_candidates(links, save_path)
            if got:
                return got
        except Exception:
            continue
    return None


def _fetch_fulltext_text_from_scholar_mirrors(doi, title):
    mirrors = _get_scholar_mirrors_daily()
    if not mirrors:
        return None

    query = doi or title
    if not query:
        return None

    for base in mirrors:
        try:
            scholar_url = urljoin(base.rstrip("/") + "/", "scholar")
            r = _requests_get(
                scholar_url,
                params={"q": query, "hl": "zh-CN"},
                headers=head,
                timeout=FAST_FETCH_TIMEOUT,
                allow_redirects=True,
            )
            if r.status_code >= 400:
                continue

            # 1) if result page itself already contains long readable text, use it directly.
            result_text = _extract_html_text(r.text or "")
            if _is_plausible_fulltext(result_text, doi=doi, title=title):
                return result_text

            # 2) otherwise collect candidate links and fetch several quickly in parallel.
            links = _extract_pdf_candidates_from_html(r.url or scholar_url, r.text or "")
            # add all href candidates, not only pdf-like links, for full-text scraping speed path.
            soup = BeautifulSoup(r.text or "", "html.parser")
            for a in soup.find_all("a", href=True):
                links.append(urljoin(r.url or scholar_url, a["href"]))

            uniq = []
            seen = set()
            for u in links:
                if not u or u in seen or not u.startswith(("http://", "https://")):
                    continue
                seen.add(u)
                uniq.append(u)
            candidates = uniq[:8]
            if not candidates:
                continue

            def _fetch_one(u):
                try:
                    rr = _requests_get(u, headers=head, timeout=FAST_FETCH_TIMEOUT, allow_redirects=True)
                    if rr.status_code >= 400:
                        return None
                    ctype = (rr.headers.get("content-type") or "").lower()
                    if "application/pdf" in ctype:
                        return None
                    txt = _extract_html_text(rr.text or "")
                    if _is_plausible_fulltext(txt, doi=doi, title=title):
                        return txt
                except Exception:
                    return None
                return None

            workers = min(4, len(candidates))
            with ThreadPoolExecutor(max_workers=workers) as ex:
                for txt in ex.map(_fetch_one, candidates):
                    if txt:
                        return txt
        except Exception:
            continue
    return None


def _llm_extract_pdf_candidates(doi, title, landing_url, landing_html):
    if not ENABLE_LLM_PDF_LINK_FINDER:
        return []
    try:
        html_snippet = (landing_html or "")[:12000]
        prompt = f"""
You are extracting direct PDF links for an academic paper.
Return JSON only in this exact format:
{{"urls":["https://...","https://..."]}}

Rules:
- Only include absolute HTTP/HTTPS URLs likely to return the full paper PDF.
- Prefer publisher/official/OA repository links.
- No explanation, no markdown.

DOI: {doi}
Title: {title}
Landing URL: {landing_url}
Landing HTML snippet:
{html_snippet}
""".strip()

        text, _, _ = model_generate(
            prompt,
            model=MODEL_NANO,
            temperature=0,
            is_messages=False,
        )
        text = (text or "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        data = json.loads(text)
        urls = data.get("urls") or []
        urls = [u.strip() for u in urls if isinstance(u, str) and u.strip().startswith(("http://", "https://"))]
        return urls[:10]
    except Exception:
        return []


def _try_download_pdf_from_unpaywall(doi, save_path):
    if not doi:
        return None
    try:
        api = f"https://api.unpaywall.org/v2/{doi}"
        r = _requests_get(api, params={"email": "bioresearcher@example.com"}, timeout=FAST_FETCH_TIMEOUT)
        if r.status_code >= 400:
            return None
        data = r.json()
        urls = []
        best = (data.get("best_oa_location") or {}).get("url_for_pdf")
        if best:
            urls.append(best)
        for loc in data.get("oa_locations") or []:
            u = loc.get("url_for_pdf")
            if u:
                urls.append(u)
        return _try_download_pdf_from_candidates(urls, save_path)
    except Exception:
        return None


def _try_download_pdf_from_doi_landing(doi, save_dir, title=""):
    if not doi:
        return None
    try:
        save_path = os.path.join(save_dir, f"{doi.replace('/', '_')}.pdf")

        # 0) OA resolver first (fast and legal source)
        from_unpaywall = _try_download_pdf_from_unpaywall(doi, save_path)
        if from_unpaywall:
            return from_unpaywall

        # 1) DOI resolver
        url = f"https://doi.org/{doi}"
        r = _requests_get(
            url,
            headers={
                "user-agent": head["user-agent"],
                "accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
            },
            timeout=FAST_FETCH_TIMEOUT,
            allow_redirects=True,
        )
        if r.status_code >= 400:
            return None
        ctype = (r.headers.get("content-type") or "").lower()
        if "application/pdf" in ctype:
            _save_bytes(r.content, save_path)
            return save_path

        # 2) Parse landing page and try discovered PDF URLs
        final_url = r.url or url
        pdf_links = _extract_pdf_candidates_from_html(final_url, r.text or "")
        from_landing = _try_download_pdf_from_candidates(pdf_links, save_path)
        if from_landing:
            return from_landing

        # 3) LLM-assisted candidate extraction (only as supplement; still strict-validated)
        llm_candidates = _llm_extract_pdf_candidates(doi, title or "", final_url, r.text or "")
        if llm_candidates:
            from_llm = _try_download_pdf_from_candidates(llm_candidates, save_path)
            if from_llm:
                return from_llm
    except Exception:
        return None
    return None


def _fetch_fulltext_text_for_paper(paper):
    pmcid = str(paper.get("pmcid") or "").strip()
    doi = str(paper.get("doi") or "").strip()
    candidates = []

    if pmcid:
        pmc = pmcid if pmcid.upper().startswith("PMC") else f"PMC{pmcid}"
        candidates.extend(
            [
                f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/",
                f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/",
                f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/{pmc}/unicode",
            ]
        )
    if doi:
        candidates.append(f"https://doi.org/{doi}")

    for url in candidates:
        try:
            r = _requests_get(url, headers=head, timeout=FAST_FETCH_TIMEOUT, allow_redirects=True)
            if r.status_code >= 400:
                continue
            ctype = (r.headers.get("content-type") or "").lower()
            if "application/pdf" in ctype:
                continue
            text = ""
            if "bionlp/RESTful/pmcoa.cgi/BioC_xml/" in url or "xml" in ctype:
                raw = ""
                try:
                    raw = r.content.decode("utf-8", errors="replace")
                except Exception:
                    try:
                        raw = r.text
                    except Exception:
                        raw = ""
                text = _extract_bioc_plain_text(raw) or raw
                text = _fix_mojibake_text(text)
            elif "html" in ctype:
                html = r.text
                if _mojibake_score(html) > 0:
                    html = _fix_mojibake_text(html)
                text = _extract_html_text(html)
            else:
                try:
                    text = r.text
                    text = _fix_mojibake_text(text)
                except Exception:
                    text = ""
            if _is_plausible_fulltext(text, doi=doi, title=paper.get("title", "")):
                return text
        except Exception:
            continue
    return None


def _recover_failed_paper(paper, save_dir):
    doi = paper.get("doi")
    title = paper.get("title", "")
    save_path = os.path.join(save_dir, f"{_safe_name_from_paper(paper)}.pdf")

    # Priority 2: Sci-Hub mirror (single fast fallback before scholar mirrors).
    from_scihub_mirror = _try_download_pdf_from_scihub_mirrors(doi, save_path, max_mirrors=1)
    if from_scihub_mirror and os.path.exists(from_scihub_mirror):
        paper["path"] = from_scihub_mirror
        paper["recovered_via"] = "scihub_mirror_pdf"
        return True, paper

    # Priority 3: Google Scholar mirrors (priority 1 already attempted by download_pdf()).
    from_scholar_mirror = _try_download_pdf_from_scholar_mirrors(doi, title, save_path)
    if from_scholar_mirror and os.path.exists(from_scholar_mirror):
        paper["path"] = from_scholar_mirror
        paper["recovered_via"] = "scholar_mirror_pdf"
        return True, paper

    # Priority 4: dynamic + API-assisted link discovery
    if doi:
        pdf_path = _try_download_pdf_from_doi_landing(doi, save_dir, title)
        if pdf_path and os.path.exists(pdf_path):
            paper["path"] = pdf_path
            paper["recovered_via"] = "doi_pdf"
            return True, paper

    if doi:
        elsevier_txt = _fetch_elsevier_fulltext_via_api(doi, save_dir, paper)
        if elsevier_txt and os.path.exists(elsevier_txt):
            paper["path"] = elsevier_txt
            if str(elsevier_txt).lower().endswith(".pdf"):
                paper["recovered_via"] = "elsevier_fulltext_api_pdf"
            else:
                paper["fallback_text"] = True
                paper["recovered_via"] = "elsevier_fulltext_api_text"
            return True, paper

    scholar_fulltext = _fetch_fulltext_text_from_scholar_mirrors(doi, title)
    if scholar_fulltext:
        try:
            path = _write_txt_and_md(
                scholar_fulltext,
                save_dir,
                paper,
                title=_clean_title_text(title) or "Scholar Recovered Full Text",
            )
            paper["path"] = path
            paper["fallback_text"] = True
            paper["recovered_via"] = "scholar_fulltext"
            return True, paper
        except Exception:
            pass

    # Priority 4: fulltext/abstract text fallback
    full_text = _fetch_fulltext_text_for_paper(paper)
    if full_text:
        try:
            path = _write_txt_and_md(
                full_text,
                save_dir,
                paper,
                title=_clean_title_text(title) or "Recovered Full Text",
            )
            paper["path"] = path
            paper["fallback_text"] = True
            paper["recovered_via"] = "fulltext_html"
            return True, paper
        except Exception:
            pass

    fallback_path = _create_fallback_text_file(paper, save_dir)
    if fallback_path is not None:
        try:
            txt = read_txt(fallback_path)
            _write_txt_and_md(
                txt,
                save_dir,
                paper,
                title=_clean_title_text(title) or "Abstract Fallback",
            )
        except Exception:
            pass
        paper["path"] = fallback_path
        paper["fallback_text"] = True
        paper["recovered_via"] = "abstract_fallback"
        return True, paper

    return False, paper


def download_pdf(doi_list, save_dir):
    fail_papers = []
    # 浣跨敤sci-hub涓嬭浇
    for doi in doi_list:
        if os.path.exists(save_dir + "/" + doi.replace("/", "_") + ".pdf"):
            print("paper {} already exists.".format(doi), flush=True)
            continue
        # 鎷兼帴缃戝潃
        #url = "https://www.sci-hub.pl/" + line + "#"  #sci hub鐨凞OI鐮佹绱rl  杩欎釜鍦板潃宸茬粡澶辨晥浜?
        url = "https://www.sci-hub.ren/" + doi + "#"  #
        url = 'https://www.et-fine.com/' + doi + '#'
        # url = "https://www.sci-hub.st/" + doi + "#"
        retry = 0
        while retry < DOWNLOAD_RETRY:
            try:
                download_url = ""
                # 璇锋眰鏂囦欢浣嶇疆
                r = _requests_get(url, headers=head, timeout=2)
                r.raise_for_status()
                r.encoding = r.apparent_encoding
                # 瑙ｆ瀽
                soup = BeautifulSoup(r.text, "html.parser")
                # download_url = "https:" + str(soup.div.ul.find(href="#")).split("href='")[-1].split(".pdf")[0] + ".pdf" #瀵绘壘鍑哄瓨鏀捐鏂囩尞鐨刾df璧勬簮鍦板潃锛堣妫€绱㈠凡澶辨晥锛?
                if soup.iframe == None:
                    download_url = "https:" + soup.embed.attrs["src"]
                else:
                    download_url = soup.iframe.attrs["src"]  #
                print(doi + " is downloading...\n  --The download url is: " +
                      download_url, flush=True)
                download_r = _requests_get(download_url, headers=head, timeout=6)
                download_r.raise_for_status()
                # 淇濆瓨鏂囦欢
                with open(save_dir + "/" + doi.replace("/", "_") + ".pdf", "wb+") as temp:
                    temp.write(download_r.content)
                    print(doi + " download successfully.\n",flush=True)
                    break
            except:
                retry += 1
        if retry == DOWNLOAD_RETRY:
            print(doi + " occurs error!\n",flush=True)
            fail_papers.append(doi)
    return fail_papers


def llm_related(aim: Annotated[str, "The research aim."], conditions: Annotated[str, "The research conditions."], requirements: Annotated[str, "Hard requirements to be implemented in experimental design."], papers_list: Annotated[list, "A list of papers with their titles and abstract."], model=MODEL_NANO) -> tuple:
    '''if len(requirements) > 0:
        requirements = "Research requirements: " + requirements'''
    results = []
    all_results = []
    input_tok = 0
    output_tok = 0
    for i in papers_list:
        if i["abstract"] == 'No abstract':
            continue
        retry = 0
        while retry < 3:
            try:
                response = model_generate(filter_prompt.format(aim, conditions, requirements, i["title"], i["abstract"]), model)
                input_tok += response[1]
                output_tok += response[2]
                response = response[0]
                score = parse_bracket_score(response, default=0.0)
                i["score"] = score
                i["llm_response_check4related"] = response
                all_results.append(i)
                if score >= 4:
                    print("paper \"{}\" is helpful to research!".format(i["title"]), flush=True)
                    results.append(i)
                    break
                else:
                    print("paper \"{}\" isn't helpful to research!".format(i["title"]), flush=True)
                    break
            except Exception as e:
                retry += 1

    return results, input_tok, output_tok, all_results

def generate_query(target, conditions, requirements, model=MODEL_NANO):
    response = model_generate(query_generator_prompt.format(target, conditions, requirements), model=model)
    input_tok = response[1]
    output_tok = response[2]
    response = response[0]
    terms = re.findall('\[(.*)\]',response)
    '''print("Terms for search:")
    print(terms)'''
    return terms, input_tok, output_tok, response

def parse_pubmed(root, search_query):
    pubmed_papers = []
    print("get {} papers".format(len(root.findall('PubmedArticle'))), flush=True)
    for pubmed_article in root.findall('PubmedArticle'):#'article' when pmc
        title = ET.tostring(pubmed_article.find('MedlineCitation/Article/ArticleTitle'), encoding='unicode')
        abstract = pubmed_article.find('MedlineCitation/Article/Abstract/AbstractText')
        if abstract is None:
            continue
        text_nodes = abstract.itertext()
        abstract = ''.join(text_nodes)
        pmid = pubmed_article.find('MedlineCitation/PMID').text
        pmcid = get_pmcid(pmid)
        try:
            doi = pubmed_article.find('MedlineCitation/Article/ELocationID[@EIdType="doi"]').text
        except:
            doi = None
        pubmed_papers.append({"title":title, "abstract": abstract, "doi":doi, "pmid":pmid, "pmcid":pmcid, "search_query":search_query})
        #get_pdf_link(doi)
    return pubmed_papers
    #download_pdf(data["doi"])


def parse_pmc(root, search_query):
    print("get {} papers".format(len(root.findall('.//article'))), flush=True)
    pmc_papers = []
    for pmc_article in root.findall('.//article'):#'article' when pmc
        title = ET.tostring(pmc_article.find('.//article-title'), encoding='unicode')
        abstract_elem = pmc_article.find('.//abstract')
        abstract = ' '.join(ET.tostring(p, encoding='unicode') for p in abstract_elem.findall('.//p')) if abstract_elem is not None else 'No abstract'
        ids = pmc_article.findall(".//article-id")
        doi = None
        pmid = None
        pmcid = None
        for i in ids:
            doi = None
            pmid = None
            pmcid = None
            if i.get("pub-id-type") == "doi":
                doi = i.text
            elif i.get("pub-id-type") == "pmid":
                pmid = i.text
            elif i.get("pub-id-type") == "pmc":
                pmcid = i.text

        pmc_papers.append({"title":title, "abstract": abstract, "doi":doi, "pmid":pmid, "pmcid":pmcid, "search_query":search_query})
        '''def get_paragraph_text(p_elem):
            text = ''
            for elem in p_elem.iter():
                if elem.text and elem.text.strip()!="":
                    text += elem.text
                if elem.tail and elem.tail.strip()!="":
                    text += elem.tail

            return text

        def parse_section(sec, level=1):
            sec_id = sec.get('id', 'No ID')
            sec_title_elem = sec.find('title')
            sec_title = get_paragraph_text(sec_title_elem) if sec_title_elem is not None else 'No section title'
            sec_text = '\n'.join(get_paragraph_text(p) for p in sec.findall('p'))

            # 瑙ｆ瀽鍥句緥
            fig_text = ''
            for fig in sec.findall('fig'):
                fig_caption = fig.find('caption')
                fig_label = fig.find('label')
                if fig_caption is not None:
                    fig_text += fig_label.text + '\n'.join(get_paragraph_text(p) for p in fig_caption.findall('p')) + '\n'
            try:
                sections.append({
                    'SectionID': sec_id,
                    'SectionTitle': 'sub'*(level-1) + 'section: ' + sec_title,
                    'SectionText': sec_text,
                    'Figure': fig_text
                })
            except:
                print("error!")

            for sub_sec in sec.findall('.//sec'):
                parse_section(sub_sec, level + 1)
        body_text = ''
        body_elem = pmc_article.find('.//body')
        if body_elem is not None:
            body_text = ET.tostring(body_elem, encoding='utf-8').decode('utf-8')
            for sec in body_elem.findall('sec'):
                parse_section(sec)

        full_text = ""
        for section in sections:
            full_text += section["SectionTitle"] + "\n" + section["SectionText"] + "\n\n" + section["Figure"] + "\n\n"
        with open(doi.replace("/", "_") + ".txt", "w", encoding="utf-8") as writer:
            writer.write(title + "\n\nAbstract: " + abstract + "\n\n" + body_text)'''
    return pmc_papers

def deduplication(data):
    def get_key(d, key):
        return d[key] if d[key] is not None else d["title"]
        # Step 1: Deduplicate based on 'pmcid'

    data = {get_key(d, 'pmcid'): d for d in data}.values()
    data = list(data)

    # Step 2: Deduplicate based on 'doi'
    data = {get_key(d, 'doi'): d for d in data}.values()
    data = list(data)

    # Step 3: Deduplicate based on 'pmid'
    data = {get_key(d, 'pmid'): d for d in data}.values()
    data = list(data)

    return data

def search_in_database(queries: Annotated[list, "Boolean queries for PubMed or PubMed Central."], retmax: Annotated[int, "Maximum number of retrieved papers."]) -> list:
    # 瀹氫箟NCBI Entrez Programming Utilities鐨刄RL
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    #retmax = 5  # 瑕佽繑鍥炵殑鏂囩尞鏁伴噺
    data = []
    database = ['pubmed', 'pmc']
    if isinstance(queries, str):
        queries = [queries]
    for db in database:
        print("Database: ", db, flush=True)
        for term in queries:
            print("Searching for {}...".format(term), flush=True)
            # 鏋勯€燛Search璇锋眰
            params = {
                'db': db,
                'term': term,
                'usehistory': 'y',
                'api_key': ncbi_api,
                'sort': 'pub_date'
            }
            response = _requests_get(base_url + 'esearch.fcgi', params=params)

            # 瑙ｆ瀽ESearch鍝嶅簲浠ヨ幏鍙朩ebEnv鍜孮ueryKey
            root = ET.fromstring(response.content)
            webenv = root.find('WebEnv').text
            query_key = root.find('QueryKey').text

            # 鏋勯€燛Fetch璇锋眰浠ヨ幏鍙栨枃妗ｅ叏鏂?
            params = {
                'db': db,
                'query_key': query_key,
                'WebEnv': webenv,
                #'rettype': 'xml',   #full
                'retmode': 'xml',
                'retmax': str(retmax),
                'api_key': ncbi_api
            }
            response = _requests_get(base_url + 'efetch.fcgi', params=params)
            # 瑙ｆ瀽EFetch鍝嶅簲浠ヨ幏鍙栨枃妗ｅ叏鏂?
            root = ET.fromstring(response.content)
            time.sleep(1)
            if db == "pubmed":
                data.extend(parse_pubmed(root, term))
            elif db == "pmc":
                data.extend(parse_pmc(root, term))
    data = deduplication(data)
    #print(data)
    return data

def download_paper(papers: Annotated[list, "A list of papers to be downloaded."], save_dir: Annotated[str, "The directory of downloaded papers."], papers_info_path) -> dict:
    pmc_papers = []
    doi_papers = []
    fail_papers = []
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    for p in papers:
        if p["pmcid"] is not None:
            pmc_papers.append([p["pmcid"], p["title"]])
        elif p["doi"] is not None:
            doi_papers.append(p["doi"])
        else:
            fail_papers.append(p)
    fail_pmc = []
    fail_doi = []
    if len(pmc_papers) > 0:
        fail_pmc = downpmc(pmc_papers, save_dir)
    if len(doi_papers) > 0:
        fail_doi = download_pdf(doi_papers, save_dir)
    fail_papers.extend([p for p in papers if p["pmcid"] is not None and p["pmcid"] in fail_pmc])
    fail_papers.extend([p for p in papers if p["doi"] is not None and p["doi"] in fail_doi])
    success_papers = [p for p in papers if p not in fail_papers]
    for p in success_papers:
        if p["pmcid"] is not None:
            p["path"] = save_dir + "/" + p["pmcid"] + ".pdf"
        else:
            p["path"] = save_dir + "/" + p["doi"].replace("/", "_") + ".pdf"

    # Fast recovery for failed papers:
    # 1) try DOI direct PDF
    # 2) try full-text HTML/XML extraction
    # 3) fallback to metadata+abstract txt
    still_failed = []
    if fail_papers:
        workers = min(MAX_RECOVER_WORKERS, len(fail_papers))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for ok, paper in executor.map(lambda p: _recover_failed_paper(p, save_dir), fail_papers):
                if ok:
                    success_papers.append(paper)
                else:
                    still_failed.append(paper)
    fail_papers = still_failed

    if os.path.exists(papers_info_path):
        data = {"download successfully": success_papers, "download failed": fail_papers}
        old_data = read_json(papers_info_path)
        data.update(old_data)

    with open(papers_info_path, "w", encoding="utf-8") as out:
        data = {"download successfully": success_papers, "download failed": fail_papers}
        json.dump(data, out, indent=4, ensure_ascii=False)
    return data



def search_download(
    objective,
    conditions,
    requirements,
    model,
    retmax,
    savedir,
    retrieved_paper_info_path,
    related_paper_info_path,
    max_search_times=5,
):
    input_tokens = 0
    output_tokens = 0
    search_times = 0
    useful_papers = []
    total_papers = []
    total_queries = []
    full_res_record = {}
    data = {"download successfully": [], "download failed": []}
    last_search_error = None
    while search_times < max_search_times:
        cheap_model = MODEL_NANO
        queries = generate_query(objective, conditions, requirements, cheap_model)
        input_tokens += queries[1]
        output_tokens += queries[2]
        full_res = queries[3]
        full_res_record[search_times] = {}
        full_res_record[search_times]["search"] = {"full_llm_res": full_res, "search_queries": queries[0]}
        full_res_record[search_times]["filter"] = "LLM filter responses are recorded in each related paper tuple."
        queries = queries[0]
        total_queries.extend(queries)

        retry = 0
        while retry < max_retry_times:
            try:
                paperlist = search_in_database(queries, retmax)
                last_search_error = None
                break
            except Exception as e:
                last_search_error = e
                retry += 1
        if retry == max_retry_times:
            print(f"Warning: search_in_database failed after retries: {last_search_error}", flush=True)
            # Keep the pipeline alive with partial results instead of hard stop.
            break
        print("retrieved {} papers.".format(len(paperlist)), flush=True)
        titles = [d["title"] for d in total_papers if "title" in d]
        paperlist = [i for i in paperlist if i["title"] not in titles]
        print("{} papers is new.".format(len(paperlist)), flush=True)
        paperlist = llm_related(objective, conditions, requirements, paperlist, cheap_model)
        print("get {} useful papers.".format(len(paperlist[0])), flush=True)
        input_tokens += paperlist[1]
        output_tokens += paperlist[2]
        total_papers.extend(paperlist[3])
        useful_papers.extend(paperlist[0])
        useful_papers = deduplication(useful_papers)
        print("totally get {} useful papers.".format(len(useful_papers)), flush=True)
        total_papers = deduplication(total_papers)
        useful_papers = sorted(useful_papers, key=lambda x: x["score"], reverse=True)
        data = download_paper(useful_papers, savedir, related_paper_info_path)
        if len(data["download successfully"]) >= 10:
            break
        else:
            search_times += 1

    # Ensure paper info files exist even when search stage partially fails.
    if not os.path.exists(related_paper_info_path):
        with open(related_paper_info_path, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=4, ensure_ascii=False)
    write_json(total_papers, retrieved_paper_info_path)
    '''useful_papers = sorted(useful_papers, key=lambda x:x["score"], reverse=True)
    data = download_paper(useful_papers, savedir, related_paper_info_path)
    if len(data["download successfully"]) >= 10:'''

    flag = True
    if len(data["download failed"]) > 0 or last_search_error is not None:
        print(f"Warning: There are {len(data['download failed'])} papers that failed to download, please download them manually!")
        flag = False
    print(input_tokens, output_tokens, flush=True)
    return total_queries, input_tokens, output_tokens, flag, full_res_record

def search_download_with_query(objective, conditions, requirements, queries, model, retmax, savedir, retrieved_paper_info_path, related_paper_info_path):
    input_tokens = 0
    output_tokens = 0
    search_times = 0
    useful_papers = []
    total_papers = []
    retry = 0
    while retry < max_retry_times:
        try:
            paperlist = search_in_database(queries, retmax)
            break
        except:
            retry += 1
    if retry == max_retry_times:
        raise Exception("search failed.")
    print("retrieved {} papers.".format(len(paperlist)), flush=True)
    titles = [d["title"] for d in total_papers if "title" in d]
    paperlist = [i for i in paperlist if i["title"] not in titles]
    print("{} papers is new.".format(len(paperlist)), flush=True)
    paperlist = llm_related(objective, conditions, requirements, paperlist, MODEL_NANO)
    print("get {} useful papers.".format(len(paperlist[0])), flush=True)
    input_tokens += paperlist[1]
    output_tokens += paperlist[2]
    total_papers.extend(paperlist[3])
    useful_papers.extend(paperlist[0])
    useful_papers = deduplication(useful_papers)
    print("totally get {} useful papers.".format(len(useful_papers)), flush=True)
    total_papers = deduplication(total_papers)
    useful_papers = sorted(useful_papers, key=lambda x: x["score"], reverse=True)
    data = download_paper(useful_papers, savedir, related_paper_info_path)
    write_json(total_papers, retrieved_paper_info_path)
    '''useful_papers = sorted(useful_papers, key=lambda x:x["score"], reverse=True)
    data = download_paper(useful_papers, savedir, related_paper_info_path)
    if len(data["download successfully"]) >= 10:'''

    flag = True
    if len(data["download failed"]) > 0:
        print(f"Warning: There are {len(data['download failed'])} papers that failed to download, please download them manually!")
        flag = False
    print(input_tokens, output_tokens, flush=True)
    return queries, input_tokens, output_tokens, flag





