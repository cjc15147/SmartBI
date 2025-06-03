<template>
  <div class="overview-container">
    <!-- 顶部操作区 -->
    <div class="operation-area">
      <el-upload
        class="upload-demo"
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        accept=".xlsx,.csv"
      >
        <el-button type="primary">选择新增机房数据</el-button>
      </el-upload>
      
      <div class="radius-input">
        <el-input-number
          v-model="radiusKm"
          :min="1"
          :max="100"
          :step="1"
          placeholder="请输入稽核半径(km)"
        />
        <el-button type="primary" @click="handleAnalyze" :loading="analyzing">
          开始稽核
        </el-button>
      </div>
    </div>

    <!-- 数据展示区 -->
    <div class="data-display">
      <!-- 左上：地图展示 -->
      <div class="map-container">
        <div id="map" class="map"></div>
      </div>
      
      <!-- 右上：散点图 -->
      <div class="scatter-container">
        <div ref="scatterChartRef" class="scatter-chart"></div>
      </div>

      <!-- 左下：详细稽核结果表格 -->
      <div class="audit-table-container">
        <el-card>
          <template #header>
            <span>详细稽核结果</span>
          </template>
          <div class="table-scroll-x">
            <el-table :data="auditResults" style="width: 100%" v-loading="auditLoading" height="300">
              <el-table-column prop="new_longitude" label="新增机房经度" min-width="120" />
              <el-table-column prop="new_latitude" label="新增机房纬度" min-width="120" />
              <el-table-column prop="new_annual_rent" label="新增机房年租金" min-width="120" />
              <el-table-column prop="nearby_avg_rent" label="周边平均租金" min-width="120" />
              <el-table-column prop="nearby_min_rent" label="周边最低租金" min-width="120" />
              <el-table-column prop="nearby_max_rent" label="周边最高租金" min-width="120" />
              <el-table-column prop="nearest_rent" label="最近机房租金" min-width="120" />
              <el-table-column prop="nearest_name" label="最近机房名称" min-width="120" />
              <el-table-column prop="nearest_contract_code" label="最近合同编码" min-width="120" />
              <el-table-column prop="rent_comparison_avg" label="与平均租金比较" min-width="120" />
              <el-table-column prop="rent_comparison_nearest" label="与最近机房比较" min-width="120" />
              <el-table-column prop="analysis_result" label="分析结果" min-width="200" />
            </el-table>
          </div>
        </el-card>
      </div>

      <!-- 右下：AI稽核总结 -->
      <div class="ai-summary-container">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>AI稽核总结</span>
              <el-button type="primary" size="small" :loading="aiLoading" @click="handleAISummary">AI总结</el-button>
            </div>
          </template>
          <div class="ai-summary-content" v-loading="aiLoading">
            <div v-if="aiSummary" style="white-space: pre-line;">{{ aiSummary }}</div>
            <div v-else class="ai-summary-placeholder">点击上方按钮生成AI稽核总结</div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, onActivated, onDeactivated } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'
import request from '@/utils/request'

// 地图相关
let map = null
let markers = []

// 散点图相关
const scatterChartRef = ref(null)
let scatterChart = null
const scatterData = ref(null)

// 数据相关
const radiusKm = ref(5)
const analyzing = ref(false)
const uploadFile = ref(null)
const auditResults = ref([])
const auditLoading = ref(false)
const aiSummary = ref('')
const aiLoading = ref(false)

// 监听散点图数据变化
watch(scatterData, (newData) => {
  if (newData) {
    nextTick(() => {
      updateScatterChart(newData)
    })
  }
}, { deep: true })

// 处理文件选择
const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

// 处理分析请求
const handleAnalyze = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择新增机房数据文件')
    return
  }

  analyzing.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    formData.append('radius_km', radiusKm.value)

    console.log('开始发送分析请求...')
    const response = await axios.post('/api/data/analyze', formData)
    console.log('收到后端响应:', response.data)
    
    if (response.data) {
      // 清除旧标记
      clearMarkers()
      // 添加新标记
      addMarkersToMap(response.data.map_data)
      
      // 检查并转换散点图数据
      const scatterData = response.data.scatter_data
      console.log('后端返回的散点图数据:', JSON.stringify(scatterData, null, 2))
      
      if (scatterData && scatterData.existing && scatterData.new) {
        // 确保数据格式正确
        const formattedData = {
          existing: scatterData.existing.map(item => ({
            longitude: Number(item.longitude),
            latitude: Number(item.latitude),
            annual_rent: Number(item.annual_rent)
          })),
          new: scatterData.new.map(item => ({
            longitude: Number(item.longitude),
            latitude: Number(item.latitude),
            annual_rent: Number(item.annual_rent)
          }))
        }
        console.log('格式化后的散点图数据:', JSON.stringify(formattedData, null, 2))
        // 直接调用updateScatterChart更新图表
        updateScatterChart(formattedData)
      } else {
        console.error('散点图数据格式不正确:', scatterData)
        ElMessage.error('散点图数据格式不正确')
      }

      auditLoading.value = true
      auditResults.value = response.data.audit_results || []
      auditLoading.value = false
    }
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败：' + (error.response?.data?.detail || error.message))
  } finally {
    analyzing.value = false
  }
}

// 初始化地图
const initMap = () => {
  map = L.map('map').setView([34.341575, 108.93977], 11) // 西安市中心坐标

  // 添加 OpenStreetMap 底图
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)
}

// 初始化散点图
const initScatterChart = () => {
  try {
    console.log('开始初始化散点图...')
    if (!scatterChartRef.value) {
      console.error('散点图容器未找到')
      return
    }
    
    if (scatterChart) {
      console.log('销毁旧的散点图实例')
      scatterChart.dispose()
    }
    
    console.log('创建新的散点图实例')
    scatterChart = echarts.init(scatterChartRef.value)
    console.log('散点图实例创建成功')
    
    // 设置一个默认的空配置
    const option = {
      title: {
        text: '机房分布散点图',
        left: '5%',
        top: '3%'
      },
      tooltip: {
        trigger: 'item'
      },
      xAxis: {
        type: 'value',
        name: '经度'
      },
      yAxis: {
        type: 'value',
        name: '纬度'
      },
      series: [
        {
          name: '存量机房',
          type: 'scatter',
          data: []
        },
        {
          name: '新增机房',
          type: 'scatter',
          data: []
        }
      ]
    }
    console.log('设置初始配置:', option)
    scatterChart.setOption(option)
    console.log('散点图初始化完成')
  } catch (error) {
    console.error('初始化散点图失败:', error)
  }
}

// 更新散点图数据
const updateScatterChart = (data) => {
  console.log('开始更新散点图数据...')
  if (!scatterChart) {
    console.error('散点图实例未初始化')
    return
  }

  try {
    console.log('原始数据:', data)
    
    // 数据预处理
    const existingData = data.existing.map(item => {
      const formatted = {
        longitude: Number(item.longitude),
        latitude: Number(item.latitude),
        annual_rent: Number(item.annual_rent)
      }
      console.log('格式化存量机房数据项:', formatted)
      return formatted
    })
    
    const newData = data.new.map(item => {
      const formatted = {
        longitude: Number(item.longitude),
        latitude: Number(item.latitude),
        annual_rent: Number(item.annual_rent)
      }
      console.log('格式化新增机房数据项:', formatted)
      return formatted
    })
    
    console.log('格式化后的数据:', { existing: existingData, new: newData })
    
    const option = {
      backgroundColor: new echarts.graphic.RadialGradient(0.3, 0.3, 0.8, [
        {
          offset: 0,
          color: '#f7f8fa'
        },
        {
          offset: 1,
          color: '#cdd0d5'
        }
      ]),
      title: {
        text: '机房分布散点图',
        left: '5%',
        top: '3%'
      },
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          return `经度: ${params.data[0]}<br/>纬度: ${params.data[1]}<br/>年租金: ${params.data[2]}元`
        }
      },
      legend: {
        right: '10%',
        top: '3%',
        data: ['存量机房', '新增机房']
      },
      grid: {
        left: '8%',
        top: '10%'
      },
      xAxis: {
        type: 'value',
        name: '经度',
        min: 108.9,
        max: 108.93,
        splitLine: {
          lineStyle: {
            type: 'dashed'
          }
        }
      },
      yAxis: {
        type: 'value',
        name: '纬度',
        min: 34.29,
        max: 34.32,
        splitLine: {
          lineStyle: {
            type: 'dashed'
          }
        },
        scale: true
      },
      series: [
        {
          name: '存量机房',
          data: existingData.map(item => [item.longitude, item.latitude, item.annual_rent]),
          type: 'scatter',
          symbolSize: function(data) {
            return Math.sqrt(data[2]) / 10
          },
          emphasis: {
            focus: 'series',
            label: {
              show: true,
              formatter: function(param) {
                return `年租金: ${param.data[2]}元`
              },
              position: 'top'
            }
          },
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(25, 100, 150, 0.5)',
            shadowOffsetY: 5,
            color: new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
              {
                offset: 0,
                color: 'rgb(129, 227, 238)'
              },
              {
                offset: 1,
                color: 'rgb(25, 183, 207)'
              }
            ])
          }
        },
        {
          name: '新增机房',
          data: newData.map(item => [item.longitude, item.latitude, item.annual_rent]),
          type: 'scatter',
          symbolSize: function(data) {
            return Math.sqrt(data[2]) / 10
          },
          emphasis: {
            focus: 'series',
            label: {
              show: true,
              formatter: function(param) {
                return `年租金: ${param.data[2]}元`
              },
              position: 'top'
            }
          },
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(120, 36, 50, 0.5)',
            shadowOffsetY: 5,
            color: new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
              {
                offset: 0,
                color: 'rgb(251, 118, 123)'
              },
              {
                offset: 1,
                color: 'rgb(204, 46, 72)'
              }
            ])
          }
        }
      ]
    }
    console.log('设置新的配置:', option)
    scatterChart.setOption(option, true)
    scatterChart.resize()
    console.log('散点图更新完成')
  } catch (error) {
    console.error('更新散点图失败:', error)
  }
}

// 清除地图标记
const clearMarkers = () => {
  markers.forEach(marker => map.removeLayer(marker))
  markers = []
}

// 添加标记到地图
const addMarkersToMap = (mapData) => {
  // 添加存量机房标记（蓝色）
  mapData.existing_markers.forEach(marker => {
    const markerInstance = L.marker([marker.latitude, marker.longitude], {
      icon: L.divIcon({
        className: 'custom-marker existing',
        html: '<div class="marker-pin existing"></div>',
        iconSize: [30, 42],
        iconAnchor: [15, 42]
      })
    }).addTo(map)

    // 添加信息窗体
    const content = `
      <div class="info-window">
        <p>经度：${marker.longitude}</p>
        <p>纬度：${marker.latitude}</p>
        <p>合同年租金：${marker.annual_rent}</p>
      </div>
    `
    markerInstance.bindPopup(content)
    markers.push(markerInstance)
  })

  // 添加新增机房标记（红色）
  mapData.new_markers.forEach(marker => {
    const markerInstance = L.marker([marker.latitude, marker.longitude], {
      icon: L.divIcon({
        className: 'custom-marker new',
        html: '<div class="marker-pin new"></div>',
        iconSize: [30, 42],
        iconAnchor: [15, 42]
      })
    }).addTo(map)

    // 添加信息窗体
    const content = `
      <div class="info-window">
        <p>经度：${marker.longitude}</p>
        <p>纬度：${marker.latitude}</p>
        <p>合同年租金：${marker.annual_rent}</p>
      </div>
    `
    markerInstance.bindPopup(content)
    markers.push(markerInstance)
  })
}

// 处理AI总结请求
const handleAISummary = async () => {
  if (!auditResults.value || auditResults.value.length === 0) {
    ElMessage.warning('请先完成稽核分析')
    return
  }
  aiLoading.value = true
  aiSummary.value = ''
  try {
    const response = await axios.post('/api/data/audit/summary', auditResults.value)
    aiSummary.value = response.data.summary || 'AI未返回有效总结'
  } catch (error) {
    ElMessage.error('AI总结生成失败')
    aiSummary.value = 'AI总结生成失败'
  } finally {
    aiLoading.value = false
  }
}

// 生命周期钩子
const initAll = () => {
  console.log('开始初始化所有组件...')
  nextTick(() => {
    console.log('DOM更新完成，开始初始化图表...')
    initMap()
    initScatterChart()
  })
}

onMounted(() => {
  initAll()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (map) {
    map.destroy()
  }
  if (scatterChart) {
    scatterChart.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

// 若用keep-alive，支持激活/失活自动重建和销毁
onActivated(() => {
  initAll()
})
onDeactivated(() => {
  if (map) map.destroy()
  if (scatterChart) scatterChart.dispose()
})

// 处理窗口大小变化
const handleResize = () => {
  if (scatterChart) {
    scatterChart.resize()
  }
}
</script>

<style lang="scss" scoped>
.overview-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.operation-area {
  display: flex;
  gap: 20px;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);

  .radius-input {
    display: flex;
    gap: 10px;
    align-items: center;
  }
}

.data-display {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 20px;
  padding: 0 20px 20px;
  min-height: 600px;

  .map-container,
  .scatter-container,
  .audit-table-container,
  .ai-summary-container {
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    overflow: hidden;
    height: 400px;
    min-height: 400px;
  }

  .map,
  .scatter-chart {
    width: 100%;
    height: 100%;
    min-height: 400px;
  }
}

.audit-table-container {
  grid-column: 1 / 2;
  grid-row: 2 / 3;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.el-card) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-card__body) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }

  .table-scroll-x {
    height: 100%;
    overflow: auto;
  }
}

.ai-summary-container {
  grid-column: 2 / 3;
  grid-row: 2 / 3;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.el-card) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  :deep(.el-card__body) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }

  .ai-summary-content {
    height: 100%;
    font-size: 15px;
    color: #333;
    padding: 10px 0;
    word-break: break-all;
    overflow-y: auto;
  }
}

:deep(.custom-marker) {
  .marker-pin {
    width: 30px;
    height: 30px;
    border-radius: 50% 50% 50% 0;
    position: relative;
    transform: rotate(-45deg);
    left: 50%;
    top: 50%;
    margin: -15px 0 0 -15px;
    
    &.existing {
      background: #409EFF;
    }
    
    &.new {
      background: #F56C6C;
    }
    
    &:after {
      content: '';
      width: 14px;
      height: 14px;
      margin: 8px 0 0 8px;
      background: #fff;
      position: absolute;
      border-radius: 50%;
    }
  }
}

:deep(.info-window) {
  padding: 10px;
  font-size: 14px;
  line-height: 1.5;
  
  p {
    margin: 5px 0;
  }
}

:deep(.leaflet-popup-content-wrapper) {
  border-radius: 4px;
}

:deep(.leaflet-popup-content) {
  margin: 10px;
}

.scatter-chart {
  width: 100%;
  height: 400px !important;
  min-height: 300px;
}

.ai-summary-placeholder {
  color: #aaa;
  font-size: 14px;
  text-align: center;
  margin-top: 40px;
}
</style> 