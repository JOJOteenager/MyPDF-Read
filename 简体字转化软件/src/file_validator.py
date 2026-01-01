"""
文件验证器模块 - 负责验证文件格式和可访问性
"""
from pathlib import Path
from typing import Tuple


class FileValidator:
    """文件验证器"""
    
    SUPPORTED_EXTENSIONS = {'.docx', '.doc'}
    
    @staticmethod
    def validate(file_path: Path) -> Tuple[bool, str]:
        """
        验证文件是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        # 确保是Path对象
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # 检查文件是否存在
        if not file_path.exists():
            return False, f"文件不存在: {file_path}"
        
        # 检查是否是文件（而非目录）
        if not file_path.is_file():
            return False, f"路径不是文件: {file_path}"
        
        # 检查文件格式
        if not FileValidator.is_supported_format(file_path):
            return False, f"不支持的文件格式: {file_path.suffix}，仅支持 .docx 和 .doc 格式"
        
        # 检查文件是否可读
        try:
            with open(file_path, 'rb') as f:
                f.read(1)
        except PermissionError:
            return False, f"文件无法访问（权限不足）: {file_path}"
        except Exception as e:
            return False, f"文件无法读取: {e}"
        
        return True, ""
    
    @staticmethod
    def is_supported_format(file_path: Path) -> bool:
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为支持的格式
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        return file_path.suffix.lower() in FileValidator.SUPPORTED_EXTENSIONS
