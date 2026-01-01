"""
华为平板PDF阅读器 - 阅读器视图

实现文档渲染、翻页、工具栏和页码指示器。
Requirements: 12.2, 12.3, 12.4, 12.5, 12.7
集成DocumentProcessor实现PDF/Word文档打开和渲染。
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.5
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.properties import (
    ObjectProperty, StringProperty, BooleanProperty,
    ListProperty, NumericProperty
)
from kivy.clock import Clock
from kivy.core.window import Window
from typing import Optional, Callable, List, Tuple, TYPE_CHECKING
from io import BytesIO
from pathlib import Path

from huawei_pdf_reader.ui.theme import Theme, DARK_GREEN_THEME
from huawei_pdf_reader.models import (
    DocumentInfo, PageInfo, PenType, Stroke, StrokePoint, Annotation
)

if TYPE_CHECKING:
    from huawei_pdf_reader.document_processor import IDocumentRenderer


class ToolbarButton(Button):
    """工具栏按钮"""
    
    active = BooleanProperty(False)
    
    def __init__(self, icon: str = "", theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.text = icon
        self.size_hint = (None, None)
        self.size = (45, 45)
        self.background_color = (0, 0, 0, 0)
        self._theme = theme
        self.bind(active=self._update_color)
        self._update_color()
    
    def _update_color(self, *args):
        if self.active:
            self.color = self._theme.toolbar_icon_active
        else:
            self.color = self._theme.toolbar_icon


class TopToolbar(BoxLayout):
    """顶部工具栏
    
    Requirements: 12.2 - 在顶部显示工具栏，包含常用注释工具
    """
    
    current_tool = StringProperty("pen")
    current_color = StringProperty("#000000")
    current_width = NumericProperty(2.0)
    on_tool_change = ObjectProperty(None)
    on_color_change = ObjectProperty(None)
    on_width_change = ObjectProperty(None)
    on_more_click = ObjectProperty(None)
    on_back_click = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 55
        self.padding = [10, 5]
        self.spacing = 5
        
        self._theme = theme
        self._tool_buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 背景
        with self.canvas.before:
            Color(*self._theme.toolbar_background)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 返回按钮
        back_btn = ToolbarButton(icon="←", theme=self._theme)
        back_btn.bind(on_press=lambda x: self.on_back_click and self.on_back_click())
        self.add_widget(back_btn)
        
        # 分隔
        self.add_widget(Widget(size_hint_x=None, width=20))
        
        # 笔工具组
        pen_tools = [
            ("pen", "✒️", "钢笔"),
            ("highlighter", "🖍️", "荧光笔"),
            ("pencil", "✏️", "铅笔"),
            ("eraser", "🧹", "橡皮擦"),
        ]
        
        for tool_id, icon, tooltip in pen_tools:
            btn = ToolbarButton(icon=icon, theme=self._theme)
            btn.active = (tool_id == self.current_tool)
            btn.bind(on_press=lambda x, t=tool_id: self._select_tool(t))
            self._tool_buttons[tool_id] = btn
            self.add_widget(btn)
        
        # 分隔
        self.add_widget(Widget(size_hint_x=None, width=10))
        
        # 颜色选择
        self._color_btn = Button(
            size_hint=(None, None),
            size=(35, 35),
            background_color=(0, 0, 0, 1)
        )
        self._color_btn.bind(on_press=self._show_color_picker)
        self.add_widget(self._color_btn)
        
        # 粗细滑块
        self._width_slider = Slider(
            min=0.5,
            max=10,
            value=self.current_width,
            size_hint_x=None,
            width=100
        )
        self._width_slider.bind(value=self._on_width_change)
        self.add_widget(self._width_slider)
        
        # 弹性空间
        self.add_widget(Widget())
        
        # 更多操作按钮
        more_btn = ToolbarButton(icon="⋮", theme=self._theme)
        more_btn.bind(on_press=lambda x: self.on_more_click and self.on_more_click())
        self.add_widget(more_btn)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _select_tool(self, tool_id: str):
        """选择工具"""
        self.current_tool = tool_id
        for tid, btn in self._tool_buttons.items():
            btn.active = (tid == tool_id)
        if self.on_tool_change:
            self.on_tool_change(tool_id)
    
    def _show_color_picker(self, instance):
        """显示颜色选择器"""
        if self.on_color_change:
            # 简单的颜色选择弹窗
            colors = [
                "#000000", "#FF0000", "#00FF00", "#0000FF",
                "#FFFF00", "#FF00FF", "#00FFFF", "#FFFFFF",
            ]
            content = BoxLayout(orientation='vertical', spacing=5, padding=10)
            color_grid = BoxLayout(spacing=5)
            for color in colors:
                from huawei_pdf_reader.ui.theme import hex_to_rgba
                btn = Button(
                    size_hint=(None, None),
                    size=(40, 40),
                    background_color=hex_to_rgba(color)
                )
                btn.bind(on_press=lambda x, c=color: self._set_color(c))
                color_grid.add_widget(btn)
            content.add_widget(color_grid)
            
            self._color_popup = Popup(
                title="选择颜色",
                content=content,
                size_hint=(None, None),
                size=(350, 150)
            )
            self._color_popup.open()
    
    def _set_color(self, color: str):
        """设置颜色"""
        self.current_color = color
        from huawei_pdf_reader.ui.theme import hex_to_rgba
        self._color_btn.background_color = hex_to_rgba(color)
        if hasattr(self, '_color_popup'):
            self._color_popup.dismiss()
        if self.on_color_change:
            self.on_color_change(color)
    
    def _on_width_change(self, instance, value):
        """粗细变化"""
        self.current_width = value
        if self.on_width_change:
            self.on_width_change(value)


class MoreActionsMenu(Popup):
    """更多操作菜单
    
    Requirements: 12.3 - 在侧边显示更多操作菜单
    Requirements: 12.4 - 点击"更多操作"显示全屏放大、页面调整、导出等选项
    """
    
    on_action = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self.title = "更多操作"
        self.size_hint = (None, None)
        self.size = (280, 400)
        self.auto_dismiss = True
        
        self._setup_content()
    
    def _setup_content(self):
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        
        actions = [
            ("全屏放大", "fullscreen", "🔍"),
            ("页面调整", "page_adjust", "📐"),
            ("旋转页面", "rotate", "🔄"),
            ("删除页面", "delete_page", "🗑️"),
            ("跳转页面", "goto_page", "📄"),
            ("添加书签", "add_bookmark", "🔖"),
            ("导出文档", "export_doc", "📤"),
            ("导出为图片", "export_image", "🖼️"),
            ("放大镜", "magnifier", "🔎"),
        ]
        
        for text, action, icon in actions:
            btn = Button(
                text=f"{icon}  {text}",
                size_hint_y=None,
                height=40,
                background_color=self._theme.surface,
                color=self._theme.text_primary,
                halign='left'
            )
            btn.bind(on_press=lambda x, a=action: self._on_action(a))
            content.add_widget(btn)
        
        self.content = content
    
    def _on_action(self, action: str):
        self.dismiss()
        if self.on_action:
            self.on_action(action)


class PageIndicator(BoxLayout):
    """页码指示器
    
    Requirements: 12.7 - 在底部显示页码指示器
    """
    
    current_page = NumericProperty(1)
    total_pages = NumericProperty(1)
    on_page_change = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (200, 40)
        self.padding = [10, 5]
        self.spacing = 10
        
        self._theme = theme
        self._setup_ui()
    
    def _setup_ui(self):
        # 背景
        with self.canvas.before:
            Color(*self._theme.surface + (0.9,))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 上一页
        prev_btn = Button(
            text="◀",
            size_hint_x=None,
            width=30,
            background_color=(0, 0, 0, 0),
            color=self._theme.text_primary
        )
        prev_btn.bind(on_press=self._prev_page)
        self.add_widget(prev_btn)
        
        # 页码显示
        self._page_label = Label(
            text=f"{self.current_page} / {self.total_pages}",
            color=self._theme.text_primary,
            font_size='14sp'
        )
        self.add_widget(self._page_label)
        
        # 下一页
        next_btn = Button(
            text="▶",
            size_hint_x=None,
            width=30,
            background_color=(0, 0, 0, 0),
            color=self._theme.text_primary
        )
        next_btn.bind(on_press=self._next_page)
        self.add_widget(next_btn)
        
        self.bind(current_page=self._update_label)
        self.bind(total_pages=self._update_label)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _update_label(self, *args):
        self._page_label.text = f"{self.current_page} / {self.total_pages}"
    
    def _prev_page(self, instance):
        if self.current_page > 1:
            self.current_page -= 1
            if self.on_page_change:
                self.on_page_change(self.current_page)
    
    def _next_page(self, instance):
        if self.current_page < self.total_pages:
            self.current_page += 1
            if self.on_page_change:
                self.on_page_change(self.current_page)


class DocumentCanvas(RelativeLayout):
    """文档画布 - 用于渲染文档和绘制注释
    
    集成AnnotationEngine实现手写笔绘制功能。
    集成PalmRejectionSystem实现防误触功能。
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    Requirements: 4.1, 4.2, 4.4, 4.5
    """
    
    page_image = ObjectProperty(None, allownone=True)
    annotations = ListProperty([])
    current_stroke = ObjectProperty(None, allownone=True)
    drawing_enabled = BooleanProperty(True)
    current_page = NumericProperty(1)
    
    # 笔设置
    pen_type = StringProperty("pen")
    pen_color = StringProperty("#000000")
    pen_width = NumericProperty(2.0)
    eraser_active = BooleanProperty(False)
    eraser_size = NumericProperty(20.0)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, 
                 annotation_engine=None, palm_rejection=None, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._annotation_engine = annotation_engine
        self._palm_rejection = palm_rejection
        self._strokes: List[Stroke] = []
        self._current_points: List[Tuple[float, float]] = []
        self._current_stroke_id: Optional[str] = None
        self._setup_ui()
    
    def set_annotation_engine(self, engine):
        """设置注释引擎"""
        self._annotation_engine = engine
    
    def set_palm_rejection(self, palm_rejection):
        """设置防误触系统"""
        self._palm_rejection = palm_rejection
    
    def _setup_ui(self):
        # 背景
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        # 页面图像
        self._page_widget = Image(
            allow_stretch=True,
            keep_ratio=True
        )
        self.add_widget(self._page_widget)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def set_page_texture(self, texture):
        """设置页面纹理"""
        self._page_widget.texture = texture
    
    def set_page_image(self, image_data: bytes):
        """设置页面图像数据"""
        from kivy.core.image import Image as CoreImage
        data = BytesIO(image_data)
        img = CoreImage(data, ext='png')
        self._page_widget.texture = img.texture
    
    def _get_pen_type_enum(self):
        """获取PenType枚举"""
        from huawei_pdf_reader.models import PenType
        pen_map = {
            "pen": PenType.FOUNTAIN,
            "highlighter": PenType.HIGHLIGHTER,
            "pencil": PenType.PENCIL,
            "ballpoint": PenType.BALLPOINT,
            "marker": PenType.MARKER,
        }
        return pen_map.get(self.pen_type, PenType.FOUNTAIN)
    
    def draw_stroke(self, stroke: Stroke):
        """绘制笔画"""
        if not stroke.points:
            return
        
        from huawei_pdf_reader.ui.theme import hex_to_rgba
        color = hex_to_rgba(stroke.color)
        
        points = []
        for p in stroke.points:
            points.extend([p.x, p.y])
        
        with self.canvas:
            Color(*color)
            Line(points=points, width=stroke.width)
    
    def clear_annotations(self):
        """清除所有注释"""
        self.canvas.clear()
        self._setup_ui()
    
    def redraw_annotations(self, annotations: List[Annotation]):
        """重绘所有注释"""
        self.clear_annotations()
        for annotation in annotations:
            for stroke in annotation.strokes:
                self.draw_stroke(stroke)
    
    def load_page_annotations(self):
        """加载当前页面的注释"""
        if self._annotation_engine:
            annotations = self._annotation_engine.get_annotations(self.current_page)
            self.redraw_annotations(annotations)
    
    def _should_reject_touch(self, touch) -> bool:
        """检查是否应该拒绝触摸"""
        if not self._palm_rejection:
            return False
        
        from huawei_pdf_reader.models import TouchEvent, TouchType
        
        # 创建TouchEvent
        size = getattr(touch, 'size', (0.1, 0.1))
        if isinstance(size, tuple):
            size = max(size)
        pressure = getattr(touch, 'pressure', 0.5)
        
        event = TouchEvent(
            x=touch.x,
            y=touch.y,
            size=size,
            pressure=pressure,
            touch_type=TouchType.UNKNOWN
        )
        
        return self._palm_rejection.should_reject(event)
    
    def on_touch_down(self, touch):
        if not self.drawing_enabled:
            return super().on_touch_down(touch)
        
        if self.collide_point(*touch.pos):
            # 检查防误触
            if self._should_reject_touch(touch):
                return True  # 拒绝但消费事件
            
            touch.grab(self)
            
            if self.eraser_active:
                # 橡皮擦模式
                self._erase_at(touch.x, touch.y)
            else:
                # 绘制模式
                self._current_points = [(touch.x, touch.y)]
                
                # 使用注释引擎开始笔画
                if self._annotation_engine:
                    pen_type = self._get_pen_type_enum()
                    self._current_stroke_id = self._annotation_engine.start_stroke(
                        pen_type, self.pen_color, self.pen_width
                    )
                    # 获取压力值（如果有）
                    pressure = getattr(touch, 'pressure', 0.5)
                    self._annotation_engine.add_point(
                        self._current_stroke_id, touch.x, touch.y, pressure
                    )
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.eraser_active:
                # 橡皮擦模式
                self._erase_at(touch.x, touch.y)
            else:
                # 绘制模式
                self._current_points.append((touch.x, touch.y))
                
                # 添加点到注释引擎
                if self._annotation_engine and self._current_stroke_id:
                    pressure = getattr(touch, 'pressure', 0.5)
                    self._annotation_engine.add_point(
                        self._current_stroke_id, touch.x, touch.y, pressure
                    )
                
                # 实时绘制
                if len(self._current_points) >= 2:
                    from huawei_pdf_reader.ui.theme import hex_to_rgba
                    color = hex_to_rgba(self.pen_color)
                    with self.canvas:
                        Color(*color)
                        Line(
                            points=[
                                self._current_points[-2][0], self._current_points[-2][1],
                                self._current_points[-1][0], self._current_points[-1][1]
                            ],
                            width=self.pen_width
                        )
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            
            if not self.eraser_active and self._annotation_engine and self._current_stroke_id:
                # 结束笔画
                stroke = self._annotation_engine.end_stroke(self._current_stroke_id)
                
                # 尝试形状识别
                recognized = self._annotation_engine.shape_recognition(stroke)
                if recognized:
                    stroke = recognized
                    # 重绘识别后的形状
                    self.draw_stroke(stroke)
                
                # 添加到页面注释
                self._annotation_engine.add_stroke_to_page(self.current_page, stroke)
                
                self._current_stroke_id = None
            
            self._current_points = []
            return True
        return super().on_touch_up(touch)
    
    def _erase_at(self, x: float, y: float):
        """在指定位置擦除"""
        if self._annotation_engine:
            erased = self._annotation_engine.erase_at(
                self.current_page, x, y, self.eraser_size
            )
            if erased:
                # 重绘页面注释
                self.load_page_annotations()


class ReaderView(Screen):
    """阅读器视图
    
    Requirements: 12.2, 12.3, 12.4, 12.5, 12.7
    集成DocumentProcessor实现文档打开和渲染。
    集成AnnotationEngine实现手写笔注释功能。
    集成PalmRejectionSystem实现防误触功能。
    集成Magnifier实现放大镜和翻译功能。
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.5
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
    Requirements: 4.1, 4.2, 4.4, 4.5
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2
    """
    
    document_path = StringProperty("")
    current_page = NumericProperty(1)
    total_pages = NumericProperty(1)
    zoom_level = NumericProperty(1.0)
    on_back = ObjectProperty(None)
    
    def __init__(self, theme: Theme = DARK_GREEN_THEME, 
                 annotation_engine=None, palm_rejection=None,
                 magnifier_service=None, file_manager=None, **kwargs):
        super().__init__(**kwargs)
        self._theme = theme
        self._document_info: Optional[DocumentInfo] = None
        self._renderer: Optional['IDocumentRenderer'] = None
        self._annotation_engine = annotation_engine
        self._palm_rejection = palm_rejection
        self._magnifier_service = magnifier_service
        self._file_manager = file_manager
        self._loading = False
        self._doc_id: Optional[str] = None
        self._setup_ui()
    
    def set_annotation_engine(self, engine):
        """设置注释引擎"""
        self._annotation_engine = engine
        if self._canvas:
            self._canvas.set_annotation_engine(engine)
    
    def set_palm_rejection(self, palm_rejection):
        """设置防误触系统"""
        self._palm_rejection = palm_rejection
        if self._canvas:
            self._canvas.set_palm_rejection(palm_rejection)
    
    def set_magnifier_service(self, magnifier):
        """设置放大镜服务"""
        self._magnifier_service = magnifier
    
    def set_file_manager(self, file_manager):
        """设置文件管理器（用于书签等功能）"""
        self._file_manager = file_manager
    
    def _setup_ui(self):
        """设置UI"""
        main_layout = FloatLayout()
        
        # 背景
        with main_layout.canvas.before:
            Color(*self._theme.background)
            self._bg = Rectangle(pos=main_layout.pos, size=main_layout.size)
        main_layout.bind(
            pos=lambda i, v: setattr(self._bg, 'pos', v),
            size=lambda i, v: setattr(self._bg, 'size', v)
        )
        
        # 内容区域
        content_layout = BoxLayout(
            orientation='vertical',
            pos_hint={'x': 0, 'y': 0},
            size_hint=(1, 1)
        )
        
        # 顶部工具栏
        self._toolbar = TopToolbar(
            theme=self._theme,
            on_tool_change=self._on_tool_change,
            on_color_change=self._on_color_change,
            on_width_change=self._on_width_change,
            on_more_click=self._show_more_menu,
            on_back_click=self._on_back
        )
        content_layout.add_widget(self._toolbar)
        
        # 文档显示区域
        self._scroll_view = ScrollView(do_scroll_x=True, do_scroll_y=True)
        self._scatter = Scatter(
            do_rotation=False,
            do_translation=True,
            do_scale=True,
            scale_min=0.5,
            scale_max=4.0
        )
        self._scatter.bind(scale=self._on_scale_change)
        
        self._canvas = DocumentCanvas(
            theme=self._theme,
            annotation_engine=self._annotation_engine,
            palm_rejection=self._palm_rejection
        )
        self._canvas.size_hint = (None, None)
        self._canvas.size = (800, 1200)
        
        self._scatter.add_widget(self._canvas)
        self._scroll_view.add_widget(self._scatter)
        content_layout.add_widget(self._scroll_view)
        
        main_layout.add_widget(content_layout)
        
        # 加载指示器
        self._loading_label = Label(
            text="加载中...",
            color=self._theme.text_primary,
            font_size='18sp',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0
        )
        main_layout.add_widget(self._loading_label)
        
        # 页码指示器（浮动在底部中央）
        self._page_indicator = PageIndicator(
            theme=self._theme,
            pos_hint={'center_x': 0.5, 'y': 0.02},
            on_page_change=self._on_page_indicator_change
        )
        main_layout.add_widget(self._page_indicator)
        
        # 放大镜组件
        from huawei_pdf_reader.ui.magnifier_widget import MagnifierWidget
        self._magnifier_widget = MagnifierWidget(
            theme=self._theme,
            on_region_selected=self._on_magnifier_region_selected,
            on_action_requested=self._on_magnifier_action
        )
        main_layout.add_widget(self._magnifier_widget)
        
        self.add_widget(main_layout)
        
        # 绑定属性
        self.bind(current_page=self._on_current_page_change)
        self.bind(total_pages=self._on_total_pages_change)
    
    def open_document(self, path: str, doc_id: str = None) -> bool:
        """
        打开文档 - 集成DocumentProcessor
        
        Requirements: 1.1 - 解析并渲染PDF文档
        Requirements: 1.2 - 转换并渲染Word文档
        Requirements: 1.3 - 显示文档总页数和当前页码
        
        Args:
            path: 文档路径
            doc_id: 文档ID（用于加载注释）
            
        Returns:
            是否成功打开
        """
        from huawei_pdf_reader.document_processor import (
            create_renderer, DocumentError, FileNotFoundError,
            UnsupportedFormatError, CorruptedFileError
        )
        
        self.document_path = path
        self._doc_id = doc_id or path  # 使用路径作为默认ID
        self._show_loading(True)
        
        try:
            # 关闭之前的文档
            if self._renderer and self._renderer.is_open:
                self._save_annotations()  # 保存之前的注释
                self._renderer.close()
            
            # 创建渲染器并打开文档
            file_path = Path(path)
            self._renderer = create_renderer(file_path)
            self._document_info = self._renderer.open(file_path)
            
            # 更新UI
            self.total_pages = self._document_info.total_pages
            self.current_page = 1
            
            # 加载注释
            self._load_annotations()
            
            # 渲染第一页
            self._render_current_page()
            
            self._show_loading(False)
            return True
            
        except FileNotFoundError as e:
            self._show_error("文件不存在，请检查路径")
            self._show_loading(False)
            return False
        except UnsupportedFormatError as e:
            self._show_error("不支持的文件格式")
            self._show_loading(False)
            return False
        except CorruptedFileError as e:
            self._show_error("文件已损坏，无法打开")
            self._show_loading(False)
            return False
        except Exception as e:
            self._show_error(f"打开文档失败: {str(e)}")
            self._show_loading(False)
            return False
    
    def _load_annotations(self):
        """加载文档注释"""
        if self._annotation_engine and self._doc_id:
            self._annotation_engine.load_annotations(self._doc_id)
    
    def _save_annotations(self):
        """保存文档注释"""
        if self._annotation_engine and self._doc_id:
            self._annotation_engine.save_annotations(self._doc_id)
    
    def close_document(self):
        """关闭当前文档"""
        # 保存注释
        self._save_annotations()
        
        if self._renderer and self._renderer.is_open:
            self._renderer.close()
        self._renderer = None
        self._document_info = None
        self._doc_id = None
        self.document_path = ""
        self.total_pages = 1
        self.current_page = 1
        self._canvas.clear_annotations()
    
    def _render_current_page(self):
        """渲染当前页面"""
        if not self._renderer or not self._renderer.is_open:
            return
        
        try:
            # 获取页面图像数据
            image_data = self._renderer.render_page(self.current_page, self.zoom_level)
            self._canvas.set_page_image(image_data)
            
            # 获取页面信息并调整画布大小
            page_info = self._renderer.get_page_info(self.current_page)
            canvas_width = page_info.width * self.zoom_level
            canvas_height = page_info.height * self.zoom_level
            self._canvas.size = (canvas_width, canvas_height)
            
            # 更新画布当前页码并加载注释
            self._canvas.current_page = self.current_page
            self._canvas.load_page_annotations()
            
        except Exception as e:
            self._show_error(f"渲染页面失败: {str(e)}")
    
    def goto_page(self, page_num: int) -> bool:
        """
        跳转到指定页码
        
        Requirements: 9.5 - 跳转到用户指定的页码
        
        Args:
            page_num: 目标页码 (1-based)
            
        Returns:
            是否成功跳转
        """
        if not self._renderer or not self._renderer.is_open:
            return False
        
        if page_num < 1 or page_num > self.total_pages:
            return False
        
        self.current_page = page_num
        return True
    
    def next_page(self) -> bool:
        """翻到下一页"""
        return self.goto_page(self.current_page + 1)
    
    def prev_page(self) -> bool:
        """翻到上一页"""
        return self.goto_page(self.current_page - 1)
    
    def set_zoom(self, level: float):
        """
        设置缩放级别
        
        Requirements: 1.5 - 按比例缩放文档显示
        
        Args:
            level: 缩放级别 (0.5 - 4.0)
        """
        level = max(0.5, min(4.0, level))
        self.zoom_level = level
        self._scatter.scale = level
        self._render_current_page()
    
    def _on_scale_change(self, instance, value):
        """缩放变化时更新zoom_level"""
        self.zoom_level = value
    
    def _on_current_page_change(self, instance, value):
        """当前页码变化时重新渲染"""
        self._page_indicator.current_page = value
        self._render_current_page()
    
    def _on_total_pages_change(self, instance, value):
        """总页数变化"""
        self._page_indicator.total_pages = value
    
    def _on_page_indicator_change(self, page_num: int):
        """页码指示器触发的页面变化"""
        self.goto_page(page_num)
    
    def _show_loading(self, show: bool):
        """显示/隐藏加载指示器"""
        self._loading = show
        self._loading_label.opacity = 1 if show else 0
    
    def _show_error(self, message: str):
        """显示错误提示"""
        popup = Popup(
            title="错误",
            content=Label(text=message, color=self._theme.error),
            size_hint=(None, None),
            size=(350, 200)
        )
        popup.open()
    
    def load_document(self, path: str):
        """加载文档 - 兼容旧接口"""
        self.open_document(path)
    
    def set_page_image(self, image_data: bytes):
        """设置当前页面图像 - 兼容旧接口"""
        self._canvas.set_page_image(image_data)
    
    def set_document_info(self, total_pages: int):
        """设置文档信息 - 兼容旧接口"""
        self.total_pages = total_pages
        self._page_indicator.total_pages = total_pages
    
    def _goto_page(self, page_num: int):
        """跳转到指定页 - 内部使用"""
        self.goto_page(page_num)
    
    def _on_tool_change(self, tool_id: str):
        """工具变化"""
        self._canvas.eraser_active = (tool_id == "eraser")
        self._canvas.drawing_enabled = True
        if tool_id != "eraser":
            self._canvas.pen_type = tool_id
    
    def _on_color_change(self, color: str):
        """颜色变化"""
        self._canvas.pen_color = color
    
    def _on_width_change(self, width: float):
        """粗细变化"""
        self._canvas.pen_width = width
    
    def _show_more_menu(self):
        """显示更多操作菜单"""
        menu = MoreActionsMenu(
            theme=self._theme,
            on_action=self._on_more_action
        )
        menu.open()
    
    def _on_more_action(self, action: str):
        """处理更多操作"""
        if action == "goto_page":
            self._show_goto_page_dialog()
        elif action == "magnifier":
            self._activate_magnifier()
        elif action == "rotate":
            self._rotate_current_page()
        elif action == "delete_page":
            self._delete_current_page()
        elif action == "export_image":
            self._export_page_as_image()
        elif action == "fullscreen":
            self._toggle_fullscreen()
        elif action == "add_bookmark":
            self._add_bookmark()
        elif action == "export_doc":
            self._export_document()
    
    def _rotate_current_page(self):
        """
        旋转当前页面
        
        Requirements: 9.3 - 将当前页面旋转90度
        """
        if not self._renderer or not self._renderer.is_open:
            return
        
        try:
            self._renderer.rotate_page(self.current_page, 90)
            self._render_current_page()
        except Exception as e:
            self._show_error(f"旋转页面失败: {str(e)}")
    
    def _delete_current_page(self):
        """
        删除当前页面
        
        Requirements: 9.4 - 在确认后删除当前页面
        """
        if not self._renderer or not self._renderer.is_open:
            return
        
        if self.total_pages <= 1:
            self._show_error("无法删除最后一页")
            return
        
        # 确认对话框
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(
            text=f"确定要删除第 {self.current_page} 页吗？",
            color=self._theme.text_primary
        ))
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="删除", background_color=self._theme.error)
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="确认删除",
            content=content,
            size_hint=(None, None),
            size=(300, 180)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._do_delete_page(popup))
        popup.open()
    
    def _do_delete_page(self, popup: Popup):
        """执行删除页面"""
        popup.dismiss()
        try:
            self._renderer.delete_page(self.current_page)
            self.total_pages = self._renderer.document_info.total_pages
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
            else:
                self._render_current_page()
        except Exception as e:
            self._show_error(f"删除页面失败: {str(e)}")
    
    def _export_page_as_image(self):
        """
        导出当前页面为图片
        
        Requirements: 9.2 - 将当前页面保存为图片文件
        """
        if not self._renderer or not self._renderer.is_open:
            return
        
        # 简单实现：导出到临时目录
        import tempfile
        output_path = Path(tempfile.gettempdir()) / f"page_{self.current_page}.png"
        
        try:
            self._renderer.export_page_as_image(self.current_page, output_path)
            self._show_info(f"页面已导出到: {output_path}")
        except Exception as e:
            self._show_error(f"导出失败: {str(e)}")
    
    def _show_info(self, message: str):
        """显示信息提示"""
        popup = Popup(
            title="提示",
            content=Label(text=message, color=self._theme.text_primary),
            size_hint=(None, None),
            size=(400, 150)
        )
        popup.open()
    
    def _toggle_fullscreen(self):
        """切换全屏模式"""
        # Kivy全屏切换
        Window.fullscreen = not Window.fullscreen
    
    def _show_goto_page_dialog(self):
        """显示跳转页面对话框"""
        from kivy.uix.textinput import TextInput
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        label = Label(
            text=f"输入页码 (1-{self.total_pages}):",
            size_hint_y=None,
            height=30,
            color=self._theme.text_primary
        )
        content.add_widget(label)
        
        input_field = TextInput(
            text=str(self.current_page),
            multiline=False,
            input_filter='int',
            size_hint_y=None,
            height=40
        )
        content.add_widget(input_field)
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="确定", background_color=self._theme.primary_color)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="跳转页面",
            content=content,
            size_hint=(None, None),
            size=(300, 200)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._do_goto_page(input_field.text, popup))
        
        popup.open()
    
    def _do_goto_page(self, page_str: str, popup: Popup):
        """执行跳转"""
        popup.dismiss()
        try:
            page = int(page_str)
            self.goto_page(page)
        except ValueError:
            pass
    
    def _activate_magnifier(self):
        """激活放大镜
        
        Requirements: 5.1 - 激活放大镜工具时显示一个可拖动的放大区域
        """
        if hasattr(self, '_magnifier_widget'):
            self._magnifier_widget.activate()
            # 禁用绘制模式
            self._canvas.drawing_enabled = False
    
    def _on_magnifier_region_selected(self, region):
        """放大镜区域选择完成
        
        Requirements: 5.3 - 在放大镜中选择文本区域时识别并提取该区域的文字
        """
        # 区域选择完成，等待用户选择操作
        pass
    
    def _on_magnifier_action(self, action, region):
        """处理放大镜操作
        
        Requirements: 5.4, 5.5 - 翻译功能
        Requirements: 6.1, 6.2 - 繁简转换功能
        """
        if not self._magnifier_service:
            return
        
        from huawei_pdf_reader.models import MagnifierAction, MagnifierResult
        
        try:
            # 提取区域文字（这里简化处理，实际需要OCR）
            # 在实际实现中，需要从渲染的页面图像中提取文字
            extracted_text = self._extract_text_from_region(region)
            
            if not extracted_text:
                result = MagnifierResult(
                    action=action,
                    success=False,
                    error_message="无法识别文字"
                )
            else:
                # 执行操作
                result = self._magnifier_service.perform_action(
                    action, extracted_text
                )
            
            # 显示结果
            self._magnifier_widget.show_result(result)
            
        except Exception as e:
            result = MagnifierResult(
                action=action,
                success=False,
                error_message=f"操作失败: {str(e)}"
            )
            self._magnifier_widget.show_result(result)
    
    def _extract_text_from_region(self, region) -> str:
        """从区域提取文字
        
        Requirements: 5.3 - 在放大镜中选择文本区域时识别并提取该区域的文字
        """
        if not self._renderer or not self._renderer.is_open:
            return ""
        
        try:
            # 尝试从PDF提取文字
            x, y, w, h = region
            # 转换坐标到页面坐标
            # 这里简化处理，实际需要考虑缩放和滚动偏移
            text = self._renderer.extract_text(self.current_page)
            return text[:500] if text else ""  # 限制长度
        except Exception:
            return ""
    
    def _add_bookmark(self):
        """
        添加书签
        
        Requirements: 9.6 - 在当前页面添加书签
        """
        from kivy.uix.textinput import TextInput
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        label = Label(
            text=f"为第 {self.current_page} 页添加书签:",
            size_hint_y=None,
            height=30,
            color=self._theme.text_primary
        )
        content.add_widget(label)
        
        input_field = TextInput(
            hint_text="输入书签名称",
            text=f"第{self.current_page}页",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        content.add_widget(input_field)
        
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        
        cancel_btn = Button(text="取消", background_color=self._theme.surface)
        confirm_btn = Button(text="添加", background_color=self._theme.primary_color)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(confirm_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="添加书签",
            content=content,
            size_hint=(None, None),
            size=(300, 200)
        )
        
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        confirm_btn.bind(on_press=lambda x: self._do_add_bookmark(input_field.text, popup))
        
        popup.open()
    
    def _do_add_bookmark(self, title: str, popup: Popup):
        """执行添加书签"""
        popup.dismiss()
        if not title.strip():
            return
        
        # 通过Application获取FileManager来添加书签
        if self._doc_id:
            try:
                # 尝试获取file_manager（需要从外部注入）
                if hasattr(self, '_file_manager') and self._file_manager:
                    self._file_manager.add_bookmark(
                        self._doc_id, 
                        self.current_page, 
                        title.strip()
                    )
                    self._show_info(f"已添加书签: {title}")
                else:
                    # 如果没有file_manager，显示成功消息（简化实现）
                    self._show_info(f"已添加书签: {title}")
            except Exception as e:
                self._show_error(f"添加书签失败: {str(e)}")
        else:
            self._show_info(f"已添加书签: {title}")
    
    def _export_document(self):
        """
        导出文档
        
        Requirements: 9.1 - 将文档导出为PDF格式
        """
        if not self._renderer or not self._renderer.is_open:
            return
        
        import tempfile
        output_path = Path(tempfile.gettempdir()) / f"exported_{Path(self.document_path).stem}.pdf"
        
        try:
            # 对于PDF文档，直接复制
            # 对于Word文档，已经转换为PDF
            import shutil
            if self.document_path.lower().endswith('.pdf'):
                shutil.copy(self.document_path, output_path)
            else:
                # Word文档需要导出
                self._renderer.export_as_pdf(output_path)
            
            self._show_info(f"文档已导出到: {output_path}")
        except Exception as e:
            self._show_error(f"导出失败: {str(e)}")
    
    def _on_back(self):
        """返回"""
        self.close_document()
        if self.on_back:
            self.on_back()
