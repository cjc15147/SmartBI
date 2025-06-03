<template>
  <div class="home-container">
    <el-row :gutter="20" class="main-row">
      <!-- 左上区域：存量机房数据 -->
      <el-col :span="12" class="data-section">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>存量机房数据</span>
              <el-upload
                class="upload-demo"
                action="/api/data/upload/existing"
                :on-success="handleExistingUploadSuccess"
                :on-error="handleUploadError"
                :before-upload="beforeUpload"
                accept=".xlsx,.csv"
              >
                <el-button type="primary">上传存量数据</el-button>
              </el-upload>
            </div>
          </template>
          <div class="table-container">
            <el-table 
              :data="existingData" 
              style="width: 100%" 
              v-loading="existingLoading"
              height="calc(100vh - 250px)"
            >
              <el-table-column prop="report_name" label="报账点名称" />
              <el-table-column prop="contract_code" label="合同编码" />
              <el-table-column prop="contract_name" label="合同名称" />
              <el-table-column prop="contract_start" label="合同期始" />
              <el-table-column prop="contract_end" label="合同期终" />
              <el-table-column prop="annual_rent" label="合同年租金" />
              <el-table-column prop="total_rent" label="合同总金额" />
              <el-table-column prop="area" label="机房面积" />
              <el-table-column prop="longitude" label="经度" />
              <el-table-column prop="latitude" label="纬度" />
            </el-table>
          </div>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="existingCurrentPage"
              v-model:page-size="existingPageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              :total="existingTotal"
              @size-change="handleExistingSizeChange"
              @current-change="handleExistingCurrentChange"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右上区域：新增机房数据 -->
      <el-col :span="12" class="data-section">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>新增机房数据</span>
              <el-upload
                class="upload-demo"
                action="/api/data/upload/new"
                :on-success="handleNewUploadSuccess"
                :on-error="handleUploadError"
                :before-upload="beforeUpload"
                accept=".xlsx,.csv"
              >
                <el-button type="primary">上传新增数据</el-button>
              </el-upload>
            </div>
          </template>
          <el-table :data="newData" style="width: 100%" v-loading="newLoading">
            <el-table-column prop="area" label="机房面积" />
            <el-table-column prop="longitude" label="经度" />
            <el-table-column prop="latitude" label="纬度" />
            <el-table-column prop="annual_rent" label="合同年租金" />
          </el-table>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="newCurrentPage"
              v-model:page-size="newPageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              :total="newTotal"
              @size-change="handleNewSizeChange"
              @current-change="handleNewCurrentChange"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 左下区域：RAG文档管理 -->
      <el-col :span="12" class="data-section">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>RAG文档管理</span>
              <el-upload
                class="upload-demo"
                action="/api/v1/documents/import"
                :on-success="handleRagUploadSuccess"
                :on-error="handleRagUploadError"
                :before-upload="beforeRagUpload"
                accept=".txt,.pdf,.doc,.docx"
              >
                <el-button type="primary">上传文档</el-button>
              </el-upload>
            </div>
          </template>
          <div class="table-container">
            <el-table 
              :data="ragDocuments" 
              style="width: 100%" 
              v-loading="ragLoading"
              height="calc(100vh - 250px)"
            >
              <el-table-column prop="source" label="文档来源" />
              <el-table-column prop="page" label="页码" />
              <el-table-column prop="row" label="行号" />
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 右下区域：预留 -->
      <el-col :span="12" class="data-section">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>智能BI请求记录</span>
            </div>
          </template>
          <div class="table-container">
            <el-table 
              :data="chartRecords" 
              style="width: 100%" 
              v-loading="chartLoading"
              height="calc(100vh - 250px)"
            >
              <el-table-column prop="name" label="图表名称" />
              <el-table-column prop="goal" label="分析目标" />
              <el-table-column prop="chartType" label="图表类型" />
              <el-table-column prop="status" label="状态">
                <template #default="scope">
                  <el-tag :type="getStatusType(scope.row.status)">
                    {{ getStatusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="createTime" label="创建时间" />
            </el-table>
          </div>
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="chartCurrentPage"
              v-model:page-size="chartPageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              :total="chartTotal"
              @size-change="handleChartSizeChange"
              @current-change="handleChartCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'  // 修改这里，使用新的 axios 实例

// 存量机房数据相关
const existingData = ref([])
const existingLoading = ref(false)
const existingCurrentPage = ref(1)
const existingPageSize = ref(10)
const existingTotal = ref(0)

// 新增机房数据相关
const newData = ref([])
const newLoading = ref(false)
const newCurrentPage = ref(1)
const newPageSize = ref(10)
const newTotal = ref(0)

// RAG文档相关
const ragDocuments = ref([])
const ragLoading = ref(false)

// 图表记录相关
const chartRecords = ref([])
const chartLoading = ref(false)
const chartCurrentPage = ref(1)
const chartPageSize = ref(10)
const chartTotal = ref(0)

// 获取存量机房数据
const fetchExistingData = async () => {
  existingLoading.value = true
  try {
    const response = await request.get('/api/data/centers', {
      params: {
        page: existingCurrentPage.value,
        size: existingPageSize.value
      }
    })
    existingData.value = response.data || []
    existingTotal.value = response.total || 0
  } catch (error) {
    console.error('获取存量机房数据失败:', error)
  } finally {
    existingLoading.value = false
  }
}

// 上传相关处理函数
const beforeUpload = (file) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  const isCSV = file.type === 'text/csv'
  if (!isExcel && !isCSV) {
    ElMessage.error('只能上传 Excel 或 CSV 文件！')
    return false
  }
  return true
}

const handleExistingUploadSuccess = (response) => {
  if (response.success) {
    ElMessage.success('存量机房数据上传成功')
    fetchExistingData()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleNewUploadSuccess = (response) => {
  if (response.success) {
    ElMessage.success('新增机房数据上传成功')
    newData.value = response.data
    newTotal.value = response.total
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 分页处理函数
const handleExistingSizeChange = (val) => {
  existingPageSize.value = val
  fetchExistingData()
}

const handleExistingCurrentChange = (val) => {
  existingCurrentPage.value = val
  fetchExistingData()
}

const handleNewSizeChange = (val) => {
  newPageSize.value = val
}

const handleNewCurrentChange = (val) => {
  newCurrentPage.value = val
}

const handleNewUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await request.post('/api/data/upload/new', formData)
    if (response.data.success) {
      newData.value = response.data.data
      newTotal.value = response.data.total
      ElMessage.success('新增机房数据上传成功')
    } else {
      ElMessage.error(response.data.message || '上传失败')
    }
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message))
  }
}

const handleExistingUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await request.post('/api/data/upload/existing', formData)
    if (response.data.success) {
      ElMessage.success('存量机房数据上传成功')
      // 刷新存量机房数据列表
      fetchExistingData()
    } else {
      ElMessage.error(response.data.message || '上传失败')
    }
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message))
  }
}

// 获取RAG文档列表
const fetchRagDocuments = async () => {
  ragLoading.value = true
  try {
    const response = await request.get('/api/v1/documents/list')
    // 直接使用 response.data，因为响应拦截器已经处理了 success 检查
    ragDocuments.value = response.data || []
  } catch (error) {
    console.error('获取文档列表失败:', error)
  } finally {
    ragLoading.value = false
  }
}

// RAG文档上传相关处理函数
const beforeRagUpload = (file) => {
  const allowedTypes = ['.txt', '.pdf', '.doc', '.docx']
  const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!allowedTypes.includes(fileExt)) {
    ElMessage.error('只能上传 .txt, .pdf, .doc, .docx 格式的文件！')
    return false
  }
  return true
}

const handleRagUploadSuccess = (response) => {
  if (response.success) {
    ElMessage.success('文档上传成功')
    fetchRagDocuments()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleRagUploadError = (error) => {
  ElMessage.error('上传失败：' + (error.response?.data?.detail || error.message))
}

// 获取图表记录
const fetchChartRecords = async () => {
  chartLoading.value = true
  try {
    const response = await request.post('/api/chart/my/list/page', {
      current: chartCurrentPage.value,
      size: chartPageSize.value
    })
    chartRecords.value = response.records || []
    chartTotal.value = response.total || 0
  } catch (error) {
    console.error('获取图表记录失败:', error)
  } finally {
    chartLoading.value = false
  }
}

// 图表状态处理
const getStatusType = (status) => {
  const statusMap = {
    0: 'info',    // 等待中
    1: 'success', // 成功
    2: 'danger'   // 失败
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    0: '等待中',
    1: '成功',
    2: '失败'
  }
  return statusMap[status] || '未知'
}

// 图表分页处理
const handleChartSizeChange = (val) => {
  chartPageSize.value = val
  fetchChartRecords()
}

const handleChartCurrentChange = (val) => {
  chartCurrentPage.value = val
  fetchChartRecords()
}

// 初始化
onMounted(() => {
  fetchExistingData()
  fetchRagDocuments()
  fetchChartRecords()
})
</script>

<style scoped>
.home-container {
  padding: 20px;
  height: 100vh;
  box-sizing: border-box;
}

.main-row {
  height: 100%;
}

.data-section {
  margin-bottom: 20px;
}

.box-card {
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-container {
  flex: 1;
  overflow: hidden;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.placeholder-content {
  height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #909399;
  font-size: 16px;
}

:deep(.el-card__body) {
  height: calc(100% - 55px);
  display: flex;
  flex-direction: column;
  padding: 20px;
}

:deep(.el-table) {
  flex: 1;
  overflow: hidden;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
}
</style> 