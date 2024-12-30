import request from '../utils/requests';

export const getinfo = async () => {
    return request({
        url: '/api/getinfo',
        method: 'get'
    });
}

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

// 获取 search 页面信息
export const getSearchModule_paper = async (data) => {
    return request({
        url: '/api/getSearchModule_paper_back',
        method: 'get',
        data
    });
}

