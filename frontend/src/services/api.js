import request from '../utils/requests';

// 上传新创建的项目信息
export const addProject = async (data) => {
    return request({
        url: '/api/addExperiment',
        method: 'post',
        data
    });
}

// 获取项目列表
export const getProjects = async () => {
    return request({
        url: '/api/getExperiments',
        method: 'get'
    });
}

// 更新项目信息
export const updateProject = async (data) => {
    return request({
        url: '/api/updateExperiment',
        method: 'put',
        data
    });
}

// 删除项目
export const deleteProject = async (id) => {
    return request({
        url: '/api/deleteExperiment',
        method: 'delete',
        params: { id }
    });
}

// 上传文件
export const uploadFile = async (data) => {
    return request({
        url: '/api/uploadfile',
        method: 'post',
        data
    });
}

// 根据文件名删除文件
export const deleteFile = async (fileName) => {
    return request({
        url: '/api/deletefile',
        method: 'delete',
        params: { file_name: fileName }
    });
}


// Search
export const getPapersets = async (id) => {
    return request({
        url: `/api/${id}/papersets`,
        method: 'get',
    });
}

export const getDatasets = async (id) => {
    return request({
        url: `/api/${id}/datasets`,
        method: 'get',
    });
}

// Literature Processing
export const getPaperInfo = async (id) => {
    return request({
        url: `/api/${id}/paperinfo`,
        method: 'get',
    });
}

export const getReportAnalysis = async (id, index) => {
    return request({
        url: `/api/${id}/paper-report-analysis`,
        method: 'get',
        params: { index }
    });
}


// Experimental Design
export const getExpDesign = async (id, value) => {
    return request({
        url: `/api/${id}/expdesign`,
        method: 'get',
        params: { value }
    });
}

// Dry Experiment
export const getDryExp = async (id, value) => {
    return request({
        url: `/api/${id}/dryexp`,
        method: 'get',
        params: { value }
    });
}

// program
export const getProgram = async (id, value) => {
    return request({
        url: `/api/${id}/program`,
        method: 'get',
        params: { value }
    });
}
