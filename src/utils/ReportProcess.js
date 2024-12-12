
let pages=["cancers-15-03360","1-s2.0-S104366182200408X-main","41467_2024_Article_52067"];
export function GetPdfName(index) {
    return pages[index];
}
   //获得文献前缀

export function GetReport(index){
    let FileName=GetPdfName(index);   
    let Reportjson=require(`../data/reports/${FileName}_report.json`);
    let jsonString =JSON.stringify(Reportjson);
    jsonString = jsonString.replace(/\\"/g, '"').replace(/\\n/g, "").replace(/\\\u/g, " ");
    jsonString = jsonString.replace(/\\/g, "").replace(/\"{/g, "{").replace(/\}"/g, "}");                  
    let Reportjson2= JSON.parse(jsonString);
    return Reportjson2;
}

export function GetAnalysis(index){
    let FileName=GetPdfName(index);
    let Analysisjson=require(`../data/reports/${FileName}_analysis.json`);
    return Analysisjson;
}
