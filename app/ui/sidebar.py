# app/ui/sidebar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag, QPixmap, QColor, QPainter, QPen, QBrush
from app import config
from app.ui.canvas.items import get_lego_path

def create_piece_pixmap(w_u, h_u, color, shape_type):
    w, h = w_u * config.GRID_SIZE, h_u * config.GRID_SIZE
    pixmap = QPixmap(w, h); pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.setOpacity(0.6) 
    path = get_lego_path(w_u, h_u, shape_type)
    painter.setBrush(QBrush(QColor(color))); painter.setPen(QPen(Qt.GlobalColor.black, 1)); painter.drawPath(path); painter.end()
    return pixmap

class ShapePreviewPopup(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #333; border: 1px solid #555; padding: 5px;")
        self.setFixedSize(80, 80); self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_preview(self, w_u, h_u, color, shape_type):
        pixmap = QPixmap(70, 70); pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = get_lego_path(w_u, h_u, shape_type); rect = path.boundingRect()
        scale = min(60/max(rect.width(), 1), 60/max(rect.height(), 1))
        painter.translate(35, 35); painter.scale(scale, scale); painter.translate(-rect.center().x(), -rect.center().y())
        painter.setBrush(QBrush(QColor(color))); painter.setPen(QPen(Qt.GlobalColor.black, 1)); painter.drawPath(path); painter.end()
        self.setPixmap(pixmap)

class LibraryItemRow(QFrame):
    def __init__(self, width_units, height_units, color, name, shape_type, preview_popup):
        super().__init__()
        self.w_units, self.h_units, self.color, self.shape_type, self.preview_popup = width_units, height_units, color, shape_type, preview_popup
        self.setStyleSheet("background-color: transparent; border-radius: 4px; color: white;")
        layout = QHBoxLayout(self); layout.setContentsMargins(5, 5, 5, 5)
        self.icon_frame = QFrame(); self.icon_frame.setFixedSize(15, 15); self.icon_frame.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        self.label = QLabel(name); self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.icon_frame); layout.addWidget(self.label); layout.addStretch()

    def enterEvent(self, event):
        self.setStyleSheet("background-color: #3d3d3d; border-radius: 4px; color: white;")
        self.preview_popup.update_preview(self.w_units, self.h_units, self.color, self.shape_type)
        self.preview_popup.move(self.mapToGlobal(QPoint(self.width() + 5, -20))); self.preview_popup.show()

    def leaveEvent(self, event):
        self.setStyleSheet("background-color: transparent; color: white;"); self.preview_popup.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mime = QMimeData(); mime.setText(f"{self.w_units},{self.h_units},{self.color},{self.shape_type}")
            drag = QDrag(self); drag.setMimeData(mime); drag.setPixmap(create_piece_pixmap(self.w_units, self.h_units, self.color, self.shape_type))
            drag.setHotSpot(QPoint(0, 0)); drag.exec(Qt.DropAction.CopyAction)

class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(260); self.setStyleSheet("background-color: #252525; border-right: 1px solid #444;")
        self.main_layout = QVBoxLayout(self); self.preview_popup = ShapePreviewPopup()
        title = QLabel("PIECE LIBRARY"); title.setStyleSheet("font-weight: bold; color: #AAAAAA; margin-bottom: 5px;")
        self.main_layout.addWidget(title)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget(); container_layout = QVBoxLayout(container)
        for w, h, col, name, sid in config.LIBRARY_DATA:
            container_layout.addWidget(LibraryItemRow(w, h, col, name, sid, self.preview_popup))
        container_layout.addStretch(); scroll.setWidget(container); self.main_layout.addWidget(scroll)