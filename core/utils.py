"""
通用工具函数 - Common utility functions
"""
import re
import unicodedata
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('utils')

def normalize_company_name(name: str) -> str:
    """
    标准化公司名称，移除特殊字符，转为小写
    
    Args:
        name: 原始公司名称
        
    Returns:
        标准化后的公司名称
    """
    # 移除公司类型后缀
    name = re.sub(r'\s+(Limited|Ltd\.?|LLC|Inc\.?|Corporation|Corp\.?|Co\.?|Company|Group|Holdings|HK)$', '', name, flags=re.IGNORECASE)
    
    # 移除中文公司后缀
    name = re.sub(r'(香港|有限公司|集团|控股)$', '', name)
    
    # 标准化字符
    name = unicodedata.normalize('NFKC', name)
    
    # 移除特殊字符
    name = re.sub(r'[^\w\s]', '', name)
    
    # 转为小写并去除首尾空格
    name = name.lower().strip()
    
    return name

def extract_domain(url: str) -> str:
    """
    从URL中提取域名
    
    Args:
        url: 完整URL
        
    Returns:
        域名
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    # 移除www前缀
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def clean_text(text: str) -> str:
    """
    清理文本，移除多余空白字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 替换HTML标签
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 替换多个空白字符为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    # 移除首尾空白
    return text.strip()

def format_date(date_str: str, input_format: Optional[str] = None) -> str:
    """
    格式化日期为统一格式 (YYYY-MM-DD)
    
    Args:
        date_str: 原始日期字符串
        input_format: 输入日期格式，如果为None则尝试自动检测
        
    Returns:
        格式化后的日期字符串
    """
    if not date_str:
        return ""
    
    if input_format:
        try:
            dt = datetime.strptime(date_str, input_format)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            logger.warning(f"Failed to parse date: {date_str} with format {input_format}")
            return date_str
    
    # 常见日期格式
    formats = [
        '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
        '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
        '%b %d, %Y', '%d %b %Y', '%B %d, %Y',
        '%d %B %Y', '%Y年%m月%d日', '%d.%m.%Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # 无法解析，返回原始字符串
    logger.warning(f"Could not parse date: {date_str}")
    return date_str

def get_absolute_url(base_url: str, relative_url: str) -> str:
    """
    将相对URL转换为绝对URL
    
    Args:
        base_url: 基础URL
        relative_url: 相对URL
        
    Returns:
        绝对URL
    """
    return urljoin(base_url, relative_url)

def create_search_query(company_name: str, industry: str = "construction") -> str:
    """
    创建搜索查询字符串
    
    Args:
        company_name: 公司名称
        industry: 行业类型
        
    Returns:
        搜索查询字符串
    """
    return f'"{company_name}" {industry} hong kong' 