# app/ui/sidebar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor

class DraggableBrick(QFrame):
    """A small visual icon in the sidebar that can be dragged."""
    def __init__(self, width_units, height_units, color):
        super().__init__()
        self.w_units = width_units
        self.h_units = height_units
        self.color = color
        
        # Appearance of the icon in the sidebar
        self.setFixedSize(40, 40)
        self.setStyleSheet(f"background-color: {color}; border: 1px solid white; border-radius: 4px;")
        self.setToolTip(f"Lego {width_units}x{height_units}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 1. Prepare the data (MIME) to be sent
            mime_data = QMimeData()
            # We store the data as a simple string "width,height,color"
            item_data = f"{self.w_units},{self.h_units},{self.color}"
            mime_data.setText(item_data)

            # 2. Create the drag object
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # 3. Create a preview image that follows the mouse
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

            # 4. Start the drag
            drag.exec(Qt.DropAction.CopyAction)

class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #252525; border-right: 1px solid #444;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("CONTROLS & LIBRARY"))
        
        # Add a 1x1 Red Piece
        self.brick1x1 = DraggableBrick(1, 1, "red")
        layout.addWidget(self.brick1x1)
        
        # Add a 2x4 Blue Piece for variety
        self.brick2x4 = DraggableBrick(2, 4, "#2196F3")
        layout.addWidget(self.brick2x4)
        
        layout.addStretch()