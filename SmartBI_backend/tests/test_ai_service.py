import unittest
import logging
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.ai_service import AiService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestAiService(unittest.TestCase):
    def setUp(self):
        """测试初始化"""
        self.ai_service = AiService()
        # 准备测试数据
        self.test_csv_data = """日期,销售额,利润
2023-01,100,20
2023-02,150,30
2023-03,180,36
2023-04,120,24
2023-05,200,40"""
    
    def test_generate_chart_with_type(self):
        """测试指定图表类型生成图表"""
        logger.info("开始测试指定图表类型的生成")
        try:
            result = self.ai_service.generate_chart(
                goal="分析月度销售额和利润的变化趋势",
                chart_type="折线图",
                csv_data=self.test_csv_data
            )
            
            # 验证返回结果
            self.assertIsInstance(result, dict)
            self.assertIn("chartType", result)
            self.assertIn("chartData", result)
            self.assertIn("genResult", result)
            
            # 验证图表类型
            self.assertEqual(result["chartType"], "折线图")
            
            # 输出生成的代码和结果
            logger.info("\n=== 测试结果 ===")
            logger.info(f"图表类型: {result['chartType']}")
            logger.info("\n=== Streamlit 代码 ===")
            logger.info(result['chartData'])
            logger.info("\n=== 分析结论 ===")
            logger.info(result['genResult'])
            
            # 验证代码中包含必要的导入语句
            self.assertIn("import streamlit", result['chartData'])
            self.assertIn("import pandas", result['chartData'])
            
        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
            raise
    
    def test_generate_chart_without_type(self):
        """测试自动选择图表类型生成图表"""
        logger.info("开始测试自动选择图表类型的生成")
        try:
            result = self.ai_service.generate_chart(
                goal="比较各月份销售额和利润的关系",
                chart_type=None,
                csv_data=self.test_csv_data
            )
            
            # 验证返回结果
            self.assertIsInstance(result, dict)
            self.assertIn("chartType", result)
            self.assertIn("chartData", result)
            self.assertIn("genResult", result)
            
            # 输出生成的代码和结果
            logger.info("\n=== 测试结果 ===")
            logger.info(f"AI选择的图表类型: {result['chartType']}")
            logger.info("\n=== Streamlit 代码 ===")
            logger.info(result['chartData'])
            logger.info("\n=== 分析结论 ===")
            logger.info(result['genResult'])
            
            # 验证代码中包含必要的导入语句
            self.assertIn("import streamlit", result['chartData'])
            self.assertIn("import pandas", result['chartData'])
            
        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
            raise
    
    def test_prompt_building(self):
        """测试提示语构建"""
        logger.info("开始测试提示语构建")
        prompt = self.ai_service._build_prompt(
            goal="测试目标",
            chart_type="测试图表",
            csv_data="测试数据"
        )
        
        # 验证提示语包含必要的部分
        self.assertIn("分析目标：测试目标", prompt)
        self.assertIn("测试数据", prompt)
        self.assertIn("测试图表", prompt)
        self.assertIn("import streamlit", prompt)
        self.assertIn("import pandas", prompt)
        self.assertIn("chartType", prompt)
        self.assertIn("chartData", prompt)
        self.assertIn("genResult", prompt)

if __name__ == '__main__':
    unittest.main() 