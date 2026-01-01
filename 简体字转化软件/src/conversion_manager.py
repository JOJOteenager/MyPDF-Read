"""
转换管理器模块 - 协调文件处理流程，管理批量转换任务
"""
from pathlib import Path
from typing import List, Callable, Optional
from dataclasses import dataclass, field

from src.converter import ChineseConverter
from src.document_processor import DocumentProcessor, ProcessResult
from src.file_validator import FileValidator


@dataclass
class ConversionTask:
    """转换任务"""
    input_path: Path
    output_path: Path
    status: str = "pending"  # pending, processing, completed, failed
    error_message: str = ""
    converted_chars: int = 0


class ConversionManager:
    """转换管理器"""
    
    DEFAULT_OUTPUT_SUFFIX = "_简体"
    
    def __init__(self):
        """初始化转换管理器"""
        self._files: List[Path] = []
        self._converter = ChineseConverter()
        self._processor = DocumentProcessor(self._converter)
    
    def add_files(self, file_paths: List[Path]) -> List[Path]:
        """
        添加文件到转换队列
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            成功添加的文件路径列表（排除重复）
        """
        added = []
        for file_path in file_paths:
            # 确保是Path对象
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # 规范化路径以便比较
            normalized_path = file_path.resolve() if file_path.exists() else file_path
            
            # 检查是否已存在（去重）
            existing_paths = [p.resolve() if p.exists() else p for p in self._files]
            if normalized_path not in existing_paths:
                self._files.append(file_path)
                added.append(file_path)
        
        return added
    
    def remove_file(self, file_path: Path) -> bool:
        """
        从队列中移除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功移除
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # 尝试直接移除
        if file_path in self._files:
            self._files.remove(file_path)
            return True
        
        # 尝试通过规范化路径移除
        normalized_path = file_path.resolve() if file_path.exists() else file_path
        for i, existing in enumerate(self._files):
            existing_normalized = existing.resolve() if existing.exists() else existing
            if existing_normalized == normalized_path:
                self._files.pop(i)
                return True
        
        return False
    
    def clear_files(self) -> None:
        """清空文件队列"""
        self._files.clear()
    
    def get_files(self) -> List[Path]:
        """
        获取当前文件队列
        
        Returns:
            文件路径列表的副本
        """
        return self._files.copy()
    
    def get_default_output_path(self, input_path: Path) -> Path:
        """
        获取默认输出路径
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            添加"_简体"后缀的输出路径，扩展名为.docx
        """
        if isinstance(input_path, str):
            input_path = Path(input_path)
        
        # 获取文件名（不含扩展名）和目录
        stem = input_path.stem
        parent = input_path.parent
        
        # 生成新文件名：原名 + _简体 + .docx
        new_name = f"{stem}{self.DEFAULT_OUTPUT_SUFFIX}.docx"
        
        return parent / new_name

    def start_conversion(
        self,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        completion_callback: Optional[Callable[[List[ConversionTask]], None]] = None
    ) -> List[ConversionTask]:
        """
        开始批量转换
        
        Args:
            output_dir: 输出目录，None则保存到原文件目录
            progress_callback: 进度回调(当前文件索引, 总文件数, 当前文件名)
            completion_callback: 完成回调(任务列表)
            
        Returns:
            转换任务列表
        """
        tasks: List[ConversionTask] = []
        total_files = len(self._files)
        
        for index, input_path in enumerate(self._files):
            # 确定输出路径
            if output_dir:
                if isinstance(output_dir, str):
                    output_dir = Path(output_dir)
                output_path = output_dir / f"{input_path.stem}{self.DEFAULT_OUTPUT_SUFFIX}.docx"
            else:
                output_path = self.get_default_output_path(input_path)
            
            # 创建任务
            task = ConversionTask(
                input_path=input_path,
                output_path=output_path,
                status="processing"
            )
            tasks.append(task)
            
            # 调用进度回调
            if progress_callback:
                progress_callback(index + 1, total_files, input_path.name)
            
            # 验证文件
            is_valid, error_msg = FileValidator.validate(input_path)
            if not is_valid:
                task.status = "failed"
                task.error_message = error_msg
                continue
            
            # 执行转换
            result = self._processor.process_document(input_path, output_path)
            
            if result.success:
                task.status = "completed"
                task.converted_chars = result.converted_chars
            else:
                task.status = "failed"
                task.error_message = result.error_message
        
        # 调用完成回调
        if completion_callback:
            completion_callback(tasks)
        
        return tasks
