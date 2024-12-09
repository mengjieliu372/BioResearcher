import RetrievedDatasets from '../data/datasets/retrieved_datasets_info.json';


export function classifyDatasetsByQuery(retrievedDatasets) {
    const queries = ['query1', 'query2', 'query3', 'query4', 'query5'];
    const classifiedData = [];

    queries.forEach(query => {
        classifiedData.push({
            query,
            datasets: []
        });
    });

    RetrievedDatasets["GEO"].forEach((dataset, index) => {
        const queryIndex = index % queries.length;
        classifiedData[queryIndex].datasets.push(dataset);
    });
    return classifiedData;
}

const classifiedDatasets = classifyDatasetsByQuery(RetrievedDatasets);

export default classifiedDatasets;
