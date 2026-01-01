"""
主窗口模块 - PyQt6主窗口，提供用户界面
"""
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QProgressBar,
    QLabel, QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from src.conversion_manager import ConversionManager, ConversionTask
from src.file_validator import FileValidator


class ConversionWorker(QThread):
    """转换工作线程，用于异步处理转换任务"""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, filename
    conversion_completed = pyqtSignal(list)  # List[ConversionTask]
    
    def __init__(self, manager: ConversionManager, output_dir: Optional[Path] = None):
        super().__init__()
        self._manager = manager
        self._output_dir = output_dir
    
    def run(self):
        """执行转换任务"""
        tasks = self._manager.start_conversion(
            output_dir=self._output_dir,
            progress_callback=self._on_progress
        )
        self.conversion_completed.emit(tasks)
    
    def _on_progress(self, current: int, total: int, filename: str):
        """进度回调"""
        self.progress_updated.emit(current, total, filename)


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号定义
    files_dropped = pyqtSignal(list)  # 文件拖拽信号
    conversion_requested = pyqtSignal()  # 转换请求信号
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化转换管理器
        self._manager = ConversionManager()
        self._worker: Optional[ConversionWorker] = None
        
        # 设置窗口属性
        self.setWindowTitle("Word繁体转简体转换工具")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        
        # 设置接受拖拽
        self.setAcceptDrops(True)
        
        # 设置UI
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self) -> None:
        """设置UI组件"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("Word繁体转简体转换工具")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 文件列表区域
        file_frame = QFrame()
        file_frame.setObjectName("fileFrame")
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(10, 10, 10, 10)
        
        # 文件列表标签
        file_label = QLabel("待转换文件列表（支持拖拽添加）:")
        file_label.setObjectName("sectionLabel")
        file_layout.addWidget(file_label)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.setMinimumHeight(150)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        file_layout.addWidget(self.file_list)
        
        # 文件操作按钮
        file_btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加文件")
        self.add_btn.setObjectName("addButton")
        self.add_btn.clicked.connect(self._on_add_files)
        file_btn_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.setObjectName("removeButton")
        self.remove_btn.clicked.connect(self._on_remove_files)
        file_btn_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._on_clear_files)
        file_btn_layout.addWidget(self.clear_btn)
        
        file_btn_layout.addStretch()
        file_layout.addLayout(file_btn_layout)
        
        main_layout.addWidget(file_frame)
        
        # 进度显示区域
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 10, 10, 10)
        
        # 当前文件标签
        self.current_file_label = QLabel("准备就绪")
        self.current_file_label.setObjectName("currentFileLabel")
        progress_layout.addWidget(self.current_file_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(progress_frame)
        
        # 转换按钮
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("convertButton")
        self.convert_btn.setMinimumHeight(45)
        self.convert_btn.clicked.connect(self._on_start_conversion)
        main_layout.addWidget(self.convert_btn)
        
        # 状态栏
        self.statusBar().showMessage("请添加Word文档开始转换")

    def setup_styles(self) -> None:
        """设置样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            #titleLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
            
            #sectionLabel {
                font-size: 13px;
                color: #34495e;
                font-weight: 500;
            }
            
            #fileFrame, #progressFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            
            #fileList {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
                font-size: 12px;
            }
            
            #fileList::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            
            #fileList::item:selected {
                background-color: #3498db;
                color: white;
            }
            
            #fileList::item:hover {
                background-color: #ecf0f1;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            
            #addButton {
                background-color: #3498db;
                color: white;
                border: none;
            }
            
            #addButton:hover {
                background-color: #2980b9;
            }
            
            #addButton:pressed {
                background-color: #2472a4;
            }
            
            #removeButton {
                background-color: #e74c3c;
                color: white;
                border: none;
            }
            
            #removeButton:hover {
                background-color: #c0392b;
            }
            
            #clearButton {
                background-color: #95a5a6;
                color: white;
                border: none;
            }
            
            #clearButton:hover {
                background-color: #7f8c8d;
            }
            
            #convertButton {
                background-color: #27ae60;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            
            #convertButton:hover {
                background-color: #219a52;
            }
            
            #convertButton:pressed {
                background-color: #1e8449;
            }
            
            #convertButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            #currentFileLabel {
                font-size: 12px;
                color: #7f8c8d;
            }
            
            #progressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                height: 22px;
            }
            
            #progressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
            
            QStatusBar {
                background-color: #ecf0f1;
                color: #7f8c8d;
            }
        """)
    
    def add_files_to_list(self, file_paths: List[Path]) -> None:
        """添加文件到列表显示"""
        added = self._manager.add_files(file_paths)
        
        for file_path in added:
            item = QListWidgetItem(str(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.file_list.addItem(item)
        
        # 更新状态
        total = self.file_list.count()
        if total > 0:
            self.statusBar().showMessage(f"已添加 {total} 个文件")
        
        # 如果有重复文件，提示用户
        duplicates = len(file_paths) - len(added)
        if duplicates > 0:
            QMessageBox.information(
                self,
                "提示",
                f"已忽略 {duplicates} 个重复文件"
            )
    
    def update_progress(self, current: int, total: int, filename: str) -> None:
        """更新进度显示"""
        percentage = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.current_file_label.setText(f"正在处理 ({current}/{total}): {filename}")
    
    def show_completion(self, results: List[ConversionTask]) -> None:
        """显示完成信息"""
        # 重新启用按钮
        self._set_ui_enabled(True)
        self.progress_bar.setValue(100)
        
        # 统计结果
        success_count = sum(1 for t in results if t.status == "completed")
        failed_count = sum(1 for t in results if t.status == "failed")
        total_chars = sum(t.converted_chars for t in results)
        
        # 构建消息
        message = f"转换完成！\n\n成功: {success_count} 个文件\n"
        if failed_count > 0:
            message += f"失败: {failed_count} 个文件\n"
        message += f"共转换 {total_chars} 个字符"
        
        # 显示失败详情
        if failed_count > 0:
            message += "\n\n失败文件:"
            for task in results:
                if task.status == "failed":
                    message += f"\n- {task.input_path.name}: {task.error_message}"
        
        QMessageBox.information(self, "转换完成", message)
        
        # 重置进度
        self.current_file_label.setText("转换完成")
        self.statusBar().showMessage(f"转换完成: {success_count} 成功, {failed_count} 失败")
    
    def show_error(self, message: str) -> None:
        """显示错误信息"""
        QMessageBox.critical(self, "错误", message)
    
    def _on_add_files(self) -> None:
        """添加文件按钮点击事件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择Word文档",
            "",
            "Word文档 (*.docx *.doc);;所有文件 (*.*)"
        )
        
        if file_paths:
            self.add_files_to_list([Path(p) for p in file_paths])
    
    def _on_remove_files(self) -> None:
        """移除选中文件"""
        selected_items = self.file_list.selectedItems()
        
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            self._manager.remove_file(file_path)
            self.file_list.takeItem(self.file_list.row(item))
        
        total = self.file_list.count()
        self.statusBar().showMessage(f"剩余 {total} 个文件")
    
    def _on_clear_files(self) -> None:
        """清空文件列表"""
        if self.file_list.count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清空文件列表吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._manager.clear_files()
            self.file_list.clear()
            self.statusBar().showMessage("文件列表已清空")
            self.progress_bar.setValue(0)
            self.current_file_label.setText("准备就绪")

    def _on_start_conversion(self) -> None:
        """开始转换按钮点击事件"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "提示", "请先添加要转换的文件")
            return
        
        # 检查是否有文件会被覆盖
        files_to_overwrite = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            output_path = self._manager.get_default_output_path(file_path)
            if output_path.exists():
                files_to_overwrite.append(output_path.name)
        
        # 如果有文件会被覆盖，询问用户
        if files_to_overwrite:
            message = "以下文件已存在，是否覆盖？\n\n"
            message += "\n".join(files_to_overwrite[:5])
            if len(files_to_overwrite) > 5:
                message += f"\n... 等 {len(files_to_overwrite)} 个文件"
            
            reply = QMessageBox.question(
                self,
                "文件已存在",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 禁用UI
        self._set_ui_enabled(False)
        
        # 重置进度
        self.progress_bar.setValue(0)
        self.current_file_label.setText("正在准备...")
        
        # 创建并启动工作线程
        self._worker = ConversionWorker(self._manager)
        self._worker.progress_updated.connect(self.update_progress)
        self._worker.conversion_completed.connect(self._on_conversion_completed)
        self._worker.start()
        
        self.conversion_requested.emit()
    
    def _on_conversion_completed(self, tasks: List[ConversionTask]) -> None:
        """转换完成回调"""
        self.show_completion(tasks)
        self._worker = None
    
    def _set_ui_enabled(self, enabled: bool) -> None:
        """设置UI启用状态"""
        self.add_btn.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.convert_btn.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
    
    # 拖拽事件处理
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否有支持的文件
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if FileValidator.is_supported_format(file_path):
                        event.acceptProposedAction()
                        return
        event.ignore()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """拖拽放下事件"""
        file_paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = Path(url.toLocalFile())
                if FileValidator.is_supported_format(file_path):
                    file_paths.append(file_path)
        
        if file_paths:
            self.add_files_to_list(file_paths)
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()
