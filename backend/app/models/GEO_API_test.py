import time

import requests
import json
import os
import bs4
import random

ncbi_api = 'ca7d6c6adb62c9ad9571230ba66728f54f08'


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
            response = requests.get(base_url, params=params)
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
    response = requests.get(url, params=params)
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

    response = requests.get(geo_url)
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
def geo_download_dataset(details: dict, download_dir: str):
    """download datasets in geo database according to the data accession number"""
    head = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
    base_download_url = f"https://www.ncbi.nlm.nih.gov"

    data_local_paths = dict()

    for accession_number in details:
        if "Supplementary file" in details[accession_number]:
            data_local_paths[accession_number] = list()
            print(f"start download data {accession_number}")
            for file in details[accession_number]["Supplementary file"]:
                file_name = file["file_name"]
                download_link = file["download_link"]

                response = requests.get(base_download_url + file["download_link"], headers=head)

                print(f"Download data file {file_name} from link {base_download_url + download_link}")
                print(response.status_code)

                if response.status_code == 200:
                    workdir_filename = "data/" + file["file_name"]
                    filename = download_dir + "/" + workdir_filename
                    if not os.path.exists(filename):
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                    print(f"Download data file {file_name} in {accession_number} to {filename}\n\n")

                    data_local_paths[accession_number].append(workdir_filename)
                else:
                    print(f"Failed to download data for {file_name} in {accession_number}\n\n")

    return data_local_paths


def get_sample_details_and_dowload_links(sample_accession_number, sample_link):
    base_url = "https://www.ncbi.nlm.nih.gov"

    geo_sample_url = base_url + sample_link

    response = requests.get(geo_sample_url)
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


