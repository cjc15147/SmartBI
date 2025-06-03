import request from '@/utils/request'

// 注册服务
export function registerService(data) {
    return request({
        url: '/api/auth/register',
        method: 'post',
        data: {
            userAccount: data.username,
            userPassword: data.password,
            userName: data.username, // 默认使用账号作为用户名
            userRole: 'user' // 默认角色
        }
    })
}

// 登录服务
export function loginService(data) {
    return request({
        url: '/api/auth/login',
        method: 'post',
        data: {
            userAccount: data.username,
            userPassword: data.password
        }
    })
}

// 获取当前用户信息
export const getCurrentUser = () => {
    return request.get('/api/auth/current-user')
}