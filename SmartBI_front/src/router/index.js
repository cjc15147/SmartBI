import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/home/index.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'analysis/overview',
        name: 'AnalysisOverview',
        component: () => import('@/views/analysis/overview.vue'),
        meta: { title: '机房报价稽核' }
      },
      {
        path: 'analysis/detail',
        name: 'AnalysisDetail',
        component: () => import('@/views/analysis/detail.vue'),
        meta: { title: '智能数据分析' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  console.log('路由守卫触发 - 目标路由:', to.path)
  const token = localStorage.getItem('token')
  console.log('当前token状态:', token ? '已存在' : '不存在')
  
  if (to.meta.requiresAuth) {
    console.log('目标路由需要认证')
    if (!token) {
      console.log('未登录，重定向到登录页')
      ElMessage.warning('请先登录')
      next('/login')
    } else {
      console.log('已登录，允许访问')
      next()
    }
  } else {
    console.log('目标路由不需要认证')
    if (token && to.path === '/login') {
      console.log('已登录用户访问登录页，重定向到首页')
      next('/')
    } else {
      console.log('允许访问')
      next()
    }
  }
})

export default router
