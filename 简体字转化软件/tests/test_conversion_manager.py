"""
ConversionManager属性测试
Feature: word-traditional-to-simplified
"""
import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path

from src.conversion_manager import ConversionManager, ConversionTask


# 有效的文件名字符
VALID_FILENAME_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
# 支持的扩展名
SUPPORTED_EXTENSIONS = ['.docx', '.doc']


class TestConversionManagerProperties:
    """ConversionManager属性测试类"""
    
    @given(
        filenames=st.lists(
            st.text(alphabet=VALID_FILENAME_CHARS, min_size=1, max_size=20),
            min_size=1,
            max_size=10
        ),
        extension=st.sampled_from(SUPPORTED_EXTENSIONS)
    )
    @settings(max_examples=100)
    def test_property2_file_deduplication(self, filenames, extension):
        """
        Property 2: 文件去重
        *For any* 文件列表和任意新文件路径，如果该文件路径已存在于列表中，则添加操作后列表长度不变。
        
        Tag: **Feature: word-traditional-to-simplified, Property 2: 文件去重**
        **Validates: Requirements 1.4**
        """
        manager = ConversionManager()
        
        # 创建文件路径列表
        file_paths = [Path(f"{name}{extension}") for name in filenames]
        
        # 添加所有文件
        manager.add_files(file_paths)
        initial_count = len(manager.get_files())
        
        # 尝试再次添加相同的文件
        manager.add_files(file_paths)
        final_count = len(manager.get_files())
        
        # 验证：重复添加后列表长度不变
        assert final_count == initial_count, \
            f"重复添加文件后列表长度从 {initial_count} 变为 {final_count}，应保持不变"
    
    @given(
        filename=st.text(alphabet=VALID_FILENAME_CHARS, min_size=1, max_size=20),
        extension=st.sampled_from(SUPPORTED_EXTENSIONS),
        directory=st.text(alphabet=VALID_FILENAME_CHARS, min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_property3_default_output_path_generation(self, filename, extension, directory):
        """
        Property 3: 默认输出路径生成
        *For any* 有效的输入文件路径，生成的默认输出路径应该是原目录下的同名文件加上"_简体"后缀，且扩展名为.docx。
        
        Tag: **Feature: word-traditional-to-simplified, Property 3: 默认输出路径生成**
        **Validates: Requirements 3.3**
        """
        manager = ConversionManager()
        
        # 创建输入路径
        input_path = Path(directory) / f"{filename}{extension}"
        
        # 获取默认输出路径
        output_path = manager.get_default_output_path(input_path)
        
        # 验证1：输出路径在同一目录下
        assert output_path.parent == input_path.parent, \
            f"输出目录 {output_path.parent} 应与输入目录 {input_path.parent} 相同"
        
        # 验证2：输出文件名包含"_简体"后缀
        assert "_简体" in output_path.stem, \
            f"输出文件名 {output_path.stem} 应包含 '_简体' 后缀"
        
        # 验证3：输出扩展名为.docx
        assert output_path.suffix == ".docx", \
            f"输出扩展名 {output_path.suffix} 应为 .docx"
        
        # 验证4：输出文件名格式正确（原名 + _简体）
        expected_stem = f"{filename}_简体"
        assert output_path.stem == expected_stem, \
            f"输出文件名 {output_path.stem} 应为 {expected_stem}"


class TestConversionManagerUnit:
    """ConversionManager单元测试类"""
    
    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        return ConversionManager()
    
    def test_add_files_empty_list(self, manager):
        """测试添加空列表"""
        added = manager.add_files([])
        assert added == []
        assert manager.get_files() == []
    
    def test_add_files_single_file(self, manager):
        """测试添加单个文件"""
        file_path = Path("test.docx")
        added = manager.add_files([file_path])
        assert len(added) == 1
        assert file_path in manager.get_files()
    
    def test_add_files_multiple_files(self, manager):
        """测试添加多个文件"""
        files = [Path("test1.docx"), Path("test2.doc"), Path("test3.docx")]
        added = manager.add_files(files)
        assert len(added) == 3
        assert len(manager.get_files()) == 3
    
    def test_add_files_duplicate_ignored(self, manager):
        """测试重复文件被忽略"""
        file_path = Path("test.docx")
        manager.add_files([file_path])
        added = manager.add_files([file_path])
        assert len(added) == 0
        assert len(manager.get_files()) == 1
    
    def test_remove_file_existing(self, manager):
        """测试移除存在的文件"""
        file_path = Path("test.docx")
        manager.add_files([file_path])
        result = manager.remove_file(file_path)
        assert result is True
        assert file_path not in manager.get_files()
    
    def test_remove_file_nonexistent(self, manager):
        """测试移除不存在的文件"""
        result = manager.remove_file(Path("nonexistent.docx"))
        assert result is False
    
    def test_clear_files(self, manager):
        """测试清空文件列表"""
        files = [Path("test1.docx"), Path("test2.docx")]
        manager.add_files(files)
        manager.clear_files()
        assert manager.get_files() == []
    
    def test_get_default_output_path_docx(self, manager):
        """测试.docx文件的默认输出路径"""
        input_path = Path("documents/report.docx")
        output_path = manager.get_default_output_path(input_path)
        assert output_path == Path("documents/report_简体.docx")
    
    def test_get_default_output_path_doc(self, manager):
        """测试.doc文件的默认输出路径"""
        input_path = Path("documents/report.doc")
        output_path = manager.get_default_output_path(input_path)
        assert output_path == Path("documents/report_简体.docx")
    
    def test_get_default_output_path_string_input(self, manager):
        """测试字符串路径输入"""
        output_path = manager.get_default_output_path("test.docx")
        assert output_path == Path("test_简体.docx")
