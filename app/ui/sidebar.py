# app/ui/sidebar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QPixmap

class DraggableBrick(QFrame):
    def __init__(self, width_units, height_units, color, shape_type="rect"):
        super().__init__()
        self.w_units = width_units
        self.h_units = height_units
        self.color = color
        self.shape_type = shape_type
        
        self.setFixedSize(30, 30)
        self.setStyleSheet(f"background-color: {color}; border: 1px solid white; border-radius: 4px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mime_data = QMimeData()
            # PACKING: width,height,color,shape
            item_data = f"{self.w_units},{self.h_units},{self.color},{self.shape_type}"
            mime_data.setText(item_data)
            
            # DEBUG PRINT:
            print(f"DEBUG: Dragging started with data: {item_data}")

            drag = QDrag(self)
            drag.setMimeData(mime_data)
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)

class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #252525; border-right: 1px solid #444; color: white;")
        self.main_layout = QVBoxLayout(self)
        
        title = QLabel("CONTROLS & LIBRARY")
        title.setStyleSheet("font-weight: bold; margin-bottom: 10px; color: #AAAAAA;")
        self.main_layout.addWidget(title)
        
        # LIBRARY - Make sure these have the shape ID at the end!
        self.add_library_item(1, 1, "#e63946", "1x1 Stud (Red)", "rect")
        self.add_library_item(2, 4, "#2196F3", "2x4 Brick (Blue)", "rect")
        self.add_library_item(1, 1, "#A0A0A0", "1x1 Half-Round (24246)", "24246")
        self.add_library_item(2, 2, "#008080", "2x2 Macaroni (27925)", "27925")
        
        self.main_layout.addStretch()

    def add_library_item(self, w, h, color, name, shape_type="rect"):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(5, 2, 5, 2)
        
        icon = DraggableBrick(w, h, color, shape_type)
        label = QLabel(name)
        
        row_layout.addWidget(icon)
        row_layout.addWidget(label)
        row_layout.addStretch()
        self.main_layout.addWidget(row_widget)