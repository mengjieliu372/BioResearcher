import requests
import xml.etree.ElementTree as ET
from typing_extensions import Annotated
from app.models.downpmc import *
from app.models.our_utils import *

# from downpmc import *
# from our_utils import *

import os
ncbi_api = 'ca7d6c6adb62c9ad9571230ba66728f54f08'


filter_prompt = prompts["filter"]
query_generator_prompt = prompts["query_generator"]


head = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}  #，防止HTTP403错误
def download_pdf(doi_list, save_dir):
    fail_papers = []
    # 使用sci-hub下载
    for doi in doi_list:
        if os.path.exists(save_dir + "/" + doi.replace("/", "_") + ".pdf"):
            print("文章{}已存在".format(doi),flush=True)
            continue
        # 拼接网址
        #url = "https://www.sci-hub.pl/" + line + "#"  #sci hub的DOI码检索url  这个地址已经失效了
        url = "https://www.sci-hub.ren/" + doi + "#"  #
        url = 'https://www.et-fine.com/' + doi + '#'
        # url = "https://www.sci-hub.st/" + doi + "#"
        retry = 0
        while retry < 3:
            try:
                download_url = ""
                # 请求文件位置
                r = requests.get(url, headers=head)
                r.raise_for_status()
                r.encoding = r.apparent_encoding
                # 解析
                soup = BeautifulSoup(r.text, "html.parser")
                # download_url = "https:" + str(soup.div.ul.find(href="#")).split("href='")[-1].split(".pdf")[0] + ".pdf" #寻找出存放该文献的pdf资源地址（该检索已失效）
                if soup.iframe == None:
                    download_url = "https:" + soup.embed.attrs["src"]
                else:
                    download_url = soup.iframe.attrs["src"]  #
                print(doi + " is downloading...\n  --The download url is: " +
                      download_url, flush=True)
                download_r = requests.get(download_url, headers=head)
                download_r.raise_for_status()
                # 保存文件
                with open(save_dir + "/" + doi.replace("/", "_") + ".pdf", "wb+") as temp:
                    temp.write(download_r.content)
                    print(doi + " download successfully.\n",flush=True)
                    break
            except:
                retry += 1
        if retry == 3:
            print(doi + " occurs error!\n",flush=True)
            fail_papers.append(doi)
    return fail_papers


def llm_related(aim: Annotated[str, "The research aim."], conditions: Annotated[str, "The research conditions."], requirements: Annotated[str, "Hard requirements to be implemented in experimental design."], papers_list: Annotated[list, "A list of papers with their titles and abstract."], model) -> tuple:
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
                score = eval(re.findall(r'\[(.*?)\]', response)[-1].lower().replace("/5", "").replace("score: ", ""))
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

def generate_query(target, conditions, requirements, model):
    response = model_generate(query_generator_prompt.format(target, conditions, requirements), model=model)
    input_tok = response[1]
    output_tok = response[2]
    response = response[0]
    terms = re.findall('\[(.*)\]',response)
    '''print("Terms for search:")
    print(terms)'''
    return terms, input_tok, output_tok, response

def parse_pubmed(root):
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
        pubmed_papers.append({"title":title, "abstract": abstract, "doi":doi, "pmid":pmid, "pmcid":pmcid})
        #get_pdf_link(doi)
    return pubmed_papers
    #download_pdf(data["doi"])


def parse_pmc(root):
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

        pmc_papers.append({"title":title, "abstract": abstract, "doi":doi, "pmid":pmid, "pmcid":pmcid})
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

            # 解析图例
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
    # 定义NCBI Entrez Programming Utilities的URL
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    #retmax = 5  # 要返回的文献数量
    data = []
    database = ['pubmed', 'pmc']
    if isinstance(queries, str):
        queries = [queries]
    for db in database:
        print("Database: ", db, flush=True)
        for term in queries:
            print("Searching for {}...".format(term), flush=True)
            # 构造ESearch请求
            params = {
                'db': db,
                'term': term,
                'usehistory': 'y',
                'api_key': ncbi_api,
                'sort': 'pub_date'
            }
            response = requests.get(base_url + 'esearch.fcgi', params=params)

            # 解析ESearch响应以获取WebEnv和QueryKey
            root = ET.fromstring(response.content)
            webenv = root.find('WebEnv').text
            query_key = root.find('QueryKey').text

            # 构造EFetch请求以获取文档全文
            params = {
                'db': db,
                'query_key': query_key,
                'WebEnv': webenv,
                #'rettype': 'xml',   #full
                'retmode': 'xml',
                'retmax': str(retmax),
                'api_key': ncbi_api
            }
            response = requests.get(base_url + 'efetch.fcgi', params=params)
            # 解析EFetch响应以获取文档全文
            root = ET.fromstring(response.content)
            time.sleep(1)
            if db == "pubmed":
                data.extend(parse_pubmed(root))
            elif db == "pmc":
                data.extend(parse_pmc(root))
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
    if os.path.exists(papers_info_path):
        data = {"download successfully": success_papers, "download failed": fail_papers}
        old_data = read_json(papers_info_path)
        data.update(old_data)

    with open(papers_info_path, "w", encoding="utf-8") as out:
        data = {"download successfully": success_papers, "download failed": fail_papers}
        json.dump(data, out, indent=4, ensure_ascii=False)
    return data



def search_download(objective, conditions, requirements, model, retmax, savedir, retrieved_paper_info_path, related_paper_info_path):
    input_tokens = 0
    output_tokens = 0
    search_times = 0
    useful_papers = []
    total_papers = []
    total_queries = []
    full_res_record = {}
    while search_times < 5:
        queries = generate_query(objective, conditions, requirements, model)
        input_tokens += queries[1]
        output_tokens += queries[2]
        full_res = queries[3]
        full_res_record[search_times] = {}
        full_res_record[search_times]["search"] = {"full_llm_res": full_res, "search_queries": queries[0]}
        full_res_record[search_times]["filter"] = "LLM 过滤（判断相似性）的响应记录在那些相关 paper list 的每个 tup 里"
        queries = queries[0]
        total_queries.extend(queries)

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
        paperlist = llm_related(objective, conditions, requirements, paperlist, model)
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
    write_json(total_papers, retrieved_paper_info_path)
    '''useful_papers = sorted(useful_papers, key=lambda x:x["score"], reverse=True)
    data = download_paper(useful_papers, savedir, related_paper_info_path)
    if len(data["download successfully"]) >= 10:'''

    flag = True
    if len(data["download failed"]) > 0:
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
    paperlist = llm_related(objective, conditions, requirements, paperlist, model)
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



