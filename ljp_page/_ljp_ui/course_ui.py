# -*- coding: utf-8 -*-

"""
抢课系统 UI
根据 sm.txt 需求重新设计，移除书籍相关内容，仅保留抢课功能。
使用 PyQt6 原生组件。
"""

import sys
import queue
import json
import ast
from datetime import datetime
from typing import Optional, Dict, List, Any

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QTimer, Qt, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QHeaderView, QAbstractItemView, QMessageBox,
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGroupBox, QListView,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QStackedWidget, QGridLayout,
    QScrollArea, QFormLayout
)

# -----------------------------------------------------------------------------
# 模拟数据对象
# -----------------------------------------------------------------------------
class CourseInfo:
    """课程信息数据模型"""
    def __init__(self, id, name, teacher, block, remark=""):
        self.id = id
        self.name = name
        self.teacher = teacher
        self.block = block
        self.remark = remark

# -----------------------------------------------------------------------------
# 基础页面类
# -----------------------------------------------------------------------------
class BasePage(QWidget):
    """
    页面基类，提供日志记录快捷方式和初始化入口
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.init_logic()

    def init_ui(self):
        """初始化 UI 组件"""
        pass

    def init_logic(self):
        """初始化业务逻辑"""
        pass

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        if hasattr(self.main_window, 'log_area'):
            self.main_window.log_area.add_log(message, level)
        else:
            print(f"[{level.upper()}] {message}")

# -----------------------------------------------------------------------------
# 1. 登录页面
# -----------------------------------------------------------------------------
class LoginPage(BasePage):
    """
    登录页面
    """
    def init_ui(self):
        self.setObjectName("login_page")
        layout = QVBoxLayout(self)
        
        # 居中容器
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        self.lbl_title = QLabel("教务抢课系统登录")
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.lbl_title)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.edit_username = QLineEdit()
        self.edit_username.setPlaceholderText("请输入学号/工号")
        self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_password.setPlaceholderText("请输入密码")
        
        form_layout.addRow("账号:", self.edit_username)
        form_layout.addRow("密码:", self.edit_password)
        center_layout.addLayout(form_layout)
        
        # 登录按钮
        self.btn_login = QPushButton("登录")
        self.btn_login.setMinimumHeight(35)
        self.btn_login.clicked.connect(self.on_login_clicked)
        center_layout.addWidget(self.btn_login)
        
        layout.addStretch()
        layout.addWidget(center_widget)
        layout.addStretch()

    def on_login_clicked(self):
        username = self.edit_username.text()
        password = self.edit_password.text()
        if not username or not password:
            self.log("请输入账号和密码", "warning")
            return
        
        self.log(f"尝试登录用户: {username}")
        # TODO: 调用后端登录接口
        # 模拟登录成功
        self.log("登录成功", "info")
        # 跳转到配置页面 (Index 1)
        self.main_window.stacked_widget.setCurrentIndex(1)

# -----------------------------------------------------------------------------
# 2. 配置页面
# -----------------------------------------------------------------------------
class ConfigPage(BasePage):
    """
    配置页面
    包含：需要抢的课程ID，不要抢的课程ID，板块选择，启动开关，保存按钮
    """
    def init_ui(self):
        self.setObjectName("config_page")
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form_layout = QVBoxLayout(content)
        
        # 1. 抢课 ID 配置
        grp_ids = QGroupBox("课程 ID 配置")
        layout_ids = QFormLayout(grp_ids)
        
        self.edit_target_ids = QTextEdit()
        self.edit_target_ids.setPlaceholderText("请输入需要抢的课程ID，多个用逗号分隔")
        self.edit_target_ids.setMaximumHeight(80)
        
        self.edit_exclude_ids = QTextEdit()
        self.edit_exclude_ids.setPlaceholderText("请输入不需要抢的课程ID，多个用逗号分隔")
        self.edit_exclude_ids.setMaximumHeight(80)
        
        layout_ids.addRow("抢课 ID:", self.edit_target_ids)
        layout_ids.addRow("排除 ID:", self.edit_exclude_ids)
        form_layout.addWidget(grp_ids)
        
        # 2. 板块选择
        grp_blocks = QGroupBox("板块选择 (多选)")
        layout_blocks = QVBoxLayout(grp_blocks)
        
        self.chk_blocks = []
        blocks = ["通识必修", "通识选修", "专业必修", "专业选修", "实践教学", "创新创业", "跨专业", "辅修", "重修", "其它"]
        
        # 使用网格布局放置 CheckBox
        grid_blocks = QGridLayout()
        for i, block_name in enumerate(blocks):
            chk = QCheckBox(block_name)
            self.chk_blocks.append(chk)
            grid_blocks.addWidget(chk, i // 4, i % 4)
            
        layout_blocks.addLayout(grid_blocks)
        form_layout.addWidget(grp_blocks)
        
        # 3. 启动开关
        grp_switch = QGroupBox("功能开关")
        layout_switch = QHBoxLayout(grp_switch)
        self.chk_enable_block = QCheckBox("启用板块抢课")
        layout_switch.addWidget(self.chk_enable_block)
        layout_switch.addStretch()
        form_layout.addWidget(grp_switch)
        
        # 4. 保存按钮
        self.btn_save = QPushButton("保存配置")
        self.btn_save.setMinimumHeight(40)
        self.btn_save.clicked.connect(self.save_config)
        form_layout.addWidget(self.btn_save)
        
        form_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def save_config(self):
        target_ids = self.edit_target_ids.toPlainText().strip()
        exclude_ids = self.edit_exclude_ids.toPlainText().strip()
        selected_blocks = [chk.text() for chk in self.chk_blocks if chk.isChecked()]
        enable_block = self.chk_enable_block.isChecked()
        
        self.log("配置已保存:", "info")
        self.log(f"  - 抢课ID: {target_ids}")
        self.log(f"  - 排除ID: {exclude_ids}")
        self.log(f"  - 选中板块: {selected_blocks}")
        self.log(f"  - 启用板块抢课: {enable_block}")

# -----------------------------------------------------------------------------
# 3. 课程展示页面
# -----------------------------------------------------------------------------
class CourseDisplayPage(BasePage):
    """
    课程展示页面
    展示内置的课程数据
    """
    def init_ui(self):
        self.setObjectName("course_display_page")
        layout = QVBoxLayout(self)
        
        self.lbl_title = QLabel("可选课程列表")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.lbl_title)
        
        # 课程表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "课程名称", "教师", "所属板块", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # 不可编辑
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # 选中整行
        layout.addWidget(self.table)
        
        # 刷新按钮 (模拟获取数据)
        self.btn_refresh = QPushButton("刷新课程数据")
        self.btn_refresh.clicked.connect(self.load_courses)
        layout.addWidget(self.btn_refresh)
        
        # 初始加载
        self.load_courses()

    def load_courses(self):
        self.log("正在加载课程数据...", "info")
        # 模拟数据
        mock_courses = [
            CourseInfo("1001", "高等数学", "张三", "通识必修", "难度高"),
            CourseInfo("1002", "大学英语", "李四", "通识必修", ""),
            CourseInfo("2001", "Python程序设计", "王五", "专业选修", "推荐"),
            CourseInfo("3005", "音乐鉴赏", "赵六", "通识选修", "抢手"),
        ]
        
        self.table.setRowCount(0)
        for row, course in enumerate(mock_courses):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(course.id))
            self.table.setItem(row, 1, QTableWidgetItem(course.name))
            self.table.setItem(row, 2, QTableWidgetItem(course.teacher))
            self.table.setItem(row, 3, QTableWidgetItem(course.block))
            self.table.setItem(row, 4, QTableWidgetItem(course.remark))
            
        self.log(f"加载完成，共 {len(mock_courses)} 门课程", "info")

# -----------------------------------------------------------------------------
# 4. 抢课页面
# -----------------------------------------------------------------------------
class GrabPage(BasePage):
    """
    抢课页面
    倒计时 + 状态表格
    """
    def init_ui(self):
        self.setObjectName("grab_page")
        layout = QVBoxLayout(self)
        
        # 倒计时区域
        top_bar = QHBoxLayout()
        self.lbl_timer_title = QLabel("距离抢课开始还有:")
        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        top_bar.addWidget(self.lbl_timer_title)
        top_bar.addWidget(self.lbl_timer)
        top_bar.addStretch()
        
        self.btn_start = QPushButton("开始抢课")
        self.btn_start.clicked.connect(self.start_grabbing)
        top_bar.addWidget(self.btn_start)
        layout.addLayout(top_bar)
        
        # 抢课状态表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["课程ID", "课程名称", "当前状态", "信息"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # 模拟倒计时
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.remaining_seconds = 60 # 模拟60秒
        self.timer.start(1000)

    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            m, s = divmod(self.remaining_seconds, 60)
            h, m = divmod(m, 60)
            self.lbl_timer.setText(f"{h:02d}:{m:02d}:{s:02d}")
        else:
            self.lbl_timer.setText("抢课已开始！")
            self.timer.stop()

    def start_grabbing(self):
        self.log("开始执行抢课任务...", "info")
        # 模拟添加抢课任务状态
        tasks = [
            ("1001", "高等数学", "正在抢课..."),
            ("3005", "音乐鉴赏", "等待中...")
        ]
        self.table.setRowCount(0)
        for row, (cid, cname, status) in enumerate(tasks):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(cid))
            self.table.setItem(row, 1, QTableWidgetItem(cname))
            self.table.setItem(row, 2, QTableWidgetItem(status))
            self.table.setItem(row, 3, QTableWidgetItem(""))

# -----------------------------------------------------------------------------
# 5. 开发者管理页面
# -----------------------------------------------------------------------------
class DeveloperPage(BasePage):
    """
    开发者管理页面
    线程数配置等
    """
    def init_ui(self):
        self.setObjectName("developer_page")
        layout = QVBoxLayout(self)
        
        grp_dev = QGroupBox("高级设置")
        form = QFormLayout(grp_dev)
        
        self.spin_thread_count = QSpinBox()
        self.spin_thread_count.setRange(1, 50)
        self.spin_thread_count.setValue(5)
        
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(100, 5000)
        self.spin_interval.setValue(500)
        self.spin_interval.setSuffix(" ms")
        
        self.chk_debug_mode = QCheckBox("开启调试模式 (输出详细日志)")
        
        form.addRow("抢课线程数:", self.spin_thread_count)
        form.addRow("请求间隔:", self.spin_interval)
        form.addRow(self.chk_debug_mode)
        
        layout.addWidget(grp_dev)
        
        self.btn_apply = QPushButton("应用设置")
        self.btn_apply.clicked.connect(self.apply_settings)
        layout.addWidget(self.btn_apply)
        
        layout.addStretch()

    def apply_settings(self):
        threads = self.spin_thread_count.value()
        interval = self.spin_interval.value()
        debug = self.chk_debug_mode.isChecked()
        self.log(f"开发者设置已应用: 线程={threads}, 间隔={interval}ms, 调试={debug}", "warning")

# -----------------------------------------------------------------------------
# 日志区域组件
# -----------------------------------------------------------------------------
class LogArea(QGroupBox):
    """
    日志显示区域
    """
    def __init__(self):
        super().__init__("系统日志")
        self.init_ui()
        self.log_queue = queue.Queue()
        
        # 定时器刷新日志
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_log_queue)
        self.timer.start(100) # 100ms 刷新一次

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.list_view = QListView()
        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)
        self.list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.list_view)

    def add_log(self, message: str, level: str = "info"):
        """添加日志到队列 (线程安全)"""
        self.log_queue.put((datetime.now(), level, message))

    def process_log_queue(self):
        """处理日志队列并更新 UI"""
        while not self.log_queue.empty():
            time_obj, level, msg = self.log_queue.get()
            time_str = time_obj.strftime("%H:%M:%S")
            
            item = QStandardItem(f"[{time_str}] [{level.upper()}] {msg}")
            
            # 设置颜色
            if level == "error":
                item.setForeground(QColor("red"))
            elif level == "warning":
                item.setForeground(QColor("orange"))
            elif level == "debug":
                item.setForeground(QColor("gray"))
            else:
                item.setForeground(QColor("green"))
                
            self.model.appendRow(item)
            self.list_view.scrollToBottom()

# -----------------------------------------------------------------------------
# 控制台/导航区域组件
# -----------------------------------------------------------------------------
class ControlArea(QGroupBox):
    """
    右下角控制台：包含导航按钮
    """
    def __init__(self, main_window):
        super().__init__("功能导航")
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 导航按钮网格
        grid = QGridLayout()
        
        self.btn_login_page = QPushButton("登录页面")
        self.btn_config_page = QPushButton("配置页面")
        self.btn_course_page = QPushButton("课程展示页面")
        self.btn_grab_page = QPushButton("抢课页面")
        self.btn_developer_page = QPushButton("开发者管理页面")
        
        # 绑定事件
        self.btn_login_page.clicked.connect(lambda: self.main_window.switch_page(0))
        self.btn_config_page.clicked.connect(lambda: self.main_window.switch_page(1))
        self.btn_course_page.clicked.connect(lambda: self.main_window.switch_page(2))
        self.btn_grab_page.clicked.connect(lambda: self.main_window.switch_page(3))
        self.btn_developer_page.clicked.connect(lambda: self.main_window.switch_page(4))
        
        grid.addWidget(self.btn_login_page, 0, 0)
        grid.addWidget(self.btn_config_page, 0, 1)
        grid.addWidget(self.btn_course_page, 1, 0)
        grid.addWidget(self.btn_grab_page, 1, 1)
        grid.addWidget(self.btn_developer_page, 2, 0, 1, 2) # 跨两列
        
        layout.addLayout(grid)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 清空日志按钮
        self.btn_clear_log = QPushButton("清空日志")
        self.btn_clear_log.clicked.connect(self.clear_log)
        layout.addWidget(self.btn_clear_log)
        
        layout.addStretch()

    def clear_log(self):
        if hasattr(self.main_window, 'log_area'):
            self.main_window.log_area.model.clear()
            self.main_window.log_area.add_log("日志已清空", "info")

# -----------------------------------------------------------------------------
# 主窗口
# -----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("教务系统抢课助手")
        self.resize(1000, 700)
        
        self.init_ui()
        self.log_area.add_log("系统初始化完成", "info")

    def init_ui(self):
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局：垂直
        main_layout = QVBoxLayout(central_widget)
        
        # --- 上部分：堆叠窗口 ---
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 初始化各个页面
        self.page_login = LoginPage(self)
        self.page_config = ConfigPage(self)
        self.page_course = CourseDisplayPage(self)
        self.page_grab = GrabPage(self)
        self.page_dev = DeveloperPage(self)
        
        # 按顺序添加 (Index 0-4)
        self.stacked_widget.addWidget(self.page_login)
        self.stacked_widget.addWidget(self.page_config)
        self.stacked_widget.addWidget(self.page_course)
        self.stacked_widget.addWidget(self.page_grab)
        self.stacked_widget.addWidget(self.page_dev)
        
        main_layout.addWidget(self.stacked_widget, stretch=7) # 上部分占70%
        
        # --- 下部分：日志与设置 ---
        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左下：日志
        self.log_area = LogArea()
        bottom_layout.addWidget(self.log_area, stretch=6) # 占60%宽
        
        # 右下：控制台
        self.control_area = ControlArea(self)
        bottom_layout.addWidget(self.control_area, stretch=4) # 占40%宽
        
        main_layout.addWidget(bottom_frame, stretch=3) # 下部分占30%

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.log_area.add_log(f"切换页面至 Index: {index}", "debug")

# -----------------------------------------------------------------------------
# 入口
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
