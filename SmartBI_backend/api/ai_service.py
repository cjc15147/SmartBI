from typing import Dict, Optional
import json
import logging
from openai import OpenAI
from datetime import datetime
from utils.rag_utils import RAGService

logger = logging.getLogger(__name__)

"""
AI服务API模块

本模块提供AI相关服务的核心业务逻辑实现，包括：

功能列表：
1. 智能分析
   - 数据智能分析
   - 趋势预测
   - 异常检测
   
2. 自然语言处理
   - 文本分析
   - 语义理解
   - 智能问答
   
3. 机器学习服务
   - 模型训练
   - 模型预测
   - 模型评估
   
4. AI辅助决策
   - 数据洞察
   - 决策建议
   - 风险评估

技术实现：
- 集成多个AI模型和算法
- 支持实时处理和批处理
- 实现了模型版本控制
- 支持模型热更新
- 集成RAG功能，支持政策检索

依赖关系：
- scikit-learn: 机器学习库
- tensorflow/pytorch: 深度学习框架
- database: 数据存储
- utils.ai_utils: AI工具集
- utils.rag_utils: RAG工具集

性能特性：
- 模型缓存机制
- 异步处理支持
- GPU加速支持
- 分布式处理能力

安全考虑：
- 数据安全保护
- 模型访问控制
- 资源使用限制
- 完整的审计日志
"""

class AiService:
    """AI服务类,处理与AI模型的交互"""
    
    def __init__(self):
        # DeepSeek API配置
        self.api_key = "sk-your-key"
        self.base_url = "https://api.deepseek.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # 初始化RAG服务
        self.rag_service = RAGService()
        
    def generate_chart(self, goal: str, chart_type: Optional[str], csv_data: str) -> Dict[str, str]:
        """调用AI生成图表和分析结论"""
        try:
            # 使用RAG检索相关政策
            policy_context = self.rag_service.query(goal)
            
            # 构造提示语
            prompt = self._build_prompt(goal, chart_type, csv_data, policy_context)
            
            # 调用 DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析和可视化助手，擅长使用 Streamlit 生成图表代码。你需要生成完整可运行的 Python 代码，包含所有必要的导入语句和数据处理步骤。"},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            
            # 获取响应内容
            response_text = response.choices[0].message.content
            
            # 解析响应
            result = self.parse_ai_response(response_text)
            return result
            
        except Exception as e:
            logger.error(f"AI生成图表失败: {str(e)}")
            raise Exception(f"AI生成图表失败: {str(e)}")
    
    def _build_prompt(self, goal: str, chart_type: Optional[str], csv_data: str, policy_context: str) -> str:
        """构建AI提示语"""
        prompt = f"""请根据以下数据和要求生成 ECharts 图表代码：

1. 分析目标：{goal}

2. 相关政策和规定：
{policy_context}

3. 数据内容：
{csv_data}

"""
        if chart_type:
            prompt += f"4. 图表类型：请使用{chart_type}类型的图表\n"
        else:
            prompt += "4. 请根据数据特点选择合适的图表类型\n"
            
        prompt += """
请严格按照以下JSON格式返回结果，注意：
1. 必须返回标准的JSON格式，不要包含任何换行符或特殊字符
2. chartData必须是完整的JSON对象，不要是字符串
3. 所有字符串必须使用双引号，不要使用单引号
4. 不要包含任何注释或说明文字

返回格式示例：
{
    "chartType": "折线图",
    "chartData": {
        "title": {
            "text": "示例图表"
        },
        "xAxis": {
            "type": "category",
            "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        },
        "yAxis": {
            "type": "value"
        },
        "series": [{
            "data": [150, 230, 224, 218, 135, 147, 260],
            "type": "line"
        }]
    },
    "genResult": "分析结论"
}

注意：
1. chartType必须是具体的图表类型，如：折线图、柱状图、饼图等
2. chartData必须是完整的 ECharts option 配置对象：
   - 必须是合法的 JSON 对象
   - 必须包含所有必要的配置项（如：title、xAxis、yAxis、series等）
   - 所有属性名和字符串值必须使用双引号
3. genResult必须是对数据的详细分析结论，并考虑相关政策规定
4. 请只返回JSON格式的结果，不要包含其他说明文字
"""
        return prompt
    
    def parse_ai_response(self, response: str) -> Dict[str, str]:
        """解析AI响应结果"""
        try:
            # 提取JSON字符串
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("未找到有效的JSON响应")
                
            json_str = response[start_idx:end_idx]
            result = json.loads(json_str)
            
            # 验证必要字段
            required_fields = ["chartType", "chartData", "genResult"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"响应中缺少必要字段: {field}")
            
            # 处理chartData
            if isinstance(result["chartData"], str):
                try:
                    # 尝试解析chartData为JSON对象
                    chart_data = json.loads(result["chartData"])
                    result["chartData"] = chart_data
                except json.JSONDecodeError:
                    # 如果解析失败，尝试清理字符串
                    cleaned_data = result["chartData"].replace("\n", "").replace("    ", "")
                    try:
                        # 再次尝试解析
                        chart_data = json.loads(cleaned_data)
                        result["chartData"] = chart_data
                    except json.JSONDecodeError:
                        # 如果还是失败，记录错误并抛出异常
                        logger.error(f"无法解析chartData: {result['chartData']}")
                        raise ValueError("图表数据格式无效")
            
            return result
        except Exception as e:
            logger.error(f"解析AI响应失败: {str(e)}\nResponse: {response}")
            raise Exception(f"解析AI响应失败: {str(e)}") 