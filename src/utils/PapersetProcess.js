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

  retrievedPapers.forEach((paper, index) => {
    const queryIndex = index % queries.length;
    const isDownload = downloadedTitles.has(paper.title);
    const cleanTitle = paper.title.replace(/<[^>]*>/g, '');
    const cleanAbstract = paper.abstract.replace(/<[^>]*>/g, '');
    const cleanedPaper = { ...paper, title: cleanTitle, abstract: cleanAbstract, isDownload };
    classifiedData[queryIndex].papers.push(cleanedPaper);
  });

  return classifiedData;
}

const classifiedPapers = classifyPapersByQuery(RetrievedPapers);
export default classifiedPapers;
