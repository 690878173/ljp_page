from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QStandardItemModel, QColor, QFont, QStandardItem
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionButton, QStyle, QPushButton, QTableView, QHeaderView


class tableview(QTableView):
    # 参考不使用
    def __init__(self, parent):
        super().__init__(parent)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # 列宽自适应
        self.setMouseTracking(True)  # 启用鼠标跟踪
        # self.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)  # 垂直滚动条按像素滚动,更丝滑(影响性能)
        # self.setItemDelegateForColumn(3, tableview_Delegate(self.main_window, self))  # 若委托后全部是下载按钮，则是忘记设置委托了


class table_model(QStandardItemModel):
    # 使用
    def __init__(self, header: list, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setHorizontalHeaderLabels(header)

    def _____a(self, data: list):
        # 向模型中添加数据
        for row in data:
            items = [QStandardItem(str(item)) for item in row]
            self.appendRow(items)


# 自定义委托：在表格单元格中嵌入下载按钮(出于性能考虑看起来像按钮)
class tableview_Delegate(QStyledItemDelegate):
    def __init__(self, main_window, parent, column_index=4): # parent 是 tableview
        super().__init__(parent)
        self.main_window = main_window  # 保存主窗口引用，用于调用下载方法
        self.column_index = column_index  # 操作列索引 ->可在逻辑修改不止一个
        self.parent = parent

    # 编辑单元格样式
    def paint(self, painter, option, index):
        # painter：QPainter 对象，用于执行绘制操作（如画矩形、文字、颜色等）
        # option：QStyleOptionViewItem 对象，包含单元格的样式信息（如位置、大小、状态（是否选中/悬停）等）
        # index：QModelIndex 对象，当前单元格的索引（用于获取数据或判断列/行）

        rect = option.rect  # 单元格的位置和大小
        # 2. 判断单元格状态（如鼠标是否悬停，决定按钮颜色）
        if option.state & QStyle.StateFlag.State_MouseOver:
            # 鼠标悬停时，按钮背景色深一点
            bg_color = QColor(200, 100, 200)
        else:
            # 默认背景色
            bg_color = QColor(240, 240, 240)

        # 3. 绘制按钮外观
        painter.save()  # 保存当前绘制状态，避免影响其他绘制
        painter.setPen(QColor(100, 100, 100))  # 边框颜色
        painter.setBrush(bg_color)  # 背景色
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 4, 4)  # 绘制圆角矩形（按钮形状）

        # 4. 绘制按钮文字（居中显示“下载”）
        painter.setPen(QColor(0, 0, 0))  # 文字颜色
        painter.setFont(QFont("SimHei", 9))  # 字体
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "下载")  # 居中绘制文字

        painter.restore() # 恢复绘制状态

    def createEditor(self, parent, option, index):

        #只在操作列显示按钮
        if index.column() == self.column_index:
            editor = QPushButton("下载", parent)
            # 绑定按钮点击事件（触发自定义逻辑，如下载小说）
            # editor.clicked.connect(lambda: self.on_button_clicked(index,editor))
            return editor
        return super().createEditor(parent, option, index)

    # 处理鼠标点击事件
    def editorEvent(self, event, model, option, index):
        # event：当前触发的事件（如QMouseEvent、QKeyEvent等）
        # model：数据模型（QAbstractItemModel）
        # option：单元格的样式选项（QStyleOptionViewItem）
        # index：当前单元格的索引（QModelIndex）

        if index.column() != self.column_index:
            return super().editorEvent(event, model, option, index)
        # 处理鼠标事件，让按钮无需双击即可交互#
        if event.type() == QEvent.Type.MouseButtonRelease:
            # 显示按钮
            if self.parent:
                self.parent.edit(index)
                pass
            # 直接触发下载逻辑（无需第二次点击）
            self.on_button_clicked(index)
        elif event.type() == QEvent.Type.MouseMove:
            # 高亮按钮
            pass
        return True

    # 按钮点击事件：获取行索引，触发下载
    def on_button_clicked(self, index):
        if self.main_window:
            self.main_window.button_click(index)  # 调用主窗口的下载方法
            bg_color = QColor(100, 100, 200)


    # 以下方法确保按钮正常显示（固定写法）
    def setEditorData(self, editor, index):
        pass  # 无需设置数据，按钮固定显示“下载”

    def setModelData(self, editor, model, index):
        pass  # 无需修改模型数据

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)  # 按钮大小适应单元格