import RetrievedDatasets from '../data/dataset/retrieved_datasets_info.json';
import RelatedDatasets from '../data/dataset/related_datasets_info.json';

export function classifyDatasetsByQuery(retrievedDatasets) {
    const queries = ['query1', 'query2', 'query3', 'query4', 'query5'];
    const classifiedData = [];

    queries.forEach(query => {
        classifiedData.push({
            query,
            datasets: {}
        });
    });

    const downloadedDataset = Object.keys(RelatedDatasets);
    
    Object.entries(retrievedDatasets).map(([category, datasets]) => {
        let innerIndex = 0; 
        Object.entries(datasets).map(([dataset, info]) => {
            const queryIndex = innerIndex % queries.length;
            innerIndex++;
            const isDownload = downloadedDataset.includes(dataset);
            const cleanedDataset = { ...info, isDownload };
            classifiedData[queryIndex].datasets[dataset] = cleanedDataset;
        });
    });

    return classifiedData;
}

const classifiedDatasets = classifyDatasetsByQuery(RetrievedDatasets);

export default classifiedDatasets;
