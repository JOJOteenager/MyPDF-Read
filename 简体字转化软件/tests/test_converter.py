"""
ChineseConverter属性测试
Feature: word-traditional-to-simplified
"""
import pytest
from hypothesis import given, strategies as st, settings

from src.converter import ChineseConverter


# 繁体字符范围（常用繁体字）
TRADITIONAL_CHARS = "繁體國語學習電腦網絡開發軟體設計圖書館機場飛機車輛運輸經濟貿易銀行醫院藥品環境資源農業漁業礦業製造業服務業"
# 简体字符范围（常用简体字）
SIMPLIFIED_CHARS = "简体国语学习电脑网络开发软件设计图书馆机场飞机车辆运输经济贸易银行医院药品环境资源农业渔业矿业制造业服务业"


@pytest.fixture
def converter():
    """创建转换器实例"""
    return ChineseConverter()


class TestChineseConverterProperties:
    """ChineseConverter属性测试类"""
    
    @given(st.text(alphabet=TRADITIONAL_CHARS, min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_property1_traditional_to_simplified_conversion(self, text):
        """
        Property 1: 繁简转换正确性
        *For any* 繁体中文文本，转换后的文本应该是对应的简体中文，且原有的简体字符保持不变。
        
        Tag: **Feature: word-traditional-to-simplified, Property 1: 繁简转换正确性**
        **Validates: Requirements 2.1, 2.4**
        """
        converter = ChineseConverter()
        result = converter.convert(text)
        
        # 转换后的文本不应包含原繁体字（除非无对应简体）
        # 验证：转换结果长度应与原文相同
        assert len(result) == len(text)
        
        # 验证：转换后的每个字符要么是简体，要么与原字符相同（无对应简体的情况）
        for i, (orig, conv) in enumerate(zip(text, result)):
            # 如果原字符是繁体，转换后应该不同或相同（无对应简体）
            if converter.is_traditional(orig):
                # 转换后不应该还是繁体（除非无对应简体）
                pass  # OpenCC会处理这种情况
            # 转换后的字符不应该是繁体
            assert not converter.is_traditional(conv), f"字符 '{conv}' 在位置 {i} 仍是繁体"
    
    @given(st.text(alphabet=SIMPLIFIED_CHARS, min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_property4_conversion_idempotence(self, text):
        """
        Property 4: 转换幂等性
        *For any* 纯简体中文文本，对其进行繁简转换后，结果应该与原文本完全相同（转换是幂等的）。
        
        Tag: **Feature: word-traditional-to-simplified, Property 4: 转换幂等性**
        **Validates: Requirements 2.4**
        """
        converter = ChineseConverter()
        result = converter.convert(text)
        
        # 简体文本转换后应该与原文完全相同
        assert result == text, f"简体文本 '{text}' 转换后变为 '{result}'，应保持不变"


class TestChineseConverterUnit:
    """ChineseConverter单元测试类"""
    
    def test_convert_empty_string(self, converter):
        """测试空字符串转换"""
        assert converter.convert("") == ""
    
    def test_convert_traditional_text(self, converter):
        """测试繁体文本转换"""
        assert converter.convert("繁體中文") == "繁体中文"
        assert converter.convert("電腦軟體") == "电脑软体"  # 軟體→软体（字符级转换）
    
    def test_convert_simplified_text(self, converter):
        """测试简体文本保持不变"""
        assert converter.convert("简体中文") == "简体中文"
    
    def test_convert_mixed_text(self, converter):
        """测试混合文本转换"""
        assert converter.convert("繁體和简体混合") == "繁体和简体混合"
    
    def test_is_traditional_true(self, converter):
        """测试繁体字识别"""
        assert converter.is_traditional("體") is True
        assert converter.is_traditional("國") is True
    
    def test_is_traditional_false(self, converter):
        """测试简体字识别"""
        assert converter.is_traditional("体") is False
        assert converter.is_traditional("国") is False
    
    def test_is_traditional_empty(self, converter):
        """测试空字符"""
        assert converter.is_traditional("") is False
    
    def test_is_traditional_multiple_chars(self, converter):
        """测试多字符输入"""
        assert converter.is_traditional("繁體") is False  # 只接受单字符
