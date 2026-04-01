# -*- coding: utf-8 -*-
import os
import random
import re
import sqlite3
import time
import urllib
import urllib.error
from urllib import request
import socket
import json
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup


CLASH_SUB_CACHE = Path(__file__).parent.parent / "data" / "clash_sub_cache.json"


def _load_sub_ports_from_cache():
    try:
        if not CLASH_SUB_CACHE.exists():
            return []
        data = json.loads(CLASH_SUB_CACHE.read_text(encoding="utf-8"))
        ports = data.get("ports") or []
        return [int(p) for p in ports if isinstance(p, int) or (isinstance(p, str) and p.isdigit())]
    except Exception:
        return []


def _install_system_proxy_for_urllib():
    """Install a global urllib opener that honors system proxy settings."""
    try:
        proxies = urllib.request.getproxies()
        if not proxies:
            for port in _load_sub_ports_from_cache():
                try:
                    with socket.create_connection(("127.0.0.1", int(port)), timeout=0.8):
                        proxy = f"http://127.0.0.1:{int(port)}"
                        proxies = {"http": proxy, "https": proxy}
                        break
                except Exception:
                    continue
        if not proxies:
            # Fallback for Clash rule mode: common local proxy ports.
            for host, port in [("127.0.0.1", 7890), ("127.0.0.1", 7897), ("127.0.0.1", 10809)]:
                try:
                    with socket.create_connection((host, port), timeout=0.8):
                        proxy = f"http://{host}:{port}"
                        proxies = {"http": proxy, "https": proxy}
                        break
                except Exception:
                    continue
        if not proxies:
            manual = os.getenv("DOWNLOAD_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
            if manual:
                if "://" not in manual:
                    manual = f"http://{manual}"
                proxies = {"http": manual, "https": manual}
        if proxies:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
            urllib.request.install_opener(opener)
            print(f"[proxy] urllib using system proxies: {proxies}")
        else:
            print("[proxy] urllib found no system proxy.")
    except Exception as e:
        print(f"[proxy] urllib proxy setup failed: {e}")


_install_system_proxy_for_urllib()


def get_pmcid(pmid):
    baseurl = "https://pubmed.ncbi.nlm.nih.gov/"
    PMID = str(pmid)
    url = baseurl + PMID
    header = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32"
        )
    }
    req = urllib.request.Request(url, headers=header)
    try:
        response = urllib.request.urlopen(req)
        html = response.read()
        content = BeautifulSoup(html, "html.parser")

        heading = content.find_all("div", class_="full-view", id="full-view-heading")
        heading = str(heading)
        pmcid_match = re.search(r"(PMC\\d+)\\n", heading)
        if pmcid_match is None:
            return None
        return pmcid_match.group(1).replace("PMC", "")
    except Exception as e:
        print(e)
        return None


# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9034016/pdf/main.pdf
def downpdf(parameter):
    downpara = "pmc/articles/PMC" + parameter + "/pdf/main.pdf"
    baseurl = "https://www.ncbi.nlm.nih.gov/"
    url = baseurl + downpara
    timeout_flag = 0
    header = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32"
        )
    }
    req = urllib.request.Request(url, headers=header)

    try:
        response = urllib.request.urlopen(req, timeout=25)
        html = response.read()
        print("%s.pdf" % parameter, "downloaded")
        return html
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
        timeout_flag = 1
        return timeout_flag
    except TimeoutError:
        timeout_flag = 1
        print("download timeout")
        return timeout_flag
    except Exception:
        print("%s.pdf" % parameter, "download failed")
        return timeout_flag


def savepdf(html, PMCID, save_dir):
    try:
        savepath = save_dir + "/" + PMCID + ".pdf"
        with open(savepath, "wb") as file:
            file.write(html)
        print("saved", savepath)
        return True
    except Exception:
        print("save failed", PMCID)
        return False


def downpmc(result, save_dir):
    fail_papers = []
    for item in result:
        if os.path.exists(save_dir + "/" + item[0] + ".pdf"):
            print("exists {}".format(item[0]))
            continue
        retry = 0
        while retry < 2:
            print("start downloading %s.pdf" % item[0])
            html = downpdf(item[0])
            if html is None:
                print("pdf missing, skip", item[0])
            elif html == 1:
                print("timeout, skip", item[0])
            if savepdf(html, item[0], save_dir):
                time.sleep(random.randint(0, 1))
                break
            retry += 1
        if retry == 2:
            fail_papers.append(item[0])
    return fail_papers
