# -*- coding: utf-8 -*-

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 800)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        # 主布局：垂直布局，分为上下两部分
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.main_layout.setObjectName("main_layout")

        # --- 上部分：堆叠窗口区域 ---
        self.top_frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.top_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.top_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.top_frame.setObjectName("top_frame")
        self.top_layout = QtWidgets.QVBoxLayout(self.top_frame)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setObjectName("top_layout")

        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.top_frame)
        self.stackedWidget.setObjectName("stackedWidget")

        # 1. 登录页面
        self.page_login = QtWidgets.QWidget()
        self.page_login.setObjectName("page_login")
        self.setup_login_page(self.page_login)
        self.stackedWidget.addWidget(self.page_login)

        # 2. 配置页面
        self.page_config = QtWidgets.QWidget()
        self.page_config.setObjectName("page_config")
        self.setup_config_page(self.page_config)
        self.stackedWidget.addWidget(self.page_config)

        # 3. 原有功能页面示例 (获取列表)
        self.page_get = QtWidgets.QWidget()
        self.page_get.setObjectName("page_get")
        self.setup_get_page(self.page_get)
        self.stackedWidget.addWidget(self.page_get)
        
        self.top_layout.addWidget(self.stackedWidget)
        
        # 将上部分添加到主布局，设置拉伸因子，使其占据主要空间
        self.main_layout.addWidget(self.top_frame, stretch=7)

        # --- 下部分：日志与功能设置区域 ---
        self.bottom_frame = QtWidgets.QFrame(parent=self.centralwidget)
        self.bottom_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.bottom_frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.bottom_frame.setObjectName("bottom_frame")
        
        # 下部分布局：水平布局，左日志，右设置
        self.bottom_layout = QtWidgets.QHBoxLayout(self.bottom_frame)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setObjectName("bottom_layout")

        # 左边：日志区域
        self.log_groupBox = QtWidgets.QGroupBox(parent=self.bottom_frame)
        self.log_groupBox.setObjectName("log_groupBox")
        self.log_layout = QtWidgets.QVBoxLayout(self.log_groupBox)
        self.log_listView = QtWidgets.QListView(parent=self.log_groupBox)
        self.log_listView.setObjectName("log_listView")
        self.log_layout.addWidget(self.log_listView)
        
        self.bottom_layout.addWidget(self.log_groupBox, stretch=6) # 日志占较多宽度

        # 右边：设置功能区域
        self.func_groupBox = QtWidgets.QGroupBox(parent=self.bottom_frame)
        self.func_groupBox.setObjectName("func_groupBox")
        self.func_layout = QtWidgets.QVBoxLayout(self.func_groupBox)
        
        # 页面切换按钮区
        self.nav_layout = QtWidgets.QGridLayout()
        self.btn_login_page = QtWidgets.QPushButton("登录页面")
        self.btn_config_page = QtWidgets.QPushButton("配置页面")
        self.btn_get_page = QtWidgets.QPushButton("获取列表")
        self.nav_layout.addWidget(self.btn_login_page, 0, 0)
        self.nav_layout.addWidget(self.btn_config_page, 0, 1)
        self.nav_layout.addWidget(self.btn_get_page, 1, 0)
        
        self.func_layout.addLayout(self.nav_layout)
        
        # 其他功能按钮
        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.func_layout.addWidget(self.line)
        
        self.btn_clear_log = QtWidgets.QPushButton("清空日志")
        self.func_layout.addWidget(self.btn_clear_log)
        
        self.func_layout.addStretch() # 底部弹簧

        self.bottom_layout.addWidget(self.func_groupBox, stretch=4) # 设置占较少宽度

        # 将下部分添加到主布局
        self.main_layout.addWidget(self.bottom_frame, stretch=3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(0)
        
        # 信号槽连接
        self.btn_login_page.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.btn_config_page.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.btn_get_page.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setup_login_page(self, parent_widget):
        """设计登录页面"""
        layout = QtWidgets.QVBoxLayout(parent_widget)
        
        # 居中容器
        center_widget = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QtWidgets.QLabel("系统登录")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title_label)
        
        form_layout = QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.login_user_edit = QtWidgets.QLineEdit()
        self.login_user_edit.setPlaceholderText("请输入用户名")
        self.login_pwd_edit = QtWidgets.QLineEdit()
        self.login_pwd_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.login_pwd_edit.setPlaceholderText("请输入密码")
        
        form_layout.addRow("用户名:", self.login_user_edit)
        form_layout.addRow("密码:", self.login_pwd_edit)
        
        center_layout.addLayout(form_layout)
        
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_login = QtWidgets.QPushButton("登录")
        self.btn_login.setMinimumHeight(35)
        btn_layout.addWidget(self.btn_login)
        
        center_layout.addLayout(btn_layout)
        
        layout.addStretch()
        layout.addWidget(center_widget)
        layout.addStretch()

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
        modules = ["数据清洗模块", "图片压缩模块", "自动翻译模块", "格式转换模块", "云端备份模块", "消息推送模块", "定时任务模块"]
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
        scroll_layout.addStretch() # 填充底部空白
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def setup_get_page(self, parent_widget):
        """设计获取列表页面 (参考原有)"""
        layout = QtWidgets.QVBoxLayout(parent_widget)
        
        group_box = QtWidgets.QGroupBox("获取列表")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 顶部搜索栏
        top_layout = QtWidgets.QHBoxLayout()
        self.combo_search_type = QtWidgets.QComboBox()
        self.combo_search_type.addItems(["名称", "ID"])
        top_layout.addWidget(self.combo_search_type)
        
        self.line_search = QtWidgets.QLineEdit()
        self.line_search.setPlaceholderText("请输入搜索关键词...")
        top_layout.addWidget(self.line_search)
        
        self.btn_search = QtWidgets.QPushButton("搜索")
        top_layout.addWidget(self.btn_search)
        
        group_layout.addLayout(top_layout)
        
        # 表格区域
        self.table_view = QtWidgets.QTableView()
        group_layout.addWidget(self.table_view)
        
        layout.addWidget(group_box)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "UI 新界面设计演示"))
        self.log_groupBox.setTitle(_translate("MainWindow", "运行日志"))
        self.func_groupBox.setTitle(_translate("MainWindow", "功能控制区"))
        self.page_login.setWindowTitle(_translate("MainWindow", "登录"))
        self.page_config.setWindowTitle(_translate("MainWindow", "配置"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
