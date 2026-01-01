"""
华为平板PDF阅读器 - 设置视图

实现阅读设置、手写笔设置和备份设置。
Requirements: 8.1-8.7, 10.1-10.7, 11.1-11.7
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty,
    ListProperty, NumericProperty
)
from typing import Optional, Callable, List

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME
from huawei_pdf_reader.models import (
    Settings, ReadingConfig, StylusConfig, ToolsConfig, 
    BackupConfig, BackupProvider
)


class SettingItem(BoxLayout):
    """设置项基类"""
    
    title = StringProperty("")
    description = StringProperty("")
    
    def __init__(self, title: str = "", description: str = "",
                 theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 60
        self.padding = [15, 10]
        self.spacing = 10
        
        self.title = title
        self.description = description
        self._theme = theme
        self._setup_base_ui()
    
    def _setup_base_ui(self):
        """设置基础UI"""
        # 文字区域
        text_layout = BoxLayout(orientation='vertical')
        
        title_label = Label(
            text=self.title,
            color=self._theme.text_primary,
            font_size='14sp',
            halign='left',
            valign='bottom',
            size_hint_y=0.6
        )
        title_label.bind(size=title_label.setter('text_size'))
        text_layout.add_widget(title_label)
        
        if self.description:
            desc_label = Label(
                text=self.description,
                color=self._theme.text_secondary,
                font_size='11sp',
                halign='left',
                valign='top',
                size_hint_y=0.4
            )
            desc_label.bind(size=desc_label.setter('text_size'))
            text_layout.add_widget(desc_label)
        
        self.add_widget(text_layout)


class SwitchSettingItem(SettingItem):
    """开关设置项"""
    
    value = BooleanProperty(False)
    on_change = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        self.value = kwargs.pop('value', False)
        self.on_change = kwargs.pop('on_change', None)
        super().__init__(**kwargs)
        self._setup_switch()
    
    def _setup_switch(self):
        self._switch = Switch(
            active=self.value,
            size_hint_x=None,
            width=60
        )
        self._switch.bind(active=self._on_switch_change)
        self.add_widget(self._switch)
    
    def _on_switch_change(self, instance, value):
        self.value = value
        if self.on_change:
            self.on_change(value)


class SliderSettingItem(SettingItem):
    """滑块设置项"""
    
    value = NumericProperty(5)
    min_value = NumericProperty(1)
    max_value = NumericProperty(10)
    on_change = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        self.value = kwargs.pop('value', 5)
        self.min_value = kwargs.pop('min_value', 1)
        self.max_value = kwargs.pop('max_value', 10)
        self.on_change = kwargs.pop('on_change', None)
        super().__init__(**kwargs)
        self._setup_slider()
    
    def _setup_slider(self):
        slider_layout = BoxLayout(size_hint_x=None, width=150, spacing=5)
        
        self._slider = Slider(
            min=self.min_value,
            max=self.max_value,
            value=self.value
        )
        self._slider.bind(value=self._on_slider_change)
        slider_layout.add_widget(self._slider)
        
        self._value_label = Label(
            text=str(int(self.value)),
            size_hint_x=None,
            width=30,
            color=self._theme.text_secondary
        )
        slider_layout.add_widget(self._value_label)
        
        self.add_widget(slider_layout)
    
    def _on_slider_change(self, instance, value):
        self.value = value
        self._value_label.text = str(int(value))
        if self.on_change:
            self.on_change(value)


class SpinnerSettingItem(SettingItem):
    """下拉选择设置项"""
    
    value = StringProperty("")
    options = ListProperty([])
    on_change = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        self.value = kwargs.pop('value', "")
        self.options = kwargs.pop('options', [])
        self.on_change = kwargs.pop('on_change', None)
        super().__init__(**kwargs)
        self._setup_spinner()
    
    def _setup_spinner(self):
        self._spinner = Spinner(
            text=self.value,
            values=self.options,
            size_hint_x=None,
            width=150,
            background_color=self._theme.surface,
            color=self._theme.text_primary
        )
        self._spinner.bind(text=self._on_spinner_change)
        self.add_widget(self._spinner)
    
    def _on_spinner_change(self, instance, value):
        self.value = value
        if self.on_change:
            self.on_change(value)


class ButtonSettingItem(SettingItem):
    """按钮设置项"""
    
    button_text = StringProperty("操作")
    on_click = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        self.button_text = kwargs.pop('button_text', "操作")
        self.on_click = kwargs.pop('on_click', None)
        super().__init__(**kwargs)
        self._setup_button()
    
    def _setup_button(self):
        self._button = Button(
            text=self.button_text,
            size_hint_x=None,
            width=100,
            background_color=self._theme.primary_color,
            color=self._theme.text_primary
        )
        self._button.bind(on_press=lambda x: self.on_click and self.on_click())
        self.add_widget(self._button)


class SettingSection(BoxLayout):
    """设置分组"""
    
    title = StringProperty("")
    
    def __init__(self, title: str = "", theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing = 2
        self.padding = [0, 10, 0, 0]
        
        self.title = title
        self._theme = theme
        self._items: List[Widget] = []
        self._setup_header()
        
        self.bind(minimum_height=self.setter('height'))
    
    def _setup_header(self):
        """设置标题"""
        header = Label(
            text=self.title,
            size_hint_y=None,
            height=35,
            color=self._theme.accent,
            font_size='13sp',
            halign='left',
            valign='middle',
            padding=[15, 0]
        )
        header.bind(size=header.setter('text_size'))
        self.add_widget(header)
    
    def add_item(self, item: Widget):
        """添加设置项"""
        self._items.append(item)
        self.add_widget(item)
        self._update_height()
    
    def _update_height(self):
        """更新高度"""
        total = 35  # header height
        for item in self._items:
            total += item.height + 2
        self.height = total


class ReadingSettingsSection(SettingSection):
    """阅读设置分组
    
    Requirements: 8.1-8.7
    """
    
    config = ObjectProperty(None)
    on_config_change = ObjectProperty(None)
    
    def __init__(self, config: ReadingConfig, **kwargs):
        self.config = config
        super().__init__(title="阅读设置", **kwargs)
        self._setup_items()
    
    def _setup_items(self):
        """设置项目"""
        # 8.1 翻页方向
        self.add_item(SpinnerSettingItem(
            title="翻页方向",
            description="选择横向或纵向翻页",
            value="纵向" if self.config.page_direction == "vertical" else "横向",
            options=["纵向", "横向"],
            theme=self._theme,
            on_change=lambda v: self._update_config('page_direction', 'vertical' if v == "纵向" else 'horizontal')
        ))
        
        # 8.2 双页浏览
        self.add_item(SwitchSettingItem(
            title="双页浏览",
            description="并排显示两页内容",
            value=self.config.dual_page,
            theme=self._theme,
            on_change=lambda v: self._update_config('dual_page', v)
        ))
        
        # 8.3 连续滚动
        self.add_item(SwitchSettingItem(
            title="连续滚动",
            description="以连续滚动方式显示文档",
            value=self.config.continuous_scroll,
            theme=self._theme,
            on_change=lambda v: self._update_config('continuous_scroll', v)
        ))
        
        # 8.4 工具栏位置
        self.add_item(SpinnerSettingItem(
            title="工具栏位置",
            value=self._get_toolbar_position_text(),
            options=["顶部", "底部", "左侧", "右侧"],
            theme=self._theme,
            on_change=self._on_toolbar_position_change
        ))
        
        # 8.5 护眼模式
        self.add_item(SwitchSettingItem(
            title="护眼模式",
            description="应用暖色滤镜减少蓝光",
            value=self.config.eye_protection,
            theme=self._theme,
            on_change=lambda v: self._update_config('eye_protection', v)
        ))
        
        # 8.6 保持屏幕常亮
        self.add_item(SwitchSettingItem(
            title="保持屏幕常亮",
            description="阻止屏幕自动休眠",
            value=self.config.keep_screen_on,
            theme=self._theme,
            on_change=lambda v: self._update_config('keep_screen_on', v)
        ))
    
    def _get_toolbar_position_text(self) -> str:
        positions = {"top": "顶部", "bottom": "底部", "left": "左侧", "right": "右侧"}
        return positions.get(self.config.toolbar_position, "顶部")
    
    def _on_toolbar_position_change(self, value: str):
        positions = {"顶部": "top", "底部": "bottom", "左侧": "left", "右侧": "right"}
        self._update_config('toolbar_position', positions.get(value, "top"))
    
    def _update_config(self, key: str, value):
        setattr(self.config, key, value)
        if self.on_config_change:
            self.on_config_change(self.config)


class StylusSettingsSection(SettingSection):
    """手写笔设置分组
    
    Requirements: 10.1-10.7
    """
    
    config = ObjectProperty(None)
    on_config_change = ObjectProperty(None)
    
    # 可用的动作选项
    ACTION_OPTIONS = ["无", "橡皮擦", "选择文本", "撤销", "重做", "截图", "切换工具"]
    
    def __init__(self, config: StylusConfig, **kwargs):
        self.config = config
        super().__init__(title="手写笔设置", **kwargs)
        self._setup_items()
    
    def _setup_items(self):
        """设置项目"""
        # 10.1 触控笔双击
        self.add_item(SpinnerSettingItem(
            title="触控笔双击",
            description="双击时执行的操作",
            value=self._action_to_text(self.config.double_tap),
            options=self.ACTION_OPTIONS,
            theme=self._theme,
            on_change=lambda v: self._update_config('double_tap', self._text_to_action(v))
        ))
        
        # 10.2 按键长按
        self.add_item(SpinnerSettingItem(
            title="按键长按",
            description="长按时执行的操作",
            value=self._action_to_text(self.config.long_press),
            options=self.ACTION_OPTIONS,
            theme=self._theme,
            on_change=lambda v: self._update_config('long_press', self._text_to_action(v))
        ))
        
        # 10.3 主键单击
        self.add_item(SpinnerSettingItem(
            title="主键单击",
            description="单击时执行的操作",
            value=self._action_to_text(self.config.primary_click),
            options=self.ACTION_OPTIONS,
            theme=self._theme,
            on_change=lambda v: self._update_config('primary_click', self._text_to_action(v))
        ))
        
        # 10.4 副键单击
        self.add_item(SpinnerSettingItem(
            title="副键单击",
            description="副键单击时执行的操作",
            value=self._action_to_text(self.config.secondary_click),
            options=self.ACTION_OPTIONS,
            theme=self._theme,
            on_change=lambda v: self._update_config('secondary_click', self._text_to_action(v))
        ))
        
        # 防误触灵敏度
        self.add_item(SliderSettingItem(
            title="防误触灵敏度",
            description="调整防误触检测的灵敏度",
            value=self.config.palm_rejection_sensitivity,
            min_value=1,
            max_value=10,
            theme=self._theme,
            on_change=lambda v: self._update_config('palm_rejection_sensitivity', int(v))
        ))
    
    def _action_to_text(self, action: str) -> str:
        mapping = {
            "none": "无", "eraser": "橡皮擦", "select_text": "选择文本",
            "undo": "撤销", "redo": "重做", "screenshot": "截图", "switch_tool": "切换工具"
        }
        return mapping.get(action, "无")
    
    def _text_to_action(self, text: str) -> str:
        mapping = {
            "无": "none", "橡皮擦": "eraser", "选择文本": "select_text",
            "撤销": "undo", "重做": "redo", "截图": "screenshot", "切换工具": "switch_tool"
        }
        return mapping.get(text, "none")
    
    def _update_config(self, key: str, value):
        setattr(self.config, key, value)
        if self.on_config_change:
            self.on_config_change(self.config)


class BackupSettingsSection(SettingSection):
    """备份设置分组
    
    Requirements: 11.1-11.7
    """
    
    config = ObjectProperty(None)
    on_config_change = ObjectProperty(None)
    on_backup = ObjectProperty(None)
    on_restore = ObjectProperty(None)
    on_bind_account = ObjectProperty(None)
    
    def __init__(self, config: BackupConfig, **kwargs):
        self.config = config
        super().__init__(title="备份设置", **kwargs)
        self._setup_items()
    
    def _setup_items(self):
        """设置项目"""
        # 11.1 本地备份
        self.add_item(SwitchSettingItem(
            title="本地备份",
            description="将数据备份到本地存储",
            value=(self.config.provider == BackupProvider.LOCAL),
            theme=self._theme,
            on_change=lambda v: self._update_provider(BackupProvider.LOCAL if v else None)
        ))
        
        # 11.2 百度网盘
        self.add_item(ButtonSettingItem(
            title="百度网盘",
            description="绑定百度网盘账号进行云备份",
            button_text="绑定",
            theme=self._theme,
            on_click=lambda: self._bind_account(BackupProvider.BAIDU_PAN)
        ))
        
        # 11.3 OneDrive
        self.add_item(ButtonSettingItem(
            title="OneDrive",
            description="绑定OneDrive账号进行云备份",
            button_text="绑定",
            theme=self._theme,
            on_click=lambda: self._bind_account(BackupProvider.ONEDRIVE)
        ))
        
        # 11.4 自动备份
        self.add_item(SwitchSettingItem(
            title="自动备份",
            description="按设定周期自动执行备份",
            value=self.config.auto_backup,
            theme=self._theme,
            on_change=lambda v: self._update_config('auto_backup', v)
        ))
        
        # 11.5 仅WiFi下备份
        self.add_item(SwitchSettingItem(
            title="仅WiFi下备份",
            description="仅在WiFi连接时执行备份",
            value=self.config.wifi_only,
            theme=self._theme,
            on_change=lambda v: self._update_config('wifi_only', v)
        ))
        
        # 11.6 手动备份
        self.add_item(ButtonSettingItem(
            title="手动备份",
            description="立即执行一次完整备份",
            button_text="立即备份",
            theme=self._theme,
            on_click=self._do_backup
        ))
        
        # 11.7 从网盘导入
        self.add_item(ButtonSettingItem(
            title="从网盘导入",
            description="下载并恢复备份的文档和设置",
            button_text="导入",
            theme=self._theme,
            on_click=self._do_restore
        ))
    
    def _update_provider(self, provider: Optional[BackupProvider]):
        if provider:
            self.config.provider = provider
        if self.on_config_change:
            self.on_config_change(self.config)
    
    def _update_config(self, key: str, value):
        setattr(self.config, key, value)
        if self.on_config_change:
            self.on_config_change(self.config)
    
    def _bind_account(self, provider: BackupProvider):
        if self.on_bind_account:
            self.on_bind_account(provider)
    
    def _do_backup(self):
        if self.on_backup:
            self.on_backup()
    
    def _do_restore(self):
        if self.on_restore:
            self.on_restore()


class SettingsView(Screen):
    """设置视图
    
    Requirements: 8.1-8.7, 10.1-10.7, 11.1-11.7
    集成BackupService实现备份功能。
    """
    
    settings = ObjectProperty(None)
    on_settings_change = ObjectProperty(None)
    backup_service = ObjectProperty(None)  # 备份服务引用
    
    def __init__(self, settings: Optional[Settings] = None,
                 theme: Theme = DARK_GREEN_THEME,
                 backup_service=None, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings or Settings()
        self._theme = theme
        self.backup_service = backup_service
        self._setup_ui()
    
    def set_backup_service(self, service):
        """设置备份服务"""
        self.backup_service = service
    
    def _setup_ui(self):
        """设置UI"""
        main_layout = BoxLayout(orientation='vertical', padding=10)
        
        # 背景
        with main_layout.canvas.before:
            Color(*self._theme.background)
            self._bg = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(
            pos=lambda i, v: setattr(self._bg, 'pos', v),
            size=lambda i, v: setattr(self._bg, 'size', v)
        )
        
        # 标题
        title = Label(
            text="设置",
            size_hint_y=None,
            height=50,
            color=self._theme.text_primary,
            font_size='20sp',
            bold=True
        )
        main_layout.add_widget(title)
        
        # 滚动区域
        scroll = ScrollView()
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=20,
            padding=[0, 10]
        )
        content.bind(minimum_height=content.setter('height'))
        
        # 阅读设置
        reading_section = ReadingSettingsSection(
            config=self.settings.reading,
            theme=self._theme,
            on_config_change=self._on_reading_change
        )
        content.add_widget(reading_section)
        
        # 手写笔设置
        stylus_section = StylusSettingsSection(
            config=self.settings.stylus,
            theme=self._theme,
            on_config_change=self._on_stylus_change
        )
        content.add_widget(stylus_section)
        
        # 备份设置
        backup_section = BackupSettingsSection(
            config=self.settings.backup,
            theme=self._theme,
            on_config_change=self._on_backup_change,
            on_backup=self._do_backup,
            on_restore=self._do_restore,
            on_bind_account=self._bind_account
        )
        content.add_widget(backup_section)
        
        # 主题设置
        theme_section = SettingSection(title="主题设置", theme=self._theme)
        theme_section.add_item(SpinnerSettingItem(
            title="界面主题",
            description="选择应用界面主题",
            value="深绿色" if self.settings.theme == "dark_green" else "浅色",
            options=["深绿色", "浅色"],
            theme=self._theme,
            on_change=self._on_theme_change
        ))
        content.add_widget(theme_section)
        
        # 关于
        about_section = SettingSection(title="关于", theme=self._theme)
        about_section.add_item(SettingItem(
            title="版本",
            description="v0.1.0",
            theme=self._theme
        ))
        content.add_widget(about_section)
        
        scroll.add_widget(content)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
    
    def _on_reading_change(self, config: ReadingConfig):
        """阅读设置变化"""
        self.settings.reading = config
        self._notify_change()
    
    def _on_stylus_change(self, config: StylusConfig):
        """手写笔设置变化"""
        self.settings.stylus = config
        self._notify_change()
    
    def _on_backup_change(self, config: BackupConfig):
        """备份设置变化"""
        self.settings.backup = config
        # 同步更新备份服务配置
        if self.backup_service:
            self.backup_service.set_config(config)
        self._notify_change()
    
    def _on_theme_change(self, value: str):
        """主题变化"""
        self.settings.theme = "dark_green" if value == "深绿色" else "light"
        self._notify_change()
    
    def _notify_change(self):
        """通知设置变化"""
        if self.on_settings_change:
            self.on_settings_change(self.settings)
    
    def _do_backup(self):
        """
        执行备份
        
        Requirements: 11.6 - 点击"手动备份"时立即执行一次完整备份
        """
        if not self.backup_service:
            self._show_error("备份服务不可用")
            return
        
        # 显示进度提示
        progress_popup = self._show_progress("正在备份...")
        
        try:
            provider = self.settings.backup.provider
            success = self.backup_service.backup(provider)
            progress_popup.dismiss()
            
            if success:
                self._show_info("备份成功！")
            else:
                self._show_error("备份失败，请重试")
        except Exception as e:
            progress_popup.dismiss()
            self._show_error(f"备份失败: {str(e)}")
    
    def _do_restore(self):
        """
        执行恢复
        
        Requirements: 11.7 - 从网盘导入时下载并恢复备份的文档和设置
        """
        if not self.backup_service:
            self._show_error("备份服务不可用")
            return
        
        # 显示确认对话框
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(
            text="恢复备份将覆盖当前数据，确定继续吗？",
            color=self._theme.text_primary
        ))
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="确定恢复", background_color=self._theme.error)
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="确认恢复",
            content=content,
            size_hint=(None, None),
            size=(350, 180)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._execute_restore(popup))
        popup.open()
    
    def _execute_restore(self, confirm_popup: Popup):
        """执行恢复操作"""
        confirm_popup.dismiss()
        
        # 显示进度提示
        progress_popup = self._show_progress("正在恢复...")
        
        try:
            provider = self.settings.backup.provider
            success = self.backup_service.restore(provider)
            progress_popup.dismiss()
            
            if success:
                self._show_info("恢复成功！请重启应用以应用更改。")
            else:
                self._show_error("恢复失败，请重试")
        except Exception as e:
            progress_popup.dismiss()
            self._show_error(f"恢复失败: {str(e)}")
    
    def _bind_account(self, provider: BackupProvider):
        """
        绑定云账号
        
        Requirements: 11.2, 11.3 - 绑定百度网盘/OneDrive账号
        """
        if not self.backup_service:
            self._show_error("备份服务不可用")
            return
        
        # 检查是否已绑定
        if self.backup_service.is_account_bound(provider):
            # 显示解绑确认
            self._show_unbind_dialog(provider)
        else:
            # 显示绑定对话框
            self._show_bind_dialog(provider)
    
    def _show_bind_dialog(self, provider: BackupProvider):
        """显示绑定对话框"""
        from kivy.uix.textinput import TextInput
        
        provider_name = "百度网盘" if provider == BackupProvider.BAIDU_PAN else "OneDrive"
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(
            text=f"请输入{provider_name}的访问令牌:",
            size_hint_y=None,
            height=30,
            color=self._theme.text_primary
        ))
        
        token_input = TextInput(
            hint_text="Access Token",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        content.add_widget(token_input)
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="绑定", background_color=self._theme.primary_color)
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title=f"绑定{provider_name}",
            content=content,
            size_hint=(None, None),
            size=(350, 220)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._execute_bind(provider, token_input.text, popup))
        popup.open()
    
    def _execute_bind(self, provider: BackupProvider, token: str, popup: Popup):
        """执行绑定"""
        popup.dismiss()
        
        if not token.strip():
            self._show_error("请输入有效的访问令牌")
            return
        
        try:
            credentials = {"access_token": token.strip()}
            success = self.backup_service.bind_account(provider, credentials)
            
            if success:
                provider_name = "百度网盘" if provider == BackupProvider.BAIDU_PAN else "OneDrive"
                self._show_info(f"{provider_name}绑定成功！")
            else:
                self._show_error("绑定失败，请检查令牌是否有效")
        except Exception as e:
            self._show_error(f"绑定失败: {str(e)}")
    
    def _show_unbind_dialog(self, provider: BackupProvider):
        """显示解绑确认对话框"""
        provider_name = "百度网盘" if provider == BackupProvider.BAIDU_PAN else "OneDrive"
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(
            text=f"确定要解绑{provider_name}账号吗？",
            color=self._theme.text_primary
        ))
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="解绑", background_color=self._theme.error)
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="确认解绑",
            content=content,
            size_hint=(None, None),
            size=(300, 150)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._execute_unbind(provider, popup))
        popup.open()
    
    def _execute_unbind(self, provider: BackupProvider, popup: Popup):
        """执行解绑"""
        popup.dismiss()
        
        try:
            self.backup_service.unbind_account(provider)
            provider_name = "百度网盘" if provider == BackupProvider.BAIDU_PAN else "OneDrive"
            self._show_info(f"{provider_name}已解绑")
        except Exception as e:
            self._show_error(f"解绑失败: {str(e)}")
    
    def _show_progress(self, message: str) -> Popup:
        """显示进度提示"""
        content = BoxLayout(orientation='vertical', padding=20)
        content.add_widget(Label(
            text=message,
            color=self._theme.text_primary
        ))
        
        popup = Popup(
            title="请稍候",
            content=content,
            size_hint=(None, None),
            size=(250, 150),
            auto_dismiss=False
        )
        popup.open()
        return popup
    
    def _show_info(self, message: str):
        """显示信息提示"""
        popup = Popup(
            title="提示",
            content=Label(text=message, color=self._theme.text_primary),
            size_hint=(None, None),
            size=(350, 150)
        )
        popup.open()
    
    def _show_error(self, message: str):
        """显示错误提示"""
        popup = Popup(
            title="错误",
            content=Label(text=message, color=self._theme.error),
            size_hint=(None, None),
            size=(350, 150)
        )
        popup.open()
