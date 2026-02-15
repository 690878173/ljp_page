from PyQt6.QtGui import QStandardItem
from ljp_page._ljp_ui.tableview.tableview import table_model, tableview_Delegate


class xs_table_model(table_model):
    def __init__(self, header: list, parent=None):
        super().__init__(header, parent)
        self.book_list = []

    def append_data(self, book_info):
        self.book_list.append(book_info)
        items = [
            QStandardItem(str(book_info.id)),
            QStandardItem(str(book_info.title)),
            QStandardItem(str(book_info.total_chapters)),
            QStandardItem('未下载'),
            QStandardItem(''),
        ]
        self.appendRow(items)

class xs_tableview_Delegate(tableview_Delegate):
    def __init__(self, main_window, parent, column_index=4):
        super().__init__(main_window, parent, column_index)
