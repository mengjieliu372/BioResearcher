import axios from "axios";


const request = axios.create({
    timeout: 5000,
});

// 请求拦截器
request.interceptors.request.use( config => {
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