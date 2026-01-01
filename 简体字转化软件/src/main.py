"""
应用入口点 - 初始化应用和主窗口

Word繁体转简体转换工具
- 支持.docx和.doc格式
- 保留文档格式和非文本元素
- 批量转换功能
"""
import sys
import logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from src.main_window import MainWindow


def get_log_dir() -> Path:
    """获取日志目录路径"""
    # 优先使用用户目录下的日志文件夹
    user_log_dir = Path.home() / ".word-converter" / "logs"
    try:
        user_log_dir.mkdir(parents=True, exist_ok=True)
        return user_log_dir
    except (PermissionError, OSError):
        # 如果无法创建用户目录，使用当前目录
        local_log_dir = Path("logs")
        local_log_dir.mkdir(exist_ok=True)
        return local_log_dir


def setup_logging() -> logging.Logger:
    """
    配置日志记录
    
    Returns:
        配置好的logger实例
    """
    log_dir = get_log_dir()
    
    # 创建带日期的日志文件名
    log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
    log_file = log_dir / log_filename
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 获取应用专用logger
    logger = logging.getLogger("word-converter")
    logger.setLevel(logging.INFO)
    
    return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许Ctrl+C正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger("word-converter")
    logger.critical("未捕获的异常", exc_info=(exc_type, exc_value, exc_traceback))


def main():
    """主函数 - 应用入口点"""
    # 配置日志
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("Word繁体转简体转换工具启动")
    logger.info(f"Python版本: {sys.version}")
    
    # 设置全局异常处理
    sys.excepthook = handle_exception
    
    try:
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("Word繁体转简体转换工具")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("WordConverter")
        
        # 设置高DPI支持
        app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        logger.info("QApplication已创建")
        
        # 创建并显示主窗口
        window = MainWindow()
        window.show()
        
        logger.info("主窗口已显示，应用准备就绪")
        
        # 运行应用
        exit_code = app.exec()
        
        logger.info(f"应用正常退出，退出码: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"应用启动失败: {e}", exc_info=True)
        # 尝试显示错误对话框
        try:
            QMessageBox.critical(
                None,
                "启动错误",
                f"应用启动失败:\n{str(e)}\n\n请检查日志文件获取详细信息。"
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
