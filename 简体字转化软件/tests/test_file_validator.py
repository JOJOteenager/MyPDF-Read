"""
FileValidator属性测试
Feature: word-traditional-to-simplified
"""
import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path

from src.file_validator import FileValidator


# 支持的扩展名
SUPPORTED_EXTENSIONS = ['.docx', '.doc']
# 不支持的扩展名示例
UNSUPPORTED_EXTENSIONS = ['.txt', '.pdf', '.xlsx', '.pptx', '.html', '.xml', '.json', '.csv', '.rtf', '.odt']


class TestFileValidatorProperties:
    """FileValidator属性测试类"""
    
    @given(
        filename=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-', min_size=1, max_size=20),
        extension=st.sampled_from(SUPPORTED_EXTENSIONS + UNSUPPORTED_EXTENSIONS)
    )
    @settings(max_examples=100)
    def test_property5_file_format_validation(self, filename, extension):
        """
        Property 5: 文件格式验证
        *For any* 文件路径，验证器应该正确识别.docx和.doc文件为有效格式，其他格式为无效。
        
        Tag: **Feature: word-traditional-to-simplified, Property 5: 文件格式验证**
        **Validates: Requirements 1.1**
        """
        file_path = Path(f"{filename}{extension}")
        
        is_supported = FileValidator.is_supported_format(file_path)
        
        if extension.lower() in ['.docx', '.doc']:
            assert is_supported is True, f"扩展名 {extension} 应该被支持"
        else:
            assert is_supported is False, f"扩展名 {extension} 不应该被支持"


class TestFileValidatorUnit:
    """FileValidator单元测试类"""
    
    def test_is_supported_format_docx(self):
        """测试.docx格式支持"""
        assert FileValidator.is_supported_format(Path("test.docx")) is True
        assert FileValidator.is_supported_format(Path("test.DOCX")) is True
    
    def test_is_supported_format_doc(self):
        """测试.doc格式支持"""
        assert FileValidator.is_supported_format(Path("test.doc")) is True
        assert FileValidator.is_supported_format(Path("test.DOC")) is True
    
    def test_is_supported_format_unsupported(self):
        """测试不支持的格式"""
        assert FileValidator.is_supported_format(Path("test.txt")) is False
        assert FileValidator.is_supported_format(Path("test.pdf")) is False
        assert FileValidator.is_supported_format(Path("test.xlsx")) is False
    
    def test_validate_nonexistent_file(self, tmp_path):
        """测试不存在的文件"""
        file_path = tmp_path / "nonexistent.docx"
        is_valid, error = FileValidator.validate(file_path)
        assert is_valid is False
        assert "文件不存在" in error
    
    def test_validate_directory(self, tmp_path):
        """测试目录路径"""
        is_valid, error = FileValidator.validate(tmp_path)
        assert is_valid is False
        assert "路径不是文件" in error
    
    def test_validate_unsupported_format(self, tmp_path):
        """测试不支持的格式"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")
        is_valid, error = FileValidator.validate(file_path)
        assert is_valid is False
        assert "不支持的文件格式" in error
    
    def test_validate_valid_docx(self, tmp_path):
        """测试有效的.docx文件"""
        file_path = tmp_path / "test.docx"
        file_path.write_bytes(b"test content")
        is_valid, error = FileValidator.validate(file_path)
        assert is_valid is True
        assert error == ""
    
    def test_validate_string_path(self, tmp_path):
        """测试字符串路径输入"""
        file_path = tmp_path / "test.docx"
        file_path.write_bytes(b"test content")
        is_valid, error = FileValidator.validate(str(file_path))
        assert is_valid is True
