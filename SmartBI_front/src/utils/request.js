import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const service = axios.create({
    baseURL: 'http://localhost:3000', // API 的基础URL
    timeout: 5000 // 请求超时时间
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        // 从 localStorage 获取 token
        const token = localStorage.getItem('token')
        if (token) {
            // 让每个请求携带token
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    error => {
        console.log(error)
        return Promise.reject(error)
    }
)

// 响应拦截器
service.interceptors.response.use(
    response => {
        const res = response.data
        console.log('API响应数据:', res)
        
        // 处理不同的响应格式
        if (res.code === 1) {
            // 直接返回完整响应
            return res
        } else if (res.success === true) {
            // 如果响应格式是 {success: true, data: [...], message: string}
            return {
                data: res.data,
                message: res.message
            }
        } else {
            ElMessage({
                message: res.message || '请求失败',
                type: 'error',
                duration: 5 * 1000
            })
            return Promise.reject(new Error(res.message || '请求失败'))
        }
    },
    error => {
        console.log('请求错误详情:', error.response || error)
        if (error.response?.status === 401) {
            ElMessage({
                message: '登录已过期，请重新登录',
                type: 'error',
                duration: 5 * 1000
            })
            localStorage.removeItem('token')
            router.push('/login')
        } else {
            ElMessage({
                message: error.response?.data?.message || error.message || '请求失败',
                type: 'error',
                duration: 5 * 1000
            })
        }
        return Promise.reject(error)
    }
)

export default service 