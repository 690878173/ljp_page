import ast
import json
import queue
import random
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QTimer, Qt, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QAbstractItemView, QMessageBox

from ljp_page._ljp_ui.tableview.xs_tableview import xs_tableview_Delegate, xs_table_model

# 如果有类型检查需求，可以使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    pass


class MockBook:
    """模拟书籍对象，用于演示和测试"""

    def __init__(self, id, title, total_chapters, status=""):
        self.id = id
        self.title = title
        self.total_chapters = total_chapters
        self.status = status


class Ui_MainWindow(object):
    """
    UI主界面构建类 (PyQt6)
    
    结构:
    - CentralWidget
        - Frame (Top: StackedWidget)
            - Get Frame (Page 0)
            - Search Frame (Page 1) 
            - Download Frame (Page 2)
        - Log Frame (Bottom: Log + Settings)
            - Log GroupBox (Left)
            - Setting GroupBox (Right)
    """
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.centralwidget_layout.setObjectName("centralwidget_layout")
        
        # --- 主框架 ---
        self.frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.frame_layout = QtWidgets.QHBoxLayout(self.frame)
        self.frame_layout.setObjectName("frame_layout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        
        # --- 下方：日志与设置区域 ---
        self.log_frame = QtWidgets.QFrame(parent=self.frame)
        self.log_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.log_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.log_frame.setObjectName("log_frame")
        self.log_layout = QtWidgets.QHBoxLayout(self.log_frame)
        self.log_layout.setObjectName("log_layout")
        
        # 日志区域 (左)
        self.log_groupBox = QtWidgets.QGroupBox(parent=self.log_frame)
        self.log_groupBox.setObjectName("log_groupBox")
        self.log_groupBox_layout = QtWidgets.QHBoxLayout(self.log_groupBox)
        self.log_groupBox_layout.setObjectName("log_groupBox_layout")
        self.log_top_layout = QtWidgets.QVBoxLayout()
        self.log_top_layout.setObjectName("log_top_layout")
        self.log_listView = QtWidgets.QListView(parent=self.log_groupBox)
        self.log_listView.setObjectName("log_listView")
        self.log_top_layout.addWidget(self.log_listView)
        self.log_groupBox_layout.addLayout(self.log_top_layout)
        self.log_layout.addWidget(self.log_groupBox)
        
        # 设置区域 (右)
        self.setting_groupBox = QtWidgets.QGroupBox(parent=self.log_frame)
        self.setting_groupBox.setObjectName("setting_groupBox")
        self.settings_layout = QtWidgets.QHBoxLayout(self.setting_groupBox)
        self.settings_layout.setObjectName("settings_layout")
        self.settings_groupBox_Layout = QtWidgets.QVBoxLayout()
        self.settings_groupBox_Layout.setObjectName("settings_groupBox_Layout")
        
        # 页面切换按钮
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.setObjectName("buttons_layout")
        self.get_page_pushButton = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.get_page_pushButton.setObjectName("get_page_pushButton")
        self.buttons_layout.addWidget(self.get_page_pushButton)
        self.download_page_pushButton = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.download_page_pushButton.setObjectName("download_page_pushButton")
        self.buttons_layout.addWidget(self.download_page_pushButton)
        self.search_page_pushButton = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.search_page_pushButton.setObjectName("search_page_pushButton")
        self.buttons_layout.addWidget(self.search_page_pushButton)
        self.log_pushButton = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.log_pushButton.setObjectName("log_pushButton")
        self.buttons_layout.addWidget(self.log_pushButton)
        self.settings_groupBox_Layout.addLayout(self.buttons_layout)
        
        # Headers 设置
        self.headers_Layout = QtWidgets.QHBoxLayout()
        self.headers_Layout.setObjectName("headers_Layout")
        self.headers_label = QtWidgets.QLabel(parent=self.setting_groupBox)
        self.headers_label.setObjectName("headers_label")
        self.headers_Layout.addWidget(self.headers_label)
        self.headers_lineEdit = QtWidgets.QLineEdit(parent=self.setting_groupBox)
        self.headers_lineEdit.setObjectName("headers_lineEdit")
        self.headers_Layout.addWidget(self.headers_lineEdit)
        self.headers_button = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.headers_button.setObjectName("headers_button")
        self.headers_Layout.addWidget(self.headers_button)
        self.settings_groupBox_Layout.addLayout(self.headers_Layout)
        
        # Cookies 设置
        self.cooies_Layout = QtWidgets.QHBoxLayout()
        self.cooies_Layout.setObjectName("cooies_Layout")
        self.cookies_label = QtWidgets.QLabel(parent=self.setting_groupBox)
        self.cookies_label.setObjectName("cookies_label")
        self.cooies_Layout.addWidget(self.cookies_label)
        self.cookies_lineEdit = QtWidgets.QLineEdit(parent=self.setting_groupBox)
        self.cookies_lineEdit.setObjectName("cookies_lineEdit")
        self.cooies_Layout.addWidget(self.cookies_lineEdit)
        self.cookies_button = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.cookies_button.setObjectName("cookies_button")
        self.cooies_Layout.addWidget(self.cookies_button)
        self.settings_groupBox_Layout.addLayout(self.cooies_Layout)
        
        # Proxy 设置
        self.proxy_Layout = QtWidgets.QHBoxLayout()
        self.proxy_Layout.setObjectName("proxy_Layout")
        self.proxy_label = QtWidgets.QLabel(parent=self.setting_groupBox)
        self.proxy_label.setObjectName("proxy_label")
        self.proxy_Layout.addWidget(self.proxy_label)
        self.proxy_lineEdit = QtWidgets.QLineEdit(parent=self.setting_groupBox)
        self.proxy_lineEdit.setObjectName("proxy_lineEdit")
        self.proxy_Layout.addWidget(self.proxy_lineEdit)
        self.proxy_button = QtWidgets.QPushButton(parent=self.setting_groupBox)
        self.proxy_button.setObjectName("proxy_button")
        self.proxy_Layout.addWidget(self.proxy_button)
        self.settings_groupBox_Layout.addLayout(self.proxy_Layout)
        
        self.settings_layout.addLayout(self.settings_groupBox_Layout)
        self.log_layout.addWidget(self.setting_groupBox)
        self.gridLayout.addWidget(self.log_frame, 1, 0, 1, 1)

        # --- 上方：堆叠页面区域 ---
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.frame)
        self.stackedWidget.setObjectName("stackedWidget")
        
        # 页面 0: 获取列表
        self.get_frame = QtWidgets.QWidget()
        self.get_frame.setObjectName("get_frame")
        self.stackedWidget.addWidget(self.get_frame)
        
        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)
        self.frame_layout.addLayout(self.gridLayout)
        self.centralwidget_layout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "教务系统助手"))
        self.log_groupBox.setTitle(_translate("MainWindow", "运行日志"))
        self.setting_groupBox.setTitle(_translate("MainWindow", "控制台"))
        self.get_page_pushButton.setText(_translate("MainWindow", "获取列表"))
        self.download_page_pushButton.setText(_translate("MainWindow", "下载中心"))
        self.search_page_pushButton.setText(_translate("MainWindow", "配置管理"))
        self.log_pushButton.setText(_translate("MainWindow", "清空日志"))
        self.headers_label.setText(_translate("MainWindow", "Headers"))
        self.headers_button.setText(_translate("MainWindow", "更新"))
        self.cookies_label.setText(_translate("MainWindow", "Cookies"))
        self.cookies_button.setText(_translate("MainWindow", "更新"))
        self.proxy_label.setText(_translate("MainWindow", "Proxy"))
        self.proxy_button.setText(_translate("MainWindow", "更新"))


class base_page:
    """
    页面逻辑基类
    
    所有具体的业务页面逻辑类（如 Log_page, setting_page）都应继承此类。
    提供了统一的初始化入口和日志快捷方式。
    """

    def __init__(self, main_window: 'Xs_ui'):
        self.main_window = main_window
        self.ui = self.main_window.ui
        self.init()

    def init(self):
        """初始化页面逻辑，子类需实现"""
        pass

    def log(self, message: str, level: str = "info"):
        """记录日志的快捷方式
        :param message: 日志内容
        :param level: 日志级别 (info, error, warning, debug)
        """
        if hasattr(self.main_window, 'log_page'):
            self.main_window.log_page.add_log(message, level)
        else:
            print(f"[{level.upper()}] {message}")


class Log_page(base_page):
    """
    日志页面逻辑控制器
    
    功能:
    - 管理日志队列
    - 定时从队列刷新日志到 UI 列表
    - 提供线程安全的日志写入接口
    """

    class LOG_TYPE:
        INFO = 'info'
        ERROR = 'error'
        WARNING = 'warning'
        DEBUG = 'debug'

    LOG_COLORS = {
        LOG_TYPE.INFO: QColor(0, 180, 0),  # Green
        LOG_TYPE.ERROR: QColor(220, 0, 0),  # Red
        LOG_TYPE.WARNING: QColor(220, 220, 0),  # Yellow
        LOG_TYPE.DEBUG: QColor(100, 100, 100)  # Gray
    }

    def init(self):
        self.log_queue = queue.Queue()
        self.init_log_model()
        self.init_timer()

    def init_log_model(self):
        """初始化日志数据模型"""
        self.log_model = QStandardItemModel(parent=self.main_window.ui.log_listView)
        self.main_window.ui.log_listView.setModel(self.log_model)
        self.main_window.ui.log_listView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.main_window.ui.log_pushButton.clicked.connect(self.clear_log)
        self.add_log("日志系统已启动", self.LOG_TYPE.INFO)

    def init_timer(self):
        """初始化定时批量刷新器（0.1秒）"""
        self.log_timer = QTimer(self.main_window)
        self.log_timer.timeout.connect(self.batch_update_logs)
        self.log_timer.start(100)

    def add_log(self, content: str, log_type: str = "info"):
        """对外接口：入队日志（供其他页面调用，线程安全）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((timestamp, log_type, content))

    def batch_update_logs(self):
        """定时批量更新日志到视图"""
        if self.log_queue.empty():
            return

        new_rows = []
        max_fetch = 100
        count = 0

        while not self.log_queue.empty() and count < max_fetch:
            try:
                timestamp, log_type, content = self.log_queue.get_nowait()
            except queue.Empty:
                break

            prefix_map = {
                'info': '[信息]',
                'error': '[错误]',
                'warning': '[警告]',
                'debug': '[调试]'
            }
            prefix = f"[{timestamp}] {prefix_map.get(log_type, '[信息]')} "
            item = QStandardItem(prefix + str(content))

            # 设置颜色
            color = self.LOG_COLORS.get(log_type, self.LOG_COLORS['info'])
            item.setForeground(color)
            item.setEditable(False)
            new_rows.append(item)

            self.log_queue.task_done()
            count += 1

        if new_rows:
            for item in new_rows:
                self.log_model.appendRow(item)
            # 滚动到底部
            self.main_window.ui.log_listView.scrollToBottom()

    def clear_log(self):
        """清空日志"""
        self.log_model.clear()
        with self.log_queue.mutex:
            self.log_queue.queue.clear()
        self.add_log("日志已清空", self.LOG_TYPE.INFO)


class setting_page(base_page):
    """
    设置与导航页面逻辑控制器
    
    功能:
    - 负责 StackedWidget 页面切换
    - 处理 Cookies/Headers 更新逻辑
    """

    def init(self):
        # 页面切换逻辑
        self.ui.get_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.search_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.download_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(2))

        # 功能按钮
        self.ui.cookies_button.clicked.connect(self.update_cookies)

    def update_cookies(self):
        """更新 Cookies"""
        cookies_text = self.ui.cookies_lineEdit.text().strip()
        if not cookies_text:
            self.log("请输入 Cookies", "warning")
            return

        cookies = None
        try:
            # 优先尝试 JSON 解析
            cookies = json.loads(cookies_text)
        except json.JSONDecodeError:
            try:
                # 尝试 Python 字面量解析 (兼容旧格式)
                if cookies_text.startswith('{') and cookies_text.endswith('}'):
                    cookies = ast.literal_eval(cookies_text)
            except Exception:
                pass

        if cookies is None or not isinstance(cookies, dict):
            self.log("Cookies 格式不正确，请输入有效的 JSON 或字典格式", "warning")
            return

        if not self.main_window.xs:
            self.log("后端服务未连接，无法更新 Session", "warning")
            return

        try:
            # 更新 Session Cookies
            sessions = []
            if hasattr(self.main_window.xs, 'ui_session') and self.main_window.xs.ui_session:
                sessions.append(self.main_window.xs.ui_session)
            if hasattr(self.main_window.xs, 'session') and self.main_window.xs.session:
                sessions.append(self.main_window.xs.session)

            if not sessions:
                self.log("未找到可用的 Session 对象", "warning")
                return

            for s in sessions:
                if hasattr(s, 'cookie_jar'):
                    s.cookie_jar.clear()
                    s.cookie_jar.update_cookies(cookies)

            self.log("Cookies 已成功更新", "info")
        except Exception as e:
            self.log(f"Cookies 更新失败: {str(e)}", "error")


class search_page(base_page):
    """
    配置/搜索页面逻辑控制器
    
    功能:
    - 提供高级配置选项 (线程数、超时、代理等)
    - 动态生成配置界面组件
    """
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.setup_config_page(self.main_window.ui.get_frame)

    def setup_config_page(self, parent_widget):
        """设计配置页面"""
        layout = QtWidgets.QVBoxLayout(parent_widget)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)

        # 第一部分：基本参数设置
        group_basic = QtWidgets.QGroupBox("基本参数")
        layout_basic = QtWidgets.QGridLayout(group_basic)

        layout_basic.addWidget(QtWidgets.QLabel("最大线程数:"), 0, 0)
        self.spin_threads = QtWidgets.QSpinBox()
        self.spin_threads.setRange(1, 100)
        self.spin_threads.setValue(10)
        layout_basic.addWidget(self.spin_threads, 0, 1)

        layout_basic.addWidget(QtWidgets.QLabel("超时时间(秒):"), 0, 2)
        self.spin_timeout = QtWidgets.QSpinBox()
        self.spin_timeout.setRange(5, 60)
        self.spin_timeout.setValue(30)
        layout_basic.addWidget(self.spin_timeout, 0, 3)

        layout_basic.addWidget(QtWidgets.QLabel("重试次数:"), 1, 0)
        self.combo_retries = QtWidgets.QComboBox()
        self.combo_retries.addItems(["0", "1", "3", "5", "10"])
        layout_basic.addWidget(self.combo_retries, 1, 1)

        scroll_layout.addWidget(group_basic)

        # 第二部分：功能开关
        group_switch = QtWidgets.QGroupBox("功能开关")
        layout_switch = QtWidgets.QHBoxLayout(group_switch)

        self.chk_accelerate = QtWidgets.QCheckBox("启动加速")
        self.chk_auto_load = QtWidgets.QCheckBox("自动加载")
        self.chk_headless = QtWidgets.QCheckBox("无头模式")
        self.chk_log_save = QtWidgets.QCheckBox("保存日志到文件")

        layout_switch.addWidget(self.chk_accelerate)
        layout_switch.addWidget(self.chk_auto_load)
        layout_switch.addWidget(self.chk_headless)
        layout_switch.addWidget(self.chk_log_save)
        layout_switch.addStretch()

        scroll_layout.addWidget(group_switch)

        # 第三部分：多选配置 (0到上限个)
        group_multi = QtWidgets.QGroupBox("高级过滤器 (可多选)")
        layout_multi = QtWidgets.QVBoxLayout(group_multi)

        layout_multi.addWidget(QtWidgets.QLabel("请选择启用的模块 (支持 Ctrl/Shift 多选):"))
        self.list_modules = QtWidgets.QListWidget()
        self.list_modules.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        modules = ["数据清洗模块", "图片压缩模块", "自动翻译模块", "格式转换模块", "云端备份模块", "消息推送模块",
                   "定时任务模块"]
        for m in modules:
            self.list_modules.addItem(m)
        self.list_modules.setMaximumHeight(150)

        layout_multi.addWidget(self.list_modules)
        scroll_layout.addWidget(group_multi)

        # 第四部分：输入项配置
        group_inputs = QtWidgets.QGroupBox("自定义参数")
        layout_inputs = QtWidgets.QFormLayout(group_inputs)

        self.input_api_key = QtWidgets.QLineEdit()
        self.input_api_key.setPlaceholderText("sk-xxxxxxxx")
        layout_inputs.addRow("API Key:", self.input_api_key)

        self.input_proxy = QtWidgets.QLineEdit()
        self.input_proxy.setPlaceholderText("http://127.0.0.1:7890")
        layout_inputs.addRow("代理地址:", self.input_proxy)

        scroll_layout.addWidget(group_inputs)

        # 底部保存按钮
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_save_config = QtWidgets.QPushButton("保存配置")
        self.btn_reset_config = QtWidgets.QPushButton("重置默认")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save_config)
        btn_layout.addWidget(self.btn_reset_config)

        scroll_layout.addLayout(btn_layout)
        scroll_layout.addStretch()  # 填充底部空白

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)


class download_page(base_page):
    """
    下载页面逻辑控制器
    
    功能:
    - 管理下载列表表格
    - 处理添加任务和下载操作
    """
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        # 预留: 初始化表格等逻辑
        pass

    def init_table(self):
        self.download_model = xs_table_model(self.COLUMNS, parent=self.ui.download_tableView)
        self.ui.download_tableView.setModel(self.download_model)
        self.ui.download_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def add_to_list(self, book_info):
        """添加到下载列表"""
        if hasattr(self, 'download_model'):
            self.download_model.append_data(book_info)
            title = getattr(book_info, 'title', 'Unknown')
            self.log(f"已添加到下载列表: {title}")


class get_page(base_page):
    """
    获取/展示列表页面逻辑控制器
    
    功能:
    - 管理数据获取表格
    - 处理搜索和操作按钮事件
    """
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        # 预留: 初始化表格
        pass

    def init_table(self):
        self.get_model = xs_table_model(self.COLUMNS, parent=self.ui.get_tableView)
        self.ui.get_tableView.setModel(self.get_model)
        self.ui.get_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.get_tableView.setMouseTracking(True)

        op_col_idx = self.COLUMNS.index('操作')
        delegate = xs_tableview_Delegate(self, self.ui.get_tableView, op_col_idx)
        self.ui.get_tableView.setItemDelegateForColumn(op_col_idx, delegate)

    def on_search_clicked(self):
        self.log('获取按钮点击')
        try:
            if self.main_window.xs:
                self.main_window.xs.run()
            else:
                self.log("后端逻辑未连接，加载模拟数据", "warning")
                mock_books = [
                    MockBook("2001", "Python编程", "20"),
                    MockBook("2002", "算法导论", "15"),
                ]
                if hasattr(self, 'get_model') and self.get_model:
                    for book in mock_books:
                        self.get_model.append_data(book)

        except Exception as e:
            self.log(f'获取按钮点击异常: {e}', "error")

    def button_click(self, index: QModelIndex):
        """表格中的操作按钮点击事件"""
        row = index.row()
        try:
            # 获取书籍信息
            book_info = self.get_model.book_list[row]
            self.log(f"点击操作: ID=[{book_info.id}], 名称=[{book_info.title}]")

            # 更新状态UI
            op_col = self.COLUMNS.index('操作')
            status_col = self.COLUMNS.index('状态')
            self.get_model.setData(self.get_model.index(row, status_col), '下载中', Qt.ItemDataRole.DisplayRole)
            self.get_model.setData(self.get_model.index(row, op_col), '...', Qt.ItemDataRole.DisplayRole)

            # 触发后端逻辑
            if self.main_window.xs:
                self.main_window.xs.ui_download_book(book_info)

            # 添加到下载页
            if self.main_window.download_page:
                self.main_window.download_page.add_to_list(book_info)

        except Exception as e:
            self.log(f"操作失败: {e}", "error")


class Xs_ui(QMainWindow):
    """
    应用程序主窗口类
    
    职责:
    - 初始化 UI 布局
    - 实例化各子页面逻辑控制器 (Page Controllers)
    - 维护与后端 (Backend) 的连接
    """

    def __init__(self, xs_backend=None):
        super().__init__()
        self.xs_backend = xs_backend
        self.xs = None  # 后端实例引用

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 初始化各页面逻辑控制器
        self.setting_page = setting_page(self)
        self.download_page = download_page(self)
        self.log_page = Log_page(self)
        self.search_page = search_page(self)
        self.get_page = get_page(self)

        if self.xs_backend:
            self.set_xs(self.xs_backend)

        self.log_page.add_log("UI 初始化完成")

    def set_xs(self, xs):
        """注入后端实例"""
        self.xs = xs

    def closeEvent(self, event):
        """窗口关闭确认"""
        reply = QMessageBox.question(self, '退出', '确定要退出吗?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 模拟后端类用于测试
    class MockXs:
        def __init__(self, xs_ui: Xs_ui):
            self.xs = xs_ui
            self.session = type('obj', (object,), {
                'cookie_jar': type('obj', (object,), {
                    'clear': lambda: None,
                    'update_cookies': lambda x: print(f"Cookies updated: {x}")
                })()
            })
            self.ui_session = self.session

        def run(self):
            print("Running mock backend...")

        def ui_download_book(self, book):
            print(f"Downloading {book.title}")


    xs_ui = Xs_ui()
    m = MockXs(xs_ui)
    xs_ui.set_xs(m)
    xs_ui.show()

    sys.exit(app.exec())
