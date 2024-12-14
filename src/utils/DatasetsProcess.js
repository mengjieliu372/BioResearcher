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
            const isRelated = downloadedDataset.includes(dataset);
            const cleanedDataset = { ...info, isRelated };
            classifiedData[queryIndex].datasets[dataset] = cleanedDataset;
        });
    });

    // 按照isRelated排序，true在前
    classifiedData.forEach(query => {
        query.datasets = Object.fromEntries(Object.entries(query.datasets).sort((a, b) => {
            if (a[1].isRelated === b[1].isRelated) {
                return 0;
            } else if (a[1].isRelated) {
                return -1;
            } else {
                return 1;
            }
        }));
    });
    return classifiedData;
}

const classifiedDatasets = classifyDatasetsByQuery(RetrievedDatasets);

export default classifiedDatasets;
