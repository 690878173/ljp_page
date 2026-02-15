import ast
import queue
import random
from datetime import datetime
import sys

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QTimer, Qt, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtWidgets import QMainWindow, QApplication, QHeaderView, QAbstractItemView, QMessageBox
from ljp_page._ljp_ui.tableview.xs_tableview import xs_tableview_Delegate,xs_table_model
from lxml import etree

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
    def __init__(self,main_window:'Xs_ui'):
        self.main_window = main_window
        self.ui = self.main_window.ui
        self.init()

    def init(self):
        pass

    def log(self, message: str, level: str = "info"):
        """Shortcut for logging."""
        self.main_window.log_page.add_log(message, level)

class Log_page(base_page):
    class LOG_TYPE:
        INFO = 'info'
        ERROR = 'error'
        WARNING = 'warning'
        DEBUG = 'debug'

    LOG_COLORS = {
        LOG_TYPE.INFO: QColor(0, 180, 0),
        LOG_TYPE.ERROR: QColor(220, 0, 0),
        LOG_TYPE.WARNING: QColor(220, 220, 0),
        LOG_TYPE.DEBUG: QColor(100, 100, 100)
    }

    def init(self):
        self.log_queue = queue.Queue()
        self.init_log_model()
        self.init_timer()

    def init_log_model(self):
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

    def add_log(self, content, log_type="info"):
        """对外接口：入队日志（供其他页面调用）
        :param content: 日志内容
        :param log_type: 日志类型，可选"info","success","error"
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
            timestamp, log_type, content = self.log_queue.get()

            prefix_map = {
                'info': '[信息]',
                'error': '[错误]',
                'warning': '[警告]',
                'debug': '[调试]'
            }
            prefix = f"[{timestamp}] {prefix_map.get(log_type, '[信息]')} "
            item = QStandardItem(prefix + str(content))
            item.setForeground(self.LOG_COLORS.get(log_type, self.LOG_COLORS['info']))
            item.setEditable(False)
            new_rows.append(item)

            self.log_queue.task_done()  # 通知队列已经取出完成
            count += 1

        if new_rows:
            self.log_model.appendColumn(
                new_rows) if self.log_model.rowCount() == 0 else None  # fix for appendRow if model is empty/weird
            for item in new_rows:
                self.log_model.appendRow(item)

        # # 每次最多取100条
        # batch_logs = []
        # max_fetch = 100
        # count = 0
        # while not self.log_queue.empty() and count < max_fetch:
        #     batch_logs.append(self.log_queue.get())
        #     count += 1
        #     self.log_queue.task_done() # 通知队列已经取出完成
        #
        # # 批量创建日志项
        # log_items = []
        # for timestamp, log_type, content in batch_logs:
        #     if log_type == self.log_type[0]:
        #         prefix = f"[{timestamp}] [信息] "
        #         color = QColor(0, 180, 0)
        #     elif log_type == self.log_type[1]:
        #         prefix = f"[{timestamp}] [错误] "
        #         color = QColor(220, 0, 0)
        #
        #     elif log_type == self.log_type[2]:
        #         prefix = f"[{timestamp}] [警告] "
        #         color = QColor(220, 220, 0)
        #     else:
        #         prefix = f"[{timestamp}] [调试] "
        #         color = QColor(100, 100, 100)
        #
        #     item = QStandardItem(prefix + content)
        #     item.setForeground(color)
        #     item.setEditable(False)
        #     log_items.append(item)
        #
        # # 批量插入模型
        # start_row = self.log_model.rowCount()
        # self.log_model.beginInsertRows(QtCore.QModelIndex(), start_row, start_row + len(log_items) - 1)
        # for item in log_items:
        #     self.log_model.appendRow(item)
        # self.log_model.endInsertRows()

        # # 滚动到最新
        # self.main_window._ljp_ui.log_listView.scrollToBottom()

    def clear_log(self):
        """清空日志(包括队列里的)"""
        # # 清空模型
        # self.log_model.removeRows(0, self.log_model.rowCount())
        # # 清空队列
        # while not self.log_queue.empty():
        #     self.log_queue.get()
        #     self.log_queue.task_done()

        self.log_model.clear()
        with self.log_queue.mutex:
            self.log_queue.queue.clear()
        # 记录清空日志
        self.add_log("日志已清空", "info")

    def test_log(self,num):
        ls = [i for i in range(1,10)]
        for i in range(num):
            self.add_log(f'测试日志{i}'*random.choice(ls),random.choice(self.log_type))

class setting_page(base_page):

    def init(self):
        self.ui.get_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.search_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.download_page_pushButton.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(2))

        self.ui.cookies_button.clicked.connect(self.update_cookies)
        # self._ljp_ui.headers_button.clicked.connect(self.update_headers) # To be implemented
        # self._ljp_ui.proxy_button.clicked.connect(self.update_proxy) # To be implemented

    def update_cookies(self):
        cookies_text = self.ui.cookies_lineEdit.text().strip()
        if not cookies_text:
            self.log("请输入cookies", "warning")
            return
        try:
            if cookies_text.startswith('{') and cookies_text.endswith('}'):
                cookies = ast.literal_eval(cookies_text)
            else:
                self.log("Cookies格式不正确，请输入字典或JSON", "warning")
                return
            if not isinstance(cookies, dict):
                self.log("Cookies必须是字典格式", "warning")
                return
            if not self.main_window.xs or not self.main_window.xs.session:
                self.log("Session未初始化", "warning")
                return

            for s in [self.main_window.xs.ui_session, self.main_window.xs.session]:
                if s:
                    s.cookie_jar.clear()
                    s.cookie_jar.update_cookies(cookies)

            self.log("Cookies已更新", "info")
        except Exception as e:
            print(e)
            self.log(f"Cookies更新失败: {str(e)}", "error")

class search_page(base_page):
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.ui.stackedWidget.setCurrentIndex(1)
        self.search_model = xs_table_model(self.COLUMNS, parent=self.ui.search_tableView)
        self.ui.search_tableView.setModel(self.search_model)
        self.ui.search_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # 列伸缩

        op_col_idx = self.COLUMNS.index('操作')
        delegate = xs_tableview_Delegate(self, self.ui.search_tableView, op_col_idx)
        self.ui.search_tableView.setItemDelegateForColumn(op_col_idx, delegate)

        self.ui.search_button.clicked.connect(self.on_search_clicked)

    def on_search_clicked(self):
        self.log('搜索按钮点击')
        # new_novels = [
        #     ["三体", "刘慈欣", "科幻", "https://example.com/santi.txt"],
        #     ["斗罗大陆", "唐家三少", "玄幻", "https://example.com/douluo.txt"],
        #     ["盗墓笔记", "南派三叔", "悬疑", "https://example.com/daomu.txt"],
        # ]
        # for novel in new_novels:
        #
        #     items = []
        #     for i in novel[:-1]:
        #         items.append(QStandardItem(i))
        #     # items[3].setEditable(True)
        #     self.search_model.appendRow(items)
        new_novels = [
            ["1001", "三体", "3", "完结", ""],
            ["1002", "斗罗大陆", "10", "连载", ""],
        ]
        # In a real scenario, you would clear model and add new rows
        # For now, just adding rows to show it works
        for novel in new_novels:
            items = [QStandardItem(x) for x in novel]
            self.search_model.appendRow(items)

    def button_click(self, index: QModelIndex):
        self.log(f"搜索页点击了第 {index.row()} 行,名称为:{index.row}")

class download_page(base_page):
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.download_model = xs_table_model(self.COLUMNS, parent=self.ui.download_tableView)
        self.ui.download_tableView.setModel(self.download_model)
        self.ui.download_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # 列伸缩
        self.ui.download_pushButton.clicked.connect(self.button_click)

    def add_to_list(self, book_info):
        """Adds a book to the download list."""
        self.download_model.append_data(book_info)
        self.log(f"已添加到下载列表: {getattr(book_info, 'title', 'Unknown')}")



    def button_click(self):
        self.log('下载按钮点击')

class get_page(base_page):
    COLUMNS = ['id', '名称', '数量', '状态', '操作']

    def init(self):
        self.get_model = xs_table_model(self.COLUMNS, parent=self.ui.get_tableView)
        self.ui.get_tableView.setModel(self.get_model)
        self.ui.get_tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # 列伸缩
        self.ui.get_tableView.setMouseTracking(True)

        op_col_idx = self.COLUMNS.index('操作')
        delegate = xs_tableview_Delegate(self, self.ui.get_tableView, op_col_idx)
        self.ui.get_tableView.setItemDelegateForColumn(op_col_idx, delegate)

        self.ui.get_pushButton.clicked.connect(self.on_search_clicked)


    def on_search_clicked(self):
        self.log('获取按钮点击')
        try:
            if self.main_window.xs:
                self.main_window.xs.run()  # Assuming this populates the list
            else:
                self.log("后端逻辑未连接 (XS instance missing)", "error")
        except Exception as e:
            self.log(f'获取按钮点击异常:{e}')

    def button_click(self,index: QModelIndex):
        row = index.row()
        self.log(f"点击了第 {row} 行下载")
        try:
            book_info = self.get_model.book_list[row]
            op_col = self.COLUMNS.index('操作')
            status_col = self.COLUMNS.index('状态')
            self.get_model.setData(self.get_model.index(row, status_col), '下载中', Qt.ItemDataRole.DisplayRole)
            self.get_model.setData(self.get_model.index(row, op_col), '...', Qt.ItemDataRole.DisplayRole)
            if self.main_window.xs:
                self.main_window.xs.ui_download_book(book_info)

            self.main_window.download_page.add_to_list(book_info)
        except IndexError:
            self.log("索引错误: 无法找到对应的信息", "error")
        except Exception as e:
            self.log(f"下载触发失败: {e}", "error")

class Xs_ui(QMainWindow):
    def __init__(self,xs_backend=None):
        super().__init__()
        self.xs_backend = xs_backend

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setting_page = setting_page(self)
        self.download_page = download_page(self)
        self.log_page = Log_page(self)
        self.search_page = search_page(self)
        self.get_page = get_page(self)

        self.log_page.add_log("UI初始化完成")

    def add_book(self,book):
        self.get_page.get_model.append_data(book)

    def set_xs(self,xs):
        self.xs = xs

    def closeEvent(self, event):
        """Handle cleanup on close."""
        reply = QMessageBox.question(self, '退出', '确定要退出吗?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()



if __name__ == '__main__':

    app = QApplication(sys.argv)
    class MockXs:
        def __init__(self,xs_ui:Xs_ui):
            self.xs = xs_ui
            self.session = type('obj', (object,), {
                'cookie_jar': type('obj', (object,), {'clear': lambda: None, 'update_cookies': lambda x: None})()})
            self.ui_session = self.session

        def run(self):
            new_novels = [
                ["1001", "三体", "3", "完结", ""],
                ["1002", "斗罗大陆", "10", "连载", ""],
            ]
            # In a real scenario, you would clear model and add new rows
            # For now, just adding rows to show it works
            for novel in new_novels:
                items = [QStandardItem(x) for x in novel]
                self.xs.get_page.get_model.append_data(items)

        def ui_download_book(self, book): print(f"Downloading {book}")

    xs_ui = Xs_ui()
    m = MockXs(xs_ui)
    xs_ui.set_xs(m)
    xs_ui.show()
    # for i in range(100000):
    #     xs_ui.log_page.add_log(f'{i}')
    sys.exit(app.exec())

