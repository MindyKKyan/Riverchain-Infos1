"""
Excel文件处理器 - Excel file processor
"""
import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple

import sys
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.storage import get_storage_manager
from core.utils import clean_text

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('excel_processor')

class ExcelProcessor:
    """Excel文件处理器"""
    
    def __init__(self):
        self.storage = get_storage_manager()
    
    def read_excel(self, file_path: str) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        读取Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            DataFrame或多个sheet的DataFrame字典
        """
        logger.info(f"Reading Excel file: {file_path}")
        
        # 判断文件类型
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path, encoding='utf-8')
        
        # Excel文件
        try:
            # 获取sheet名称列表
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            if len(sheet_names) == 1:
                # 只有一个sheet，直接返回DataFrame
                return pd.read_excel(file_path, sheet_name=0)
            else:
                # 多个sheet，返回字典
                return pd.read_excel(file_path, sheet_name=None)
                
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析DataFrame的结构和内容
        
        Args:
            df: 要分析的DataFrame
            
        Returns:
            分析结果
        """
        # 基本信息
        result = {
            'shape': df.shape,
            'columns': list(df.columns),
            'data_types': {col: str(df[col].dtype) for col in df.columns},
            'null_counts': {col: int(df[col].isna().sum()) for col in df.columns},
            'sample': df.head(5).to_dict(orient='records')
        }
        
        # 数值列统计
        numeric_stats = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            numeric_stats[col] = {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std())
            }
        result['numeric_stats'] = numeric_stats
        
        # 分类列统计
        categorical_stats = {}
        for col in df.select_dtypes(include=['object', 'category']).columns:
            value_counts = df[col].value_counts().head(10).to_dict()  # 前10个最常见值
            categorical_stats[col] = {
                'unique_count': int(df[col].nunique()),
                'top_values': value_counts
            }
        result['categorical_stats'] = categorical_stats
        
        return result
    
    def extract_company_info(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]]) -> Dict[str, Any]:
        """
        从Excel数据中提取公司相关信息
        
        Args:
            data: Excel数据，单个DataFrame或多个sheet的DataFrame字典
            
        Returns:
            提取的公司信息
        """
        if isinstance(data, dict):
            # 多个sheet
            sheets_info = {}
            for sheet_name, df in data.items():
                sheets_info[sheet_name] = self.analyze_dataframe(df)
            
            # 尝试从所有sheet中查找公司相关信息
            company_info = self._search_company_info_in_sheets(data)
            
            return {
                'multi_sheet': True,
                'sheets_count': len(data),
                'sheets_info': sheets_info,
                'company_info': company_info
            }
        else:
            # 单个DataFrame
            df_analysis = self.analyze_dataframe(data)
            company_info = self._search_company_info_in_df(data)
            
            return {
                'multi_sheet': False,
                'df_info': df_analysis,
                'company_info': company_info
            }
    
    def _search_company_info_in_sheets(self, sheets_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        在多个sheet中搜索公司相关信息
        
        Args:
            sheets_data: 多个sheet的DataFrame字典
            
        Returns:
            公司相关信息
        """
        # 初始化结果
        result = {
            'company_names': [],
            'contacts': [],
            'addresses': [],
            'project_names': [],
            'financial_data': []
        }
        
        # 在每个sheet中查找
        for sheet_name, df in sheets_data.items():
            sheet_result = self._search_company_info_in_df(df)
            
            # 合并结果
            for key in result:
                if key in sheet_result:
                    result[key].extend(sheet_result[key])
        
        # 去重
        for key in result:
            result[key] = list(set(result[key]))
        
        return result
    
    def _search_company_info_in_df(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        在DataFrame中搜索公司相关信息
        
        Args:
            df: DataFrame
            
        Returns:
            公司相关信息
        """
        result = {
            'company_names': [],
            'contacts': [],
            'addresses': [],
            'project_names': [],
            'financial_data': []
        }
        
        # 搜索公司名称相关列
        company_keywords = ['company', 'corporation', 'corp', 'ltd', 'limited', '公司', '企业']
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in company_keywords):
                values = df[col].dropna().unique()
                for value in values:
                    if isinstance(value, str) and len(value) > 3:
                        result['company_names'].append(clean_text(value))
        
        # 搜索联系方式相关列
        contact_keywords = ['contact', 'phone', 'tel', 'email', 'fax', '联系', '电话', '邮箱']
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in contact_keywords):
                values = df[col].dropna().unique()
                for value in values:
                    if isinstance(value, str):
                        result['contacts'].append(clean_text(value))
        
        # 搜索地址相关列
        address_keywords = ['address', 'location', 'office', '地址', '办公室', '位置']
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in address_keywords):
                values = df[col].dropna().unique()
                for value in values:
                    if isinstance(value, str) and len(value) > 10:
                        result['addresses'].append(clean_text(value))
        
        # 搜索项目名称相关列
        project_keywords = ['project', 'tender', 'contract', '项目', '工程', '合同']
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in project_keywords):
                values = df[col].dropna().unique()
                for value in values:
                    if isinstance(value, str) and len(value) > 3:
                        result['project_names'].append(clean_text(value))
        
        # 搜索财务数据相关列
        financial_keywords = ['amount', 'value', 'price', 'cost', 'budget', '金额', '价格', '成本', '预算']
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in financial_keywords) and df[col].dtype in [np.float64, np.int64]:
                result['financial_data'].append({
                    'column': col,
                    'sum': float(df[col].sum()),
                    'mean': float(df[col].mean()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max())
                })
        
        return result


def process_excel(file_path: str, company_name: Optional[str] = None) -> Dict[str, Any]:
    """
    处理Excel文件，提取相关信息
    
    Args:
        file_path: Excel文件路径
        company_name: 相关公司名称（可选）
        
    Returns:
        提取的信息
    """
    processor = ExcelProcessor()
    
    try:
        # 读取Excel
        data = processor.read_excel(file_path)
        
        # 提取信息
        extracted_info = processor.extract_company_info(data)
        
        # 如果提供了公司名称，保存处理结果
        if company_name:
            storage = get_storage_manager()
            storage.save_company_data(
                company_name, 
                "document", 
                {
                    "source": "excel_upload",
                    "filename": os.path.basename(file_path),
                    "data": extracted_info
                }
            )
        
        return extracted_info
        
    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        return {
            "error": str(e),
            "filename": os.path.basename(file_path)
        }


if __name__ == "__main__":
    # 测试代码
    test_file = "example.xlsx"  # 替换为实际的测试文件路径
    if os.path.exists(test_file):
        result = process_excel(test_file)
        print(f"Processed Excel file with {result.get('sheets_count', 1)} sheet(s)")
        if 'company_info' in result:
            print(f"Extracted company names: {result['company_info']['company_names']}")
    else:
        print(f"Test file {test_file} not found") 