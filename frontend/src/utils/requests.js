import axios from "axios";
import { getAuthToken } from "./auth";


const request = axios.create({
    timeout: 5000,
});

// 请求拦截器
request.interceptors.request.use( config => {
    const token = getAuthToken();
    if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => {
    return Promise.reject(error);
});


// 响应拦截器
request.interceptors.response.use( response => {
    return response;
}, error => {
    return Promise.reject(error);
});

export default request;
