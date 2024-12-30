
from app.routers.our_utils import *
import app.routers.Nucldotide_API as Nucldotide_API
import app.routers.GEO_API_test as GEO_API_test

# from our_utils import *
# import Nucldotide_API as Nucldotide_API
# import GEO_API_test as GEO_API_test

# from search_download import generate_query

ncbi_api = 'ca7d6c6adb62c9ad9571230ba66728f54f08'



database_describe = '''
GEO: GEO is a public functional genomics data repository supporting MIAME-compliant data submissions. Array- and sequence-based data are accepted. Tools are provided to help users query and download experiments and curated gene expression profiles.
'''
def generate_query(target, model):
    response = model_generate(prompts["database_query_generator"].format(target, database_describe), model=model)
    input_tok = response[1]
    output_tok = response[2]
    response = response[0]
    query = parser_json(response, prompts)
    input_tok += query[1]
    output_tok += query[2]
    '''print("Terms for search:")
    print(terms)'''
    return query[0], input_tok, output_tok, response

def dataset_llm_related(aim, datasets, model="gpt-4o-mini-2024-07-18") -> tuple:
    '''if len(requirements) > 0:
        requirements = "Research requirements: " + requirements'''
    results = {}
    input_tok = 0
    output_tok = 0
    record_llm_res = {}
    for db in datasets:
        results[db] = {}
        record_llm_res[db] = {}
        for did, data in datasets[db].items():
            retry_times = 0
            while retry_times < max_retry_times:
                try:
                    response = model_generate(prompts["dataset_filter"].format(aim, str(data)), model=model)
                    input_tok += response[1]
                    output_tok += response[2]
                    response = response[0]
                    usability = parser_json(response, prompts)
                    
                    record_llm_res[db][did] = {}
                    record_llm_res[db][did][retry_times] = {
                        "input": prompts["dataset_filter"].format(aim, str(data)),
                        "full_llm_res": response,
                        "usability": usability
                    }

                    input_tok += usability[1]
                    output_tok += usability[2]
                    usability = usability[0]["usability"]
                    #score = eval(re.findall(r'\[(.*?)\]', response)[-1].lower().replace("/5", "").replace("score: ", ""))
                    if usability.lower() == "yes":
                        print("dataset \"{}\" in {} is useful to research!".format(did, db), flush=True)
                        #data["score"] = score
                        results[db][did] = data
                        break
                    else:
                        print("dataset \"{}\" in {} isn't useful to research!".format(did, db), flush=True)
                        break
                except Exception as e:
                    retry_times += 1

    return results, input_tok, output_tok, record_llm_res

def search_datasets(objective, model, save_path, retmax=2):
    details = dict()
    input_tokens = 0
    output_tokens = 0
    times = 0
    all_datasets = {"GEO": {}}
    all_useful = {}
    all_queries = []
    queries = {}
    full_llm_res_record = dict()
    while(times < retmax):
        query = generate_query(objective, model)
        input_tokens += query[1]
        output_tokens += query[2]
        full_llm_res = query[3]
        full_llm_res_record[times] = {}
        full_llm_res_record[times]["search"] = {
            "full_llm_res": full_llm_res,
            "search_query": query[0]
        }
        query = query[0]
        queries["GEO"] = [i for i in query["GEO"] if i not in all_queries]
        all_queries.extend(queries["GEO"])
        details["GEO"] = GEO_API_test.search_details(queries["GEO"])
    # details = select_attr(details)    # 获取的 details 已经是过滤后的
        dup = []
        for k in details["GEO"].keys():
            if k in all_datasets["GEO"].keys():
                dup.append(k)
        for k in dup:
            del details["GEO"][k]
        all_datasets["GEO"].update(details["GEO"])
        useful_details = dataset_llm_related(objective, details, model)
        input_tokens += useful_details[1]
        output_tokens += useful_details[2]
        record_llm_check4related_res = useful_details[3]
        full_llm_res_record[times]["filter"] = record_llm_check4related_res
        useful_details = useful_details[0]
        all_useful.update(useful_details["GEO"])
        if len(all_useful) >= 3:
            break
        times += 1
    useful_details['input_tokens'] = input_tokens
    useful_details['output_tokens'] = output_tokens
    write_json(all_useful, save_path)
    return queries, all_datasets, input_tokens, output_tokens, full_llm_res_record

def search_datasets_with_query(objective, queries, model, save_path):
    details = dict()
    input_tokens = 0
    output_tokens = 0
    retry = 0
    while retry < max_retry_times:
        try:
            #details["Nucleotide"] = Nucldotide_API.search_details(queries["Nucleotide"])
            details["GEO"] = GEO_API_test.search_details(queries)
            break
        except Exception as e:
            retry += 1
            print(f"datasets search failed {retry}: {e}")
    if retry == max_retry_times:
        print("Error: dataset search failed over 3 times!")
    # details = select_attr(details)    # 获取的 details 已经是过滤后的
    useful_details = dataset_llm_related(objective, details)
    input_tokens += useful_details[1]
    output_tokens += useful_details[2]
    useful_details = useful_details[0]
    useful_details['input_tokens'] = input_tokens
    useful_details['output_tokens'] = output_tokens
    write_json(useful_details, save_path)
    return queries, details, input_tokens, output_tokens

def generate_query2(objective, context, model):
    response = model_generate(prompts["database_query_generator2"].format(database_describe, objective, context))
    input_tok = response[1]
    output_tok = response[2]
    response = response[0]
    query = parser_json(response, prompts)
    input_tok += query[1]
    output_tok += query[2]
    '''print("Terms for search:")
    print(terms)'''
    return query[0], input_tok, output_tok

def dataset_llm_related2(datasets_details, objective, context, model) -> tuple:
    '''if len(requirements) > 0:
        requirements = "Research requirements: " + requirements'''
    history = dict()
    results = {}
    input_tok = 0
    output_tok = 0
    for db in datasets_details:
        history[db] = {}
        results[db] = {}
        for did, data in datasets_details[db].items():
            retry_times = 0
            while retry_times < max_retry_times:
                try:
                    response = model_generate(prompts["dataset_filter2"].format(did + ": " + str(data), objective, context), temperature=0.1)
                    input_tok += response[1]
                    output_tok += response[2]
                    response = response[0]
                    history[db][did] = {
                        "input for LLM": prompts["dataset_filter2"].format(str(data), objective, context),
                        "output for LLM": response
                    }

                    usability = parser_json(response, prompts)

                    input_tok += usability[1]
                    output_tok += usability[2]
                    usability = usability[0]["usability"]
                    #score = eval(re.findall(r'\[(.*?)\]', response)[-1].lower().replace("/5", "").replace("score: ", ""))
                    if usability.lower() == "yes":
                        print("dataset \"{}\" in {} is useful to research!".format(did, db), flush=True)
                        #data["score"] = score
                        results[db][did] = data
                        break
                    else:
                        print("dataset \"{}\" in {} isn't useful to research!".format(did, db), flush=True)
                        break
                except Exception as e:
                    print(f"dataset_llm_related2 error for {db} {did}", e)
                    retry_times += 1

    return results, input_tok, output_tok, history


def search_datasets2(objective, context, model, save_path):
    details = dict()
    input_tokens = 0
    output_tokens = 0
    query = generate_query2(objective, context, model)
    input_tokens += query[1]
    output_tokens += query[2]
    queries = query[0]
    retry = 0
    while retry < max_retry_times:
        try:
            #details["Nucleotide"] = Nucldotide_API.search_details(queries["Nucleotide"])
            details["GEO"] = GEO_API_test.search_details(queries["GEO"])
            break
        except Exception as e:
            print(f"search_datasets2 error: ", e)
            retry += 1
            if retry == max_retry_times:
                raise Exception(f"dataset search failed. {e}")

    details['input_tokens'] = input_tokens
    details['output_tokens'] = output_tokens
    write_json(details, save_path)
    return details, input_tokens, output_tokens, queries

def search_datasets_ids(ids):
    # 输入是 geo accession numbers 
    dataset = dict()
    retry = 0
    while retry < max_retry_times:
        try:
            for accession_number in ids:
                dataset[accession_number] = GEO_API_test.get_details_and_download_links(accession_number)
            break
        except Exception as e:
            print(f"search_datasets_id error: ", e, flush=True)
            print(f"error of geo data {accession_number}")
            retry += 1
            if retry == max_retry_times:
                raise Exception(f"dataset search failed. {e}")
    return dataset


def select_attr(datasets):
    """ 检索得到的数据集描述过长，有一些不必要的信息，需要选择关键信息给大模型 """
    datasets_details = dict()
    if "Nucleotide" in datasets:
        attr_selected = ["title", "createdate", "updatedate", "biomol", "moltype", "topology", "sourcedb", "genome", "subtype", "subname", "organism", "biosample"]
        datasets_details["Nucleotide"] = dict()
        for did in datasets["Nucleotide"]:
            datasets_details["Nucleotide"][did] = dict()
            for attr in attr_selected:
                if attr in datasets["Nucleotide"][did]:
                    datasets_details["Nucleotide"][did][attr] = datasets["Nucleotide"][did][attr]

    if "GEO" in datasets:
        attr_selected = ["title", "summary", "taxon", "entrytype", "gdstype", "pdat", "suppfile", "geo2r", "bioproject"]
        datasets_details["GEO"] = dict()
        for did in datasets["GEO"]:
            datasets_details["GEO"][did] = dict()
            for attr in attr_selected:
                if attr in datasets["GEO"][did]:
                    datasets_details["GEO"][did][attr] = datasets["GEO"][did][attr]

    return datasets_details




#target = '''Identify populations that are sensitive to immunotherapy for liposarcoma and explore the mechanisms of therapeutic sensitivity to guide the treatment of those whose immune quality is not sensitive.'''
#context = '''"Title": "Transcriptomic Data Integration (TCGA, GEO, and In-House Data)",
#                "Outline": "This part focuses on integrating and analyzing existing transcriptomic data from TCGA, GEO, and in-house datasets for immunophenotyping of liposarcoma. Detailed steps will be provided for data normalization using DESeq2 and edgeR, quality control, and merging datasets. The protocols will emphasize statistical rigor, reproducibility, and provide examples to enhance clarity. Methods for addressing potential variability and ensuring robust data integration will be included."'''
'''print(generate_query(target, "gpt-4o")[0])

print(generate_query2(target, context, "gpt-4o")[0])'''
