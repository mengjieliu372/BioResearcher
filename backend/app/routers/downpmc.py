# -*- coding: utf-8 -*-
import random
import re
import sqlite3
import time
import urllib
import urllib.error
from urllib import request
from bs4 import BeautifulSoup
import os
import eventlet

def get_pmcid(pmid):
    # getinfo是用指定的PMID打开文献所在的网页html，爬取一些关键信息，返回成列表或者字典之类的
    baseurl = "https://pubmed.ncbi.nlm.nih.gov/"  # baseurl和之前的搜索页面一致
    PMID = str(pmid)
    url = baseurl + PMID
    one_data = []
    header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32"}
    request = urllib.request.Request(url, headers=header)
    html = ""
    try:
        response = urllib.request.urlopen(request)
        html = response.read()
        content = BeautifulSoup(html, "html.parser")

        findlink_abs = re.compile(r'<p>.*?([A-Za-z0-9].*[\.\?]).+<\/p>', re.S)

        heading = content.find_all('div', class_="full-view", id="full-view-heading")
        heading = str(heading)  # heading是一个包含文章大部分信息的标签
        PMCID = re.search(r'(PMC\d+)\n', heading)  # 获取PMCID用于后续的自动下载
        if PMCID == None:
            return None
        else:
            PMCID = PMCID.group(1)
            return PMCID.replace("PMC","")
    except Exception as e:
        print(e)

# https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9034016/pdf/main.pdf
def downpdf(parameter):
    #eventlet.monkey_patch()
    downpara = "pmc/articles/PMC" + parameter + "/pdf/main.pdf"
    # openurl是用于使用指定的搜索parameter进行检索，以get的方式获取pubmed的搜索结果页面，返回成html文件
    baseurl = "https://www.ncbi.nlm.nih.gov/"
    url = baseurl + downpara
    timeout_flag=0
    header={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32"}
    request=urllib.request.Request(url,headers=header)
    html=""
    # try:
    #     response=urllib.request.urlopen(request,timeout=30)
    #     html=response.read()
    #     print("%s.pdf"%parameter,"从目标站获取pdf数据成功")
    #     return html
    try:
        with eventlet.Timeout(180,True):
            response = urllib.request.urlopen(request, timeout=60)
            html = response.read()
            print("%s.pdf" % parameter, "从目标站获取pdf数据成功")
            return html
    except urllib.error.URLError as e:
        if hasattr(e, "code"):  # 判断e这个对象里面是否包含code这个属性
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
        timeout_flag=1
        return timeout_flag
    except eventlet.timeout.Timeout:
        timeout_flag=1
        print("下载目标数据超时")
        return timeout_flag
    except:
        print("%s.pdf"%parameter,"从目标站获取pdf数据失败")


def savepdf(html, PMCID, save_dir):
    # pdf = html.decode("utf-8")  # 使用Unicode8对二进制网页进行解码，直接写入文件就不需要解码了

    try:
        #name = re.sub(r'[< > / \\ | : " * ?]', ' ', name)
        # 需要注意的是文件命名中不能含有以上特殊符号，只能去除掉

        savepath = save_dir + "/" + PMCID + ".pdf"
        file = open(savepath, 'wb')
        print("open success")
        file.write(html)
        file.close()
        print("pdf文件写入成功,文件ID为 %s" % PMCID, "保存路径为%s" % (save_dir + "/"))
        return True
        ''' try:
            conn = sqlite3.connect(dbpath)
            cursor = conn.cursor()
            cursor.execute(" UPDATE %s SET savepath = ? WHERE PMCID =?" % tablename,
                           (savepath, PMCID))
            conn.commit()
            cursor.close()
            return 'success'
            print("pdf文件写入成功,文件ID为 %s"%PMCID,"地址写入到数据库pubmedsql下的table%s中成功"%tablename)
        except:
            print("pdf文件保存路径写入到数据库失败")'''
    except:
        print("pdf文件写入失败,文件ID为 %s"%PMCID,"文件写入失败,检查路径")
        return False

def downpmc(result, save_dir):
    fail_papers = []
    for item in result:
        if os.path.exists(save_dir + "/" + item[0] + ".pdf"):
            print("文章{}已存在".format(item[0]))
            continue
        retry = 0
        while retry < 3:
            print("开始下载%s.pdf"%item[0])
            #result是从数据库获取的列表元组，其中的每一项构成为PMCID,doctitle
            html=downpdf(item[0])
            if html==None:
                print("网页pdf数据不存在，自动跳过该文献 PMCID为 %s" % item[0])
            elif html == 1:
                print("30s超时,自动跳过该文献 PMCID为 %s" % item[0])
            if savepdf(html, item[0], save_dir):
                time.sleep(random.randint(0, 1))
                break
            retry += 1
        if retry == 3:
            fail_papers.append(item[0])
    #print("爬取的所有文献已经保存到%s目录下"%(save_dir+"/"))
    return fail_papers
