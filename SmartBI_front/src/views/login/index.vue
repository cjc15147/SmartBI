<script setup>
import { User, Lock } from '@element-plus/icons-vue'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { registerService, loginService } from '@/api/user.js'
import { useRouter } from 'vue-router'

const router = useRouter()

// 控制注册与登录表单的显示，默认显示登录
const isRegister = ref(false)

// 用于注册的数据模型
const registerData = ref({
    username: '',
    password: '',
    rePassword: ''
})

// 用于登录的数据模型
const loginData = ref({
    username: '',
    password: ''
})

// 表单引用
const registerFormRef = ref(null)
const loginFormRef = ref(null)

// 清空注册表单数据
const clearRegisterData = () => {
    registerData.value = {
        username: '',
        password: '',
        rePassword: ''
    }
}

// 清空登录表单数据
const clearLoginData = () => {
    loginData.value = {
        username: '',
        password: ''
    }
}

// 自定义确认密码的校验函数
const rePasswordValid = (rule, value, callback) => {
    if (value === '') {
        callback(new Error('请再次确认密码'))
    } else if (value !== registerData.value.password) {
        callback(new Error('两次输入密码不一致'))
    } else {
        callback()
    }
}

// 注册表单校验规则
const registerDataRules = {
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 5, max: 16, message: '用户名的长度必须为5~16位', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 5, max: 16, message: '密码长度必须为5~16位', trigger: 'blur' }
    ],
    rePassword: [
        { validator: rePasswordValid, trigger: 'blur' }
    ]
}

// 登录表单校验规则
const loginDataRules = {
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
    ]
}

// 注册按钮点击事件
const registerUser = async () => {
    try {
        const result = await registerService(registerData.value)
        if (result.code === 1) {
            ElMessage.success(result.message || '注册成功!')
            isRegister.value = false // 注册成功后切换到登录页面
            clearRegisterData() // 清空注册表单
        } else {
            ElMessage.error(result.message || '注册失败!')
        }
    } catch (error) {
        ElMessage.error('注册失败，请稍后重试')
    }
}

const register = () => {
    if (!registerFormRef.value) return
    registerFormRef.value.validate((valid) => {
        if (valid) {
            registerUser()
        }
    })
}

// 登录按钮点击事件
const loginUser = async () => {
    try {
        console.log('开始登录请求...')
        const result = await loginService(loginData.value)
        console.log('登录响应:', result)
        
        if (result.code === 1 && result.token) {
            const token = result.token
            console.log('获取到token:', token)
            localStorage.setItem('token', token)
            
            const storedToken = localStorage.getItem('token')
            console.log('存储后的token:', storedToken)
            
            if (storedToken === token) {
                ElMessage.success(result.msg || '登录成功!')
                console.log('准备跳转到首页...')
                try {
                    await router.push('/')
                    console.log('路由跳转完成')
                } catch (routerError) {
                    console.error('路由跳转失败:', routerError)
                }
            } else {
                console.error('Token存储验证失败')
                ElMessage.error('Token存储失败，请重试')
            }
        } else {
            console.error('登录响应格式错误:', result)
            ElMessage.error(result.msg || '登录失败!')
        }
    } catch (error) {
        console.error('登录过程发生错误:', error)
        ElMessage.error('登录失败，请稍后重试')
    }
}

const login = () => {
    if (!loginFormRef.value) return
    loginFormRef.value.validate((valid) => {
        if (valid) {
            loginUser()
        }
    })
}
</script>

<template>
    <el-row class="login-page">
        <el-col :span="12" class="bg"></el-col>
        <el-col :span="6" :offset="3" class="form">
            <!-- 注册表单 -->
            <el-form 
                ref="registerFormRef" 
                size="large" 
                autocomplete="off" 
                v-if="isRegister" 
                :model="registerData"
                :rules="registerDataRules"
            >
                <el-form-item>
                    <h1>注册</h1>
                </el-form-item>
                <el-form-item prop="username">
                    <el-input 
                        :prefix-icon="User" 
                        placeholder="请输入用户名" 
                        v-model="registerData.username"
                    ></el-input>
                </el-form-item>
                <el-form-item prop="password">
                    <el-input 
                        :prefix-icon="Lock" 
                        type="password" 
                        placeholder="请输入密码" 
                        v-model="registerData.password"
                    ></el-input>
                </el-form-item>
                <el-form-item prop="rePassword">
                    <el-input 
                        :prefix-icon="Lock" 
                        type="password" 
                        placeholder="请再次输入密码" 
                        v-model="registerData.rePassword"
                    ></el-input>
                </el-form-item>
                <el-form-item>
                    <el-button class="button" type="primary" @click="register">
                        注册
                    </el-button>
                </el-form-item>
                <el-form-item class="flex">
                    <el-link type="info" :underline="false" @click="isRegister = false; clearRegisterData()">
                        ← 返回登录
                    </el-link>
                </el-form-item>
            </el-form>

            <!-- 登录表单 -->
            <el-form 
                ref="loginFormRef" 
                size="large" 
                autocomplete="off" 
                v-else
                :model="loginData"
                :rules="loginDataRules"
            >
                <el-form-item>
                    <h1>登录</h1>
                </el-form-item>
                <el-form-item prop="username">
                    <el-input 
                        :prefix-icon="User" 
                        placeholder="请输入用户名"
                        v-model="loginData.username"
                    ></el-input>
                </el-form-item>
                <el-form-item prop="password">
                    <el-input 
                        :prefix-icon="Lock" 
                        type="password" 
                        placeholder="请输入密码"
                        v-model="loginData.password"
                    ></el-input>
                </el-form-item>
                <el-form-item class="flex">
                    <div class="flex">
                        <el-checkbox>记住我</el-checkbox>
                        <el-link type="primary" :underline="false">忘记密码？</el-link>
                    </div>
                </el-form-item>
                <el-form-item>
                    <el-button class="button" type="primary" auto-insert-space @click="login">
                        登录
                    </el-button>
                </el-form-item>
                <el-form-item class="flex">
                    <el-link type="info" :underline="false" @click="isRegister = true; clearLoginData()">
                        注册账号 →
                    </el-link>
                </el-form-item>
            </el-form>
        </el-col>
    </el-row>
</template>

<style lang="scss" scoped>
.login-page {
    height: 100vh;
    background-color: #fff;

    .bg {
        background: url('@/assets/logo2.png') no-repeat 60% center / 240px auto,
            url('@/assets/login_bg.jpg') no-repeat center / cover;
        border-radius: 0 20px 20px 0;
    }

    .form {
        display: flex;
        flex-direction: column;
        justify-content: center;
        user-select: none;

        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }

        .button {
            width: 100%;
        }

        .flex {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    }
}
</style> 