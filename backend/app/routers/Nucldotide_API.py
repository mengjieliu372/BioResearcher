import requests
import os
import json
import logging
import ftplib
import gzip
from requests.exceptions import ChunkedEncodingError, ConnectionError, RequestException, Timeout

# from autogen.coding.func_with_reqs import Alias, ImportFromModule, with_requirements
# from autogen.coding import CodeBlock, LocalCommandLineCodeExecutor



def fetch_dataset_information(query, max_records):
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
    retmax = 5
    retstart = 0
    all_summaries = dict()

    print(f"\nSearch {query} in Nucldotide:")
    while retstart < max_records:
        print(f"Starting batch search with retstart={retstart} and retmax={retmax}")

        # Step 1: ESearch 获取 UID 列表
        search_params = {
            "db": "nuccore",
            "term": query,
            "retmax": retmax,
            "retstart": retstart,
            "retmode": "json"
        }
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        uids = search_data["esearchresult"]["idlist"]
        print(f"ESearch retrieved {len(uids)} UIDs: {uids}")

        if not uids:
            print("No more UIDs found, exiting loop.")
            break

        # Step 2: ESummary 获取描述信息
        summary_params = {
            "db": "nuccore",
            "id": ",".join(uids),
            "retmode": "json"
        }
        summary_response = requests.get(summary_url, params=summary_params)
        summary_data = summary_response.json()
        for uid in uids:
            all_summaries[uid] = summary_data["result"][uid]

        print(f"ESummary retrieved summaries for UIDs: {uids}")

        retstart += retmax

    print(f"Summary information returned, Nucldotide search over!\n")

    return uids, all_summaries



def search_details(queries):
    # search datasets id and details in Nucldotide
    result = dict()

    for q in queries:
        data_ids, details = fetch_dataset_information(q, 5)
        if len(data_ids) > 0:
            # print(json.dumps({"data ids": data_ids, "details": details}, ensure_ascii=False, indent=4), '\n\n')

            result.update(details)

    return result



# @with_requirements(python_packages=["os", "requests"], global_imports=["os", "requests"])
def GenBank_download_data(uid: str, output_dir: str):
    """download dataset in Nucldotide database according to the data uid"""
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    workdir_filename = f"data/{uid}-genbank_full_sequences.gb"

    genbank_file_path = os.path.join(output_dir, workdir_filename)
    if os.path.exists(genbank_file_path):
        return [workdir_filename]

    all_genbank_data = ""

    print("\nGenBank download start!")
    # EFetch acquire squenence data with format GenBank (full)
    fetch_params = {
        "db": "nuccore",
        "id": uid,
        "rettype": "gbwithparts",
        "retmode": "text"
    }

    max_timeout = 300
    fetch_response = requests.get(fetch_url, params=fetch_params, stream=True, timeout=max_timeout)
    fetch_response.raise_for_status()
    for chunk in fetch_response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            all_genbank_data += chunk.decode("utf-8")
    print(f"EFetch request successful. Retrieved {len(all_genbank_data)} bytes of GenBank data.")

    # save GenBank (full) squenence data
    if all_genbank_data:
        with open(genbank_file_path, "w") as genbank_file:
            genbank_file.write(all_genbank_data)
        print(f"GenBank full sequences saved to {genbank_file_path}, download is over!\n")
        return [workdir_filename]
    else:
        print(f"Failed to download GenBank full sequences to {genbank_file_path}")
        return None


