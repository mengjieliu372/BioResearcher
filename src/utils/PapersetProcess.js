import RetrievedPapers from '../data/papers/retrieved_papers_info.json';

export function classifyPapersByQuery(retrievedPapers) {
  const queries = ['query1', 'query2', 'query3', 'query4', 'query5'];
  const classifiedData = [];


  queries.forEach(query => {
    classifiedData.push({
      query,
      papers: []
    });
  });


  retrievedPapers.forEach((paper, index) => {
    const queryIndex = index % queries.length;
    const cleanTitle = paper.title.replace(/<[^>]*>/g, '');
    const cleanedPaper = { ...paper, title: cleanTitle };
    classifiedData[queryIndex].papers.push(cleanedPaper);
  });

  return classifiedData;
}

const classifiedPapers = classifyPapersByQuery(RetrievedPapers);
export default classifiedPapers;
