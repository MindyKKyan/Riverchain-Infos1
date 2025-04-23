"""
测试工具函数
"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from core.utils import normalize_company_name, clean_text, format_date, extract_domain

class TestUtils(unittest.TestCase):
    """测试工具函数"""
    
    def test_normalize_company_name(self):
        """测试公司名称标准化"""
        self.assertEqual(normalize_company_name("ABC Ltd."), "abc")
        self.assertEqual(normalize_company_name("ABC Company Limited"), "abc company")
        self.assertEqual(normalize_company_name("香港ABC有限公司"), "香港abc")
    
    def test_clean_text(self):
        """测试文本清理"""
        self.assertEqual(clean_text("  Hello  World  "), "Hello World")
        self.assertEqual(clean_text("<p>Hello</p>"), "Hello")
        self.assertEqual(clean_text(""), "")
    
    def test_format_date(self):
        """测试日期格式化"""
        self.assertEqual(format_date("2022-05-01"), "2022-05-01")
        self.assertEqual(format_date("01/05/2022", "%d/%m/%Y"), "2022-05-01")
    
    def test_extract_domain(self):
        """测试域名提取"""
        self.assertEqual(extract_domain("https://www.example.com/path"), "example.com")
        self.assertEqual(extract_domain("http://example.org"), "example.org")

if __name__ == "__main__":
    unittest.main() 