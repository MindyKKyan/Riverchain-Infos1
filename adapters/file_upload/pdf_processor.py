"""
PDF文件处理器 - PDF file processor
"""
import os
import re
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
import pdfplumber
import io

import sys
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.storage import get_storage_manager
from core.utils import clean_text

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pdf_processor')

class PDFProcessor:
    """PDF文件处理器"""
    
    def __init__(self):
        self.storage = get_storage_manager()
    
    def extract_text(self, file_path: str) -> str:
        """
        从PDF文件中提取文本
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        logger.info(f"Extracting text from PDF: {file_path}")
        
        all_text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    all_text += text + "\n\n"
                    
            # 清理文本
            all_text = clean_text(all_text)
            
            # 保存原始提取文本
            filename = os.path.basename(file_path)
            self.storage.save_raw_data(
                "pdf_extract", 
                all_text, 
                filename.replace(".pdf", "")
            )
            
            return all_text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_tables(self, file_path: str) -> List[pd.DataFrame]:
        """
        从PDF中提取表格
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            提取的表格列表，每个表格为DataFrame
        """
        logger.info(f"Extracting tables from PDF: {file_path}")
        
        tables = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for j, table in enumerate(page_tables):
                        if table:
                            # 转换为DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            # 添加页面和表格索引信息
                            df['page_number'] = i + 1
                            df['table_number'] = j + 1
                            tables.append(df)
            
            logger.info(f"Extracted {len(tables)} tables from PDF")
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {e}")
            return []
    
    def extract_company_info(self, file_path: str) -> Dict[str, Any]:
        """
        从PDF中提取公司相关信息
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            提取的公司信息
        """
        logger.info(f"Extracting company information from PDF: {file_path}")
        
        # 提取文本
        text = self.extract_text(file_path)
        
        # 提取表格
        tables = self.extract_tables(file_path)
        
        # 解析公司信息
        company_info = self._parse_company_info(text)
        
        # 如果有表格数据，添加表格摘要
        if tables:
            company_info['tables'] = []
            for i, df in enumerate(tables):
                table_info = {
                    'table_index': i + 1,
                    'rows': len(df),
                    'columns': list(df.columns),
                    'summary': self._summarize_table(df)
                }
                company_info['tables'].append(table_info)
        
        return company_info
    
    def _parse_company_info(self, text: str) -> Dict[str, Any]:
        """
        从文本中解析公司相关信息
        
        Args:
            text: PDF提取的文本
            
        Returns:
            解析的公司信息
        """
        info = {
            'company_names': [],
            'company_numbers': [],
            'addresses': [],
            'contacts': [],
            'dates': [],
            'amounts': [],
            'projects': []
        }
        
        # 公司名称 (示例模式，需根据实际情况调整)
        company_pattern = r'([A-Z][A-Za-z\s]+)(Limited|Ltd\.?|LLC|Inc\.?|Corporation|Corp\.?)'
        for match in re.finditer(company_pattern, text):
            info['company_names'].append(match.group(0))
        
        # 公司注册号 (示例模式，需根据实际情况调整)
        reg_number_pattern = r'(?:Company|Registration|CR)[.\s]+(?:No|Number)[.\s:]+([A-Z0-9]+)'
        for match in re.finditer(reg_number_pattern, text, re.IGNORECASE):
            info['company_numbers'].append(match.group(1))
        
        # 地址 (示例模式，需根据实际情况调整)
        address_pattern = r'(?:Address|Registered Office|Location)[.\s:]+(.+?)(?:\n|\r|$)'
        for match in re.finditer(address_pattern, text, re.IGNORECASE):
            info['addresses'].append(clean_text(match.group(1)))
        
        # 联系方式 (示例模式，需根据实际情况调整)
        contact_pattern = r'(?:Tel|Phone|Contact)[.\s:]+([0-9\s\+\-]+)'
        for match in re.finditer(contact_pattern, text, re.IGNORECASE):
            info['contacts'].append(match.group(1).strip())
        
        # 日期 (示例模式，需根据实际情况调整)
        date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        for match in re.finditer(date_pattern, text):
            info['dates'].append(match.group(1))
        
        # 金额 (示例模式，需根据实际情况调整)
        amount_pattern = r'(?:HK\$|USD|CNY|RMB)?\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s?(?:million|billion|HKD|USD)?'
        for match in re.finditer(amount_pattern, text):
            info['amounts'].append(match.group(0))
        
        # 项目名称 (示例模式，需根据实际情况调整)
        project_pattern = r'Project[:\s]+([A-Za-z0-9\s]+)'
        for match in re.finditer(project_pattern, text, re.IGNORECASE):
            info['projects'].append(clean_text(match.group(1)))
        
        # 移除列表中的重复项
        for key in info:
            info[key] = list(set(info[key]))
        
        # 添加原始文本摘要
        info['text_summary'] = text[:500] + '...' if len(text) > 500 else text
        
        return info
    
    def _summarize_table(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成表格数据摘要
        
        Args:
            df: 表格数据
            
        Returns:
            表格摘要
        """
        summary = {}
        
        # 添加每列的基本统计信息
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # 数值列添加统计值
                summary[col] = {
                    'type': 'numeric',
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'sum': df[col].sum()
                }
            else:
                # 文本列添加值计数
                value_counts = df[col].value_counts().to_dict()
                # 只保留前5个
                top_values = dict(sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5])
                summary[col] = {
                    'type': 'text',
                    'unique_values': len(value_counts),
                    'top_values': top_values
                }
        
        return summary


def process_pdf(file_path: str, company_name: Optional[str] = None) -> Dict[str, Any]:
    """
    处理PDF文件，提取相关信息
    
    Args:
        file_path: PDF文件路径
        company_name: 相关公司名称（可选）
        
    Returns:
        提取的信息
    """
    processor = PDFProcessor()
    
    # 提取公司信息
    company_info = processor.extract_company_info(file_path)
    
    # 如果提供了公司名称，保存处理结果
    if company_name:
        storage = get_storage_manager()
        storage.save_company_data(
            company_name, 
            "document", 
            {
                "source": "pdf_upload",
                "filename": os.path.basename(file_path),
                "data": company_info
            }
        )
    
    return company_info


if __name__ == "__main__":
    # 测试代码
    test_file = "example.pdf"  # 替换为实际的测试文件路径
    if os.path.exists(test_file):
        result = process_pdf(test_file)
        print(f"Extracted company names: {result['company_names']}")
        print(f"Extracted amounts: {result['amounts']}")
    else:
        print(f"Test file {test_file} not found") 