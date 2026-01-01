"""
中文转换器模块 - 负责繁体到简体的文字转换
"""
from opencc import OpenCC


class ChineseConverter:
    """繁体转简体转换器"""
    
    def __init__(self):
        """初始化OpenCC转换器，使用t2s（繁体到简体）配置"""
        self._converter = OpenCC('t2s')
    
    def convert(self, text: str) -> str:
        """
        将繁体中文转换为简体中文
        
        Args:
            text: 待转换的文本
            
        Returns:
            转换后的简体中文文本
        """
        if not text:
            return text
        return self._converter.convert(text)
    
    def is_traditional(self, char: str) -> bool:
        """
        判断字符是否为繁体字
        
        Args:
            char: 单个字符
            
        Returns:
            是否为繁体字
        """
        if not char or len(char) != 1:
            return False
        
        # 如果转换后与原字符不同，说明是繁体字
        converted = self._converter.convert(char)
        return converted != char
