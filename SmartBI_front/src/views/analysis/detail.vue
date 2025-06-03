<template>
  <div class="analysis-container">
    <div class="analysis-grid">
      <!-- 左上：文件上传和预览区域 -->
      <div class="upload-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据文件上传</span>
            </div>
          </template>
          <el-upload
            class="upload-area"
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handleFileChange"
            :before-upload="beforeUpload"
            accept=".xlsx,.csv"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 .xlsx 或 .csv 格式文件</div>
            </template>
          </el-upload>
          
          <div v-if="fileName" class="file-info">
            <span>已选择文件：{{ fileName }}</span>
          </div>
          
          <div v-if="previewData.length" class="preview-table">
            <el-table :data="previewData" style="width: 100%" max-height="200">
              <el-table-column v-for="col in previewColumns" :key="col" :prop="col" :label="col" />
            </el-table>
          </div>
        </el-card>
      </div>

      <!-- 右上：分析信息输入区域 -->
      <div class="input-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>分析信息配置</span>
            </div>
          </template>
          <el-form :model="analysisForm" label-width="100px">
            <el-form-item label="分析目标">
              <el-input
                v-model="analysisForm.goal"
                type="textarea"
                :rows="3"
                placeholder="请输入分析目标，例如：分析机房价格趋势"
              />
            </el-form-item>
            <el-form-item label="图表名称">
              <el-input v-model="analysisForm.name" placeholder="请输入图表名称" />
            </el-form-item>
            <el-form-item label="图表类型">
              <el-select v-model="analysisForm.chartType" placeholder="请选择图表类型">
                <el-option label="折线图" value="折线图" />
                <el-option label="柱状图" value="柱状图" />
                <el-option label="饼图" value="饼图" />
                <el-option label="散点图" value="散点图" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="analyzing" @click="handleAnalyze">
                开始分析
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- 左下：分析结论区域 -->
      <div class="result-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>分析结论</span>
            </div>
          </template>
          <div class="analysis-result">
            <el-input
              v-model="aiResult"
              type="textarea"
              :rows="12"
              readonly
              placeholder="分析结论将在这里显示..."
            />
          </div>
        </el-card>
      </div>

      <!-- 右下：图表展示区域 -->
      <div class="chart-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>分析图表</span>
            </div>
          </template>
          <div id="analysis-chart" class="chart-container"></div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { useRouter } from 'vue-router'

// 文件相关
const file = ref(null)
const fileName = ref('')
const previewData = ref([])
const previewColumns = ref([])

// 分析表单
const analysisForm = reactive({
  goal: '',
  name: '',
  chartType: '折线图'
})

// 分析结果
const analyzing = ref(false)
const aiResult = ref('')
let chartInstance = null

const router = useRouter()

// 文件上传前检查
const beforeUpload = (fileObj) => {
  const isExcel = fileObj.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  const isCSV = fileObj.type === 'text/csv'
  if (!isExcel && !isCSV) {
    ElMessage.error('只能上传 Excel 或 CSV 文件！')
    return false
  }
  return true
}

// 文件变更处理
const handleFileChange = (fileObj) => {
  file.value = fileObj.raw
  fileName.value = fileObj.name
  // TODO: 实现文件预览逻辑
  previewData.value = []
  previewColumns.value = []
}

// 开始分析
const handleAnalyze = async () => {
  if (!file.value) {
    ElMessage.warning('请先上传数据文件')
    return
  }
  if (!analysisForm.goal) {
    ElMessage.warning('请输入分析目标')
    return
  }
  if (!analysisForm.name) {
    ElMessage.warning('请输入图表名称')
    return
  }

  analyzing.value = true
  aiResult.value = ''
  
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('goal', analysisForm.goal)
    formData.append('name', analysisForm.name)
    formData.append('chart_type', analysisForm.chartType)

    console.log('Sending request with data:', {
      goal: analysisForm.goal,
      name: analysisForm.name,
      chart_type: analysisForm.chartType,
      file: file.value.name
    })

    const response = await request({
      url: '/api/ai/gen',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 30000
    })
    
    console.log('AI analysis response:', response)
    
    if (response.code === 1 && response.data) {
      console.log('Analysis result:', response.data)
      aiResult.value = response.data.genResult || 'AI未返回分析结论'
      if (response.data.genChart) {
        try {
          console.log('Chart data:', response.data.genChart)
          // 直接使用图表数据，不需要解析
          renderChart(response.data.genChart)
        } catch (chartError) {
          console.error('Chart data error:', chartError)
          ElMessage.error('图表数据错误：' + chartError.message)
        }
      }
    } else {
      console.error('Invalid response:', response)
      ElMessage.error(response.msg || '分析失败')
    }
  } catch (error) {
    console.error('Analysis error:', error)
    if (error.response) {
      console.error('Error response:', error.response)
      console.error('Error response data:', error.response.data)
      if (error.response.status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      } else {
        ElMessage.error(`请求失败: ${error.response.data?.msg || error.message}`)
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timeout')
      ElMessage.error('请求超时，请稍后重试')
    } else {
      console.error('Network error:', error)
      ElMessage.error('网络连接失败，请检查网络')
    }
  } finally {
    analyzing.value = false
  }
}

// 渲染图表
const renderChart = (chartData) => {
  try {
    if (chartInstance) {
      chartInstance.dispose()
    }
    const chartDom = document.getElementById('analysis-chart')
    if (!chartDom) {
      console.error('Chart container not found')
      return
    }
    
    console.log('Initializing chart with data:', chartData)
    chartInstance = echarts.init(chartDom)
    chartInstance.setOption(chartData, true)
    console.log('Chart rendered successfully')
  } catch (error) {
    console.error('Chart rendering error:', error)
    ElMessage.error('图表渲染失败：' + error.message)
  }
}
</script>

<style lang="scss" scoped>
.analysis-container {
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  background-color: #f5f7fa;
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 20px;
  height: 100%;
}

.upload-section,
.input-section,
.result-section,
.chart-section {
  height: 100%;
  
  .el-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    :deep(.el-card__body) {
      flex: 1;
      overflow: auto;
    }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  margin-bottom: 20px;
}

.file-info {
  margin: 10px 0;
  color: #409EFF;
}

.preview-table {
  margin-top: 20px;
}

.analysis-result {
  height: 100%;
  
  :deep(.el-textarea__inner) {
    height: 100%;
    font-family: monospace;
  }
}

.chart-container {
  height: 100%;
  min-height: 300px;
}
</style> 