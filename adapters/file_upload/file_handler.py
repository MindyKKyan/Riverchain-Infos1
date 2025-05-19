"""
文件上传处理器 - File upload handler
"""
import os
import logging
import tempfile
from typing import Dict, List, Any, Optional, BinaryIO, Union, Tuple
import pandas as pd

# 移除sys.path修改，使用相对导入
from adapters.file_upload.pdf_processor import process_pdf
from adapters.file_upload.excel_processor import process_excel
from core.storage import get_storage_manager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('file_handler')

class FileHandler:
    """文件上传处理器"""
    
    def __init__(self):
        self.storage = get_storage_manager()
        self.allowed_extensions = {
            'pdf': ['.pdf'],
            'excel': ['.xlsx', '.xls', '.csv'],
            'text': ['.txt', '.md', '.json'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        }
    
    def get_file_type(self, filename: str) -> str:
        """
        根据文件名判断文件类型
        
        Args:
            filename: 文件名
            
        Returns:
            文件类型
        """
        ext = os.path.splitext(filename)[1].lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if ext in extensions:
                return file_type
        
        return 'unknown'
    
    def validate_file(self, filename: str) -> bool:
        """
        验证文件是否符合允许的类型
        
        Args:
            filename: 文件名
            
        Returns:
            是否是允许的文件类型
        """
        file_type = self.get_file_type(filename)
        return file_type != 'unknown'
    
    def save_uploaded_file(self, file_obj: BinaryIO, filename: str) -> str:
        """
        保存上传的文件
        
        Args:
            file_obj: 文件对象
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        # 确保上传目录存在
        upload_dir = os.path.join(self.storage.base_dir, "uploads")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 保存文件
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(file_obj.read())
        
        logger.info(f"Saved uploaded file to {file_path}")
        return file_path
    
    def process_file(self, file_path: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file_path: 文件路径
            company_name: 相关公司名称（可选）
            
        Returns:
            处理结果
        """
        filename = os.path.basename(file_path)
        file_type = self.get_file_type(filename)
        
        logger.info(f"Processing {file_type} file: {filename}")
        
        if file_type == 'pdf':
            return process_pdf(file_path, company_name)
        elif file_type == 'excel':
            return process_excel(file_path, company_name)
        elif file_type == 'text':
            # 简单文本处理，实际项目中可以更复杂
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = {
                'source': 'text_upload',
                'filename': filename,
                'content': content[:1000] + ('...' if len(content) > 1000 else '')
            }
            
            if company_name:
                self.storage.save_company_data(
                    company_name,
                    "document",
                    result
                )
            
            return result
        else:
            return {
                'source': 'unknown_upload',
                'filename': filename,
                'error': 'Unsupported file type'
            }
    
    def handle_uploaded_file(self, file_obj: BinaryIO, filename: str, 
                            company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file_obj: 文件对象
            filename: 文件名
            company_name: 相关公司名称（可选）
            
        Returns:
            处理结果
        """
        if not self.validate_file(filename):
            return {
                'success': False,
                'error': 'Invalid file type',
                'allowed_types': list(self.allowed_extensions.keys())
            }
        
        try:
            # 保存文件
            file_path = self.save_uploaded_file(file_obj, filename)
            
            # 处理文件
            result = self.process_file(file_path, company_name)
            
            return {
                'success': True,
                'file_type': self.get_file_type(filename),
                'filename': filename,
                'company_name': company_name,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error handling uploaded file: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def handle_uploaded_file(file_obj: BinaryIO, filename: str, 
                         company_name: Optional[str] = None) -> Dict[str, Any]:
    """
    处理上传的文件
    
    Args:
        file_obj: 文件对象
        filename: 文件名
        company_name: 相关公司名称（可选）
        
    Returns:
        处理结果
    """
    handler = FileHandler()
    return handler.handle_uploaded_file(file_obj, filename, company_name)


def process_temp_file(file_content: bytes, filename: str, 
                      company_name: Optional[str] = None) -> Dict[str, Any]:
    """
    处理临时文件内容
    
    Args:
        file_content: 文件内容字节
        filename: 文件名
        company_name: 相关公司名称（可选）
        
    Returns:
        处理结果
    """
    handler = FileHandler()
    
    if not handler.validate_file(filename):
        return {
            'success': False,
            'error': 'Invalid file type',
            'allowed_types': list(handler.allowed_extensions.keys())
        }
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        # 处理文件
        result = handler.process_file(temp_path, company_name)
        
        # 清理临时文件
        os.unlink(temp_path)
        
        return {
            'success': True,
            'file_type': handler.get_file_type(filename),
            'filename': filename,
            'company_name': company_name,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"Error processing temp file: {e}")
        return {
            'success': False,
            'error': str(e)
        } 