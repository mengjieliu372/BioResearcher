import RetrievedPapers from '../data/papers/retrieved_papers_info.json';
import RelatedPapers from '../data/papers/related_papers_info.json';

export function classifyPapersByQuery(retrievedPapers) {
  const queries = ['query1', 'query2', 'query3', 'query4', 'query5'];
  const classifiedData = [];

  queries.forEach(query => {
    classifiedData.push({
      query,
      papers: []
    });
  });

  const downloadedTitles = new Set(
    RelatedPapers["download successfully"].map(item => item.title)
  );

  const undownloadedTitles = new Set(
    RelatedPapers["download failed"].map(item => item.title)
  );

  retrievedPapers.forEach((paper, index) => {
    const queryIndex = index % queries.length;
    let flag = 1;
    if (downloadedTitles.has(paper.title)) {
      flag = 3;
    }
    if (undownloadedTitles.has(paper.title)) {
      flag = 2;
    }
    const cleanTitle = paper.title.replace(/<[^>]*>/g, '');
    const cleanAbstract = paper.abstract.replace(/<[^>]*>/g, '');
    const cleanedPaper = { ...paper, title: cleanTitle, abstract: cleanAbstract, flag };
    classifiedData[queryIndex].papers.push(cleanedPaper);
  });
  // 按照flag从大到小排序
  classifiedData.forEach((query) => {
    query.papers.sort((a, b) => b.flag - a.flag);
  });
  return classifiedData;
}

const classifiedPapers = classifyPapersByQuery(RetrievedPapers);
export default classifiedPapers;
