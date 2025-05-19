"""
存储控制器 - Data storage and management
"""
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('storage')

class StorageManager:
    """存储管理器，负责数据的保存、读取和管理"""
    
    def __init__(self, base_dir: str = "data"):
        """
        初始化存储管理器
        
        Args:
            base_dir: 数据存储的基础目录
        """
        self.base_dir = base_dir
        self._ensure_directory_exists(self.base_dir)
        self._ensure_directory_exists(os.path.join(self.base_dir, "companies"))
        self._ensure_directory_exists(os.path.join(self.base_dir, "raw"))
        self._ensure_directory_exists(os.path.join(self.base_dir, "processed"))
        logger.info(f"Storage manager initialized with base directory: {base_dir}")
    
    def _ensure_directory_exists(self, directory: str) -> None:
        """确保目录存在，不存在则创建"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.debug(f"Created directory: {directory}")
    
    def _get_company_dir(self, company_name: str) -> str:
        """获取公司数据存储目录"""
        company_dir = os.path.join(self.base_dir, "companies", company_name)
        self._ensure_directory_exists(company_dir)
        return company_dir
    
    def save_company_data(self, company_name: str, data_type: str, data: Union[Dict, List, pd.DataFrame]) -> str:
        """
        保存公司相关数据
        
        Args:
            company_name: 公司名称
            data_type: 数据类型 (news, social, gov, industry)
            data: 要保存的数据
            
        Returns:
            保存的文件路径
        """
        company_dir = self._get_company_dir(company_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 确保数据类型目录存在
        data_type_dir = os.path.join(company_dir, data_type)
        self._ensure_directory_exists(data_type_dir)
        
        # 根据数据类型选择保存格式
        if isinstance(data, pd.DataFrame):
            file_path = os.path.join(data_type_dir, f"{timestamp}.csv")
            data.to_csv(file_path, index=False, encoding='utf-8')
        else:
            file_path = os.path.join(data_type_dir, f"{timestamp}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {data_type} data for {company_name} to {file_path}")
        return file_path
    
    def load_company_data(self, company_name: str, data_type: str = None, latest_only: bool = True) -> Dict[str, Any]:
        """
        加载公司数据
        
        Args:
            company_name: 公司名称
            data_type: 数据类型，如果为None则加载所有类型
            latest_only: 是否只加载最新数据
            
        Returns:
            加载的数据字典
        """
        company_dir = self._get_company_dir(company_name)
        result = {}
        
        # 确定要加载的数据类型
        data_types = [data_type] if data_type else os.listdir(company_dir)
        
        for dt in data_types:
            dt_path = os.path.join(company_dir, dt)
            if not os.path.isdir(dt_path):
                continue
                
            files = sorted(os.listdir(dt_path), reverse=True)  # 按名称排序，最新的在前面
            
            if not files:
                continue
                
            if latest_only:
                files = [files[0]]  # 只取最新的文件
            
            dt_data = []
            for file in files:
                file_path = os.path.join(dt_path, file)
                if file.endswith('.json'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        dt_data.append(json.load(f))
                elif file.endswith('.csv'):
                    dt_data.append(pd.read_csv(file_path, encoding='utf-8'))
            
            result[dt] = dt_data[0] if latest_only else dt_data
        
        return result
    
    def save_raw_data(self, source: str, data: Any, company_name: Optional[str] = None) -> str:
        """
        保存原始数据
        
        Args:
            source: 数据源名称
            data: 原始数据
            company_name: 相关公司名称（可选）
            
        Returns:
            保存的文件路径
        """
        raw_dir = os.path.join(self.base_dir, "raw")
        self._ensure_directory_exists(raw_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source}_{timestamp}"
        if company_name:
            filename = f"{company_name}_{filename}"
        
        if isinstance(data, pd.DataFrame):
            file_path = os.path.join(raw_dir, f"{filename}.csv")
            data.to_csv(file_path, index=False, encoding='utf-8')
        elif isinstance(data, (dict, list)):
            file_path = os.path.join(raw_dir, f"{filename}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif isinstance(data, str):
            file_path = os.path.join(raw_dir, f"{filename}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)
        else:
            file_path = os.path.join(raw_dir, f"{filename}.bin")
            with open(file_path, 'wb') as f:
                f.write(data)
        
        logger.info(f"Saved raw data from {source} to {file_path}")
        return file_path
        

# 创建默认实例供模块内使用
default_manager = StorageManager()

def get_storage_manager() -> StorageManager:
    """获取默认的存储管理器实例"""
    return default_manager 