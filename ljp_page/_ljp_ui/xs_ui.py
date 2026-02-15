import ast
import json
import queue
import random
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any, TYPE_CHECKING

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
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.centralwidget_layout.setObjectName("centralwidget_layout")
        self.frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.frame_layout = QtWidgets.QHBoxLayout(self.frame)
        self.frame_layout.setObjectName("frame_layout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.log_frame = QtWidgets.QFrame(parent=self.frame)
        self.log_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.log_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.log_frame.setObjectName("log_frame")
        self.log_layout = QtWidgets.QHBoxLayout(self.log_frame)
        self.log_layout.setObjectName("log_layout")
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
        self.setting_groupBox = QtWidgets.QGroupBox(parent=self.log_frame)
        self.setting_groupBox.setObjectName("setting_groupBox")
        self.settings_layout = QtWidgets.QHBoxLayout(self.setting_groupBox)
        self.settings_layout.setObjectName("settings_layout")
        self.settings_groupBox_Layout = QtWidgets.QVBoxLayout()
        self.settings_groupBox_Layout.setObjectName("settings_groupBox_Layout")
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

        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.frame)
        self.stackedWidget.setObjectName("stackedWidget")
        self.get_frame = QtWidgets.QWidget()
        self.get_frame.setObjectName("get_frame")
        self.get_frame_layout = QtWidgets.QVBoxLayout(self.get_frame)
        self.get_frame_layout.setObjectName("get_frame_layout")
        self.get_groupBox = QtWidgets.QGroupBox(parent=self.get_frame)
        self.get_groupBox.setObjectName("get_groupBox")
        self.get_groupBox_layout = QtWidgets.QVBoxLayout(self.get_groupBox)
        self.get_groupBox_layout.setObjectName("get_groupBox_layout")
        self.get_groupBox_all_layout = QtWidgets.QVBoxLayout()
        self.get_groupBox_all_layout.setObjectName("get_groupBox_all_layout")
        self.get_groupBox_top_layout = QtWidgets.QHBoxLayout()
        self.get_groupBox_top_layout.setObjectName("get_groupBox_top_layout")
        self.get_comboBox = QtWidgets.QComboBox(parent=self.get_groupBox)
        self.get_comboBox.setObjectName("get_comboBox")
        self.get_comboBox.addItem("")
        self.get_comboBox.addItem("")
        self.get_groupBox_top_layout.addWidget(self.get_comboBox)
        self.get_lineEdit = QtWidgets.QLineEdit(parent=self.get_groupBox)
        self.get_lineEdit.setObjectName("get_lineEdit")
        self.get_groupBox_top_layout.addWidget(self.get_lineEdit)
        self.get_pushButton = QtWidgets.QPushButton(parent=self.get_groupBox)
        self.get_pushButton.setObjectName("get_pushButton")
        self.get_groupBox_top_layout.addWidget(self.get_pushButton)
        self.get_groupBox_all_layout.addLayout(self.get_groupBox_top_layout)
        self.get_tableView = QtWidgets.QTableView(parent=self.get_groupBox)
        self.get_tableView.setObjectName("get_tableView")
        self.get_groupBox_all_layout.addWidget(self.get_tableView)
        self.get_groupBox_layout.addLayout(self.get_groupBox_all_layout)
        self.get_frame_layout.addWidget(self.get_groupBox)
        self.stackedWidget.addWidget(self.get_frame)
        self.page_5 = QtWidgets.QWidget()
        self.page_5.setObjectName("page_5")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.page_5)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.search_groupBox = QtWidgets.QGroupBox(parent=self.page_5)
        self.search_groupBox.setObjectName("search_groupBox")
        self.search_groupBox_layout = QtWidgets.QVBoxLayout(self.search_groupBox)
        self.search_groupBox_layout.setObjectName("search_groupBox_layout")
        self.search_groupBox_all_layout = QtWidgets.QVBoxLayout()
        self.search_groupBox_all_layout.setObjectName("search_groupBox_all_layout")
        self.search_groupBox_top_layout = QtWidgets.QHBoxLayout()
        self.search_groupBox_top_layout.setObjectName("search_groupBox_top_layout")
        self.search_start_label_2 = QtWidgets.QLabel(parent=self.search_groupBox)
        self.search_start_label_2.setStyleSheet("border: 2px solid rgb(255, 255, 255);  /* 2px宽的实线，颜色为橙色 */")
        self.search_start_label_2.setScaledContents(False)
        self.search_start_label_2.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self.search_start_label_2.setObjectName("search_start_label_2")
        self.search_groupBox_top_layout.addWidget(self.search_start_label_2)
        self.search_start_lineEdit = QtWidgets.QLineEdit(parent=self.search_groupBox)
        self.search_start_lineEdit.setObjectName("search_start_lineEdit")
        self.search_groupBox_top_layout.addWidget(self.search_start_lineEdit)
        self.search_end_label = QtWidgets.QLabel(parent=self.search_groupBox)
        self.search_end_label.setStyleSheet("border: 2px solid rgb(255, 255, 255); ")
        self.search_end_label.setObjectName("search_end_label")
        self.search_groupBox_top_layout.addWidget(self.search_end_label)
        self.search_end_lineEdit = QtWidgets.QLineEdit(parent=self.search_groupBox)
        self.search_end_lineEdit.setObjectName("search_end_lineEdit")
        self.search_groupBox_top_layout.addWidget(self.search_end_lineEdit)
        self.search_button = QtWidgets.QPushButton(parent=self.search_groupBox)
        self.search_button.setObjectName("search_button")
        self.search_groupBox_top_layout.addWidget(self.search_button)
        self.search_groupBox_all_layout.addLayout(self.search_groupBox_top_layout)
        self.search_tableView = QtWidgets.QTableView(parent=self.search_groupBox)
        self.search_tableView.setObjectName("search_tableView")
        self.search_groupBox_all_layout.addWidget(self.search_tableView)
        self.search_groupBox_layout.addLayout(self.search_groupBox_all_layout)
        self.horizontalLayout_15.addWidget(self.search_groupBox)
        self.stackedWidget.addWidget(self.page_5)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.page_2)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.download_groupBox = QtWidgets.QGroupBox(parent=self.page_2)
        self.download_groupBox.setObjectName("download_groupBox")
        self.download_layout = QtWidgets.QVBoxLayout(self.download_groupBox)
        self.download_layout.setObjectName("download_layout")
        self.download_groupBox_all_layout = QtWidgets.QVBoxLayout()
        self.download_groupBox_all_layout.setObjectName("download_groupBox_all_layout")
        self.download_groupBox_top_layout = QtWidgets.QHBoxLayout()
        self.download_groupBox_top_layout.setObjectName("download_groupBox_top_layout")
        self.download_comboBox = QtWidgets.QComboBox(parent=self.download_groupBox)
        self.download_comboBox.setObjectName("download_comboBox")
        self.download_comboBox.addItem("")
        self.download_comboBox.addItem("")
        self.download_groupBox_top_layout.addWidget(self.download_comboBox)
        self.download_lineEdit = QtWidgets.QLineEdit(parent=self.download_groupBox)
        self.download_lineEdit.setObjectName("download_lineEdit")
        self.download_groupBox_top_layout.addWidget(self.download_lineEdit)
        self.download_pushButton = QtWidgets.QPushButton(parent=self.download_groupBox)
        self.download_pushButton.setObjectName("download_pushButton")
        self.download_groupBox_top_layout.addWidget(self.download_pushButton)
        self.download_groupBox_all_layout.addLayout(self.download_groupBox_top_layout)
        self.download_tableView = QtWidgets.QTableView(parent=self.download_groupBox)
        self.download_tableView.setObjectName("download_tableView")
        self.download_groupBox_all_layout.addWidget(self.download_tableView)
        self.download_layout.addLayout(self.download_groupBox_all_layout)
        self.horizontalLayout_8.addWidget(self.download_groupBox)
        self.stackedWidget.addWidget(self.page_2)
        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)
        self.frame_layout.addLayout(self.gridLayout)
        self.centralwidget_layout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.log_groupBox.setTitle(_translate("MainWindow", "日志"))
        self.setting_groupBox.setTitle(_translate("MainWindow", "设置"))
        self.get_page_pushButton.setText(_translate("MainWindow", "获取列表"))
        self.download_page_pushButton.setText(_translate("MainWindow", "下载列表"))
        self.search_page_pushButton.setText(_translate("MainWindow", "搜索"))
        self.log_pushButton.setText(_translate("MainWindow", "清空日志"))
        self.headers_label.setText(_translate("MainWindow", "headers"))
        self.headers_button.setText(_translate("MainWindow", "更新"))
        self.cookies_label.setText(_translate("MainWindow", "cookies"))
        self.cookies_button.setText(_translate("MainWindow", "更新"))
        self.proxy_label.setText(_translate("MainWindow", "proxy"))
        self.proxy_button.setText(_translate("MainWindow", "更新"))
        self.get_groupBox.setTitle(_translate("MainWindow", "获取列表"))
        self.get_comboBox.setItemText(0, _translate("MainWindow", "名称"))
        self.get_comboBox.setItemText(1, _translate("MainWindow", "id"))
        self.get_pushButton.setText(_translate("MainWindow", "搜索"))
        self.search_groupBox.setTitle(_translate("MainWindow", "搜索列表"))
        self.search_start_label_2.setText(_translate("MainWindow", "开始"))
        self.search_end_label.setText(_translate("MainWindow", "结束"))
        self.search_button.setText(_translate("MainWindow", "搜索"))
        self.download_groupBox.setTitle(_translate("MainWindow", "下载列表"))
        self.download_comboBox.setItemText(0, _translate("MainWindow", "名称"))
        self.download_comboBox.setItemText(1, _translate("MainWindow", "id"))
        self.download_pushButton.setText(_translate("MainWindow", "搜索"))

class base_page:
    """页面逻辑基类"""
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
    """日志页面逻辑"""
    
    class LOG_TYPE:
        INFO = 'info'
        ERROR = 'error'
        WARNING = 'warning'
        DEBUG = 'debug'

    LOG_COLORS = {
        LOG_TYPE.INFO: QColor(0, 180, 0),    # Green
        LOG_TYPE.ERROR: QColor(220, 0, 0),   # Red
        LOG_TYPE.WARNING: QColor(220, 220, 0), # Yellow
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
        """对外接口：入队日志（供其他页面调用，线程安全）
        :param content: 日志内容
        :param log_type: 日志类型
        """
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
        # 清空队列
        with self.log_queue.mutex:
            self.log_queue.queue.clear()
        
        self.add_log("日志已清空", self.LOG_TYPE.INFO)

    def test_log(self, num: int):
        """测试日志功能"""
        ls = [i for i in range(1, 10)]
        types = [self.LOG_TYPE.INFO, self.LOG_TYPE.ERROR, self.LOG_TYPE.WARNING, self.LOG_TYPE.DEBUG]
        for i in range(num):
            self.add_log(f'测试日志{i}' * random.choice(ls), random.choice(types))

class setting_page(base_page):
    """设置页面逻辑"""

    def init(self):
        # 页面切换逻辑
        self.ui.get_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.search_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.download_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(2))

        # 功能按钮
        self.ui.cookies_button.clicked.connect(self.update_cookies)
        # 预留接口
        # self._ljp_ui.headers_button.clicked.connect(self.update_headers)
        # self._ljp_ui.proxy_button.clicked.connect(self.update_proxy)

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
    """搜索页面逻辑"""
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.init_table()
        self.ui.search_button.clicked.connect(self.on_search_clicked)

    def init_table(self):
        self.search_model = xs_table_model(self.COLUMNS, parent=self.ui.search_tableView)
        self.ui.search_tableView.setModel(self.search_model)
        self.ui.search_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        op_col_idx = self.COLUMNS.index('操作')
        delegate = xs_tableview_Delegate(self, self.ui.search_tableView, op_col_idx)
        self.ui.search_tableView.setItemDelegateForColumn(op_col_idx, delegate)
    def on_search_clicked(self):
        self.log('搜索按钮点击')
        # 示例数据，实际应调用后端接口
        mock_books = [
            MockBook("1001", "三体", "3"),
            MockBook("1002", "斗罗大陆", "10"),
            MockBook("1003", "百年孤独", "1")
        ]
        
        if self.search_model:
            # 清空旧数据（可选，根据需求）
            # self.search_model.removeRows(0, self.search_model.rowCount())
            # self.search_model.book_list.clear()

            for book in mock_books:
                # 使用 append_data 确保 book_list 同步更新
                self.search_model.append_data(book)

    def button_click(self, index: QModelIndex):
        """处理表格按钮点击"""
        row = index.row()
        try:
            # 尝试从 model 的 book_list 获取数据
            if hasattr(self.search_model, 'book_list') and row < len(self.search_model.book_list):
                book = self.search_model.book_list[row]
                self.log(f"搜索页点击: ID=[{book.id}], 名称=[{book.title}], 章节=[{book.total_chapters}]")
            else:
                 # Fallback: 从 item 获取
                 id_item = self.search_model.item(row, 0)
                 name_item = self.search_model.item(row, 1)
                 self.log(f"搜索页点击(Item): ID=[{id_item.text()}], 名称=[{name_item.text()}]")
        except Exception as e:
            self.log(f"获取书籍信息失败: {e}", "error")

class download_page(base_page):
    """下载页面逻辑"""
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.init_table()
        self.ui.download_pushButton.clicked.connect(self.button_click)

    def init_table(self):
        self.download_model = xs_table_model(self.COLUMNS, parent=self.ui.download_tableView)
        self.ui.download_tableView.setModel(self.download_model)
        self.ui.download_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def add_to_list(self, book_info):
        """添加到下载列表"""
        self.download_model.append_data(book_info)
        # 假设 book_info 是对象或字典，这里做个简单兼容
        title = getattr(book_info, 'title', 'Unknown')
        self.log(f"已添加到下载列表: {title}")

    def button_click(self):
        self.log('下载按钮点击')

class get_page(base_page):
    """获取列表页面逻辑"""
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.init_table()
        self.ui.get_pushButton.clicked.connect(self.on_search_clicked)

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
                self.log("后端逻辑未连接 (XS instance missing)，加载模拟数据", "warning")
                mock_books = [
                    MockBook("2001", "Python编程", "20"),
                    MockBook("2002", "算法导论", "15"),
                ]
                if self.get_model:
                     for book in mock_books:
                         self.get_model.append_data(book)

        except Exception as e:
            self.log(f'获取按钮点击异常: {e}', "error")

    def button_click(self, index: QModelIndex):
        """表格中的操作按钮点击事件"""
        row = index.row()
        try:
            # 获取书籍信息 (假设 model 有 book_list 属性)
            book_info = self.get_model.book_list[row]
            
            # 打印详细信息
            self.log(f"获取页点击下载: ID=[{book_info.id}], 名称=[{book_info.title}], 状态=[{book_info.status}]")

            op_col = self.COLUMNS.index('操作')
            status_col = self.COLUMNS.index('状态')
            
            # 更新状态
            self.get_model.setData(self.get_model.index(row, status_col), '下载中', Qt.ItemDataRole.DisplayRole)
            self.get_model.setData(self.get_model.index(row, op_col), '...', Qt.ItemDataRole.DisplayRole)
            
            # 触发后端下载
            if self.main_window.xs:
                self.main_window.xs.ui_download_book(book_info)

            # 添加到下载列表
            self.main_window.download_page.add_to_list(book_info)
            
        except IndexError:
            self.log("索引错误: 无法找到对应的信息", "error")
        except Exception as e:
            self.log(f"下载触发失败: {e}", "error")

class Xs_ui(QMainWindow):
    """主窗口逻辑"""
    def __init__(self, xs_backend=None):
        super().__init__()
        self.xs_backend = xs_backend
        self.xs = None  # 后端实例引用

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 初始化各页面逻辑
        self.setting_page = setting_page(self)
        self.download_page = download_page(self)
        self.log_page = Log_page(self)
        self.search_page = search_page(self)
        self.get_page = get_page(self)

        if self.xs_backend:
             self.set_xs(self.xs_backend)

        self.log_page.add_log("UI 初始化完成")

    def add_book(self, book):
        """添加书籍到获取列表"""
        if self.get_page and hasattr(self.get_page, 'get_model'):
            self.get_page.get_model.append_data(book)

    def set_xs(self, xs):
        """设置后端实例"""
        self.xs = xs

    def closeEvent(self, event):
        """关闭窗口时的确认提示"""
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
            # 模拟 Session
            self.session = type('obj', (object,), {
                'cookie_jar': type('obj', (object,), {
                    'clear': lambda: None, 
                    'update_cookies': lambda x: print(f"Cookies updated: {x}")
                })()
            })
            self.ui_session = self.session

        def run(self):
            new_novels = [
                ["1001", "三体", "3", "完结", ""],
                ["1002", "斗罗大陆", "10", "连载", ""],
            ]
            print("Running mock backend...")
            # 模拟数据填充
            # 注意：实际使用需要 Xs_table_model 支持 append_data 格式
            pass

        def ui_download_book(self, book): 
            print(f"Downloading {book}")

    xs_ui = Xs_ui()
    m = MockXs(xs_ui)
    xs_ui.set_xs(m)
    xs_ui.show()
    
    sys.exit(app.exec())
