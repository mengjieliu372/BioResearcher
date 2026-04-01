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

// 获取某个项目信息
export const getProject = async (id) => {
    return request({
        url: `/api/${id}/experiment`,
        method: 'get',
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

// 获取已完成步骤
export const getCompletedSteps = async (id) => {
    return request({
        url: `/api/${id}/process`,
        method: 'get',
    });
}

export const resumeExperiment = async (id) => {
    return request({
        url: `/api/${id}/resume`,
        method: 'post',
    });
}

export const pauseExperiment = async (id) => {
    return request({
        url: `/api/${id}/pause`,
        method: 'post',
    });
}


// Search
export const getPapersets = async (id) => {
    return request({
        url: `/api/${id}/papersets`,
        method: 'get',
    });
}

export const uploadManualPaperPdf = async (id, data) => {
    return request({
        url: `/api/${id}/papers/upload-manual`,
        method: 'post',
        data,
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

export const getProgramMeta = async (id) => {
    return request({
        url: `/api/${id}/program/meta`,
        method: 'get',
    });
}

export const downloadProgramDataZip = async (id) => {
    return request({
        url: `/api/${id}/program/download-data-zip`,
        method: 'get',
        responseType: 'blob',
        timeout: 0,
    });
}

export const regenerateProgram = async (id) => {
    return request({
        url: `/api/${id}/program/regenerate`,
        method: 'post',
    });
}

export const regenerateProgramWithFeedback = async (id, feedback) => {
    return request({
        url: `/api/${id}/program/regenerate-with-feedback`,
        method: 'post',
        data: { feedback },
    });
}

// auth
export const authRegister = async (data) => {
    return request({
        url: '/api/auth/register',
        method: 'post',
        data,
    });
}

export const authLogin = async (data) => {
    return request({
        url: '/api/auth/login',
        method: 'post',
        data,
    });
}

export const authMe = async () => {
    return request({
        url: '/api/auth/me',
        method: 'get',
    });
}

export const authLogout = async () => {
    return request({
        url: '/api/auth/logout',
        method: 'post',
    });
}
