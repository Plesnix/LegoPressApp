# app/ui/sidebar.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag, QPixmap, QColor, QPainter, QPen, QBrush
from app import config
from app.ui.canvas.items import get_lego_path

def create_piece_pixmap(w_u, h_u, color, shape_type):
    """Generates a 1:1 scale pixmap of the Lego piece for dragging."""
    # Calculate pixel size based on grid units
    w = w_u * config.GRID_SIZE
    h = h_u * config.GRID_SIZE
    
    # Create pixmap with a tiny bit of padding for the 1px border
    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Set opacity
    painter.setOpacity(0.6) 

    # Get the shape path
    path = get_lego_path(w_u, h_u, shape_type)
    
    # Draw it
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(QPen(Qt.GlobalColor.black, 1))
    painter.drawPath(path)
    painter.end()
    
    return pixmap

class ShapePreviewPopup(QLabel):
    """A small floating window that shows a render of the Lego piece."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #333; border: 1px solid #555; padding: 5px;")
        self.setFixedSize(80, 80)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_preview(self, w_u, h_u, color, shape_type):
        # 1. Create a blank image
        pixmap = QPixmap(70, 70)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        # 2. Setup Painter to draw the shape
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get the real path and scale it to fit the preview window
        path = get_lego_path(w_u, h_u, shape_type)
        
        # Center and scale the path for the preview box
        rect = path.boundingRect()
        scale = min(60/max(rect.width(), 1), 60/max(rect.height(), 1))
        painter.translate(35, 35) # Move to center of 70x70
        painter.scale(scale, scale)
        painter.translate(-rect.center().x(), -rect.center().y())

        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawPath(path)
        painter.end()
        
        self.setPixmap(pixmap)

class LibraryItemRow(QFrame):
    def __init__(self, width_units, height_units, color, name, shape_type, preview_popup):
        super().__init__()
        self.w_units = width_units
        self.h_units = height_units
        self.color = color
        self.shape_type = shape_type
        self.preview_popup = preview_popup

        self.setStyleSheet("background-color: transparent; border-radius: 4px; color: white;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.icon_frame = QFrame()
        self.icon_frame.setFixedSize(15, 15)
        self.icon_frame.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        
        self.label = QLabel(name)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(self.icon_frame)
        layout.addWidget(self.label)
        layout.addStretch()

    def enterEvent(self, event):
        """When mouse enters: Show preview"""
        self.setStyleSheet("background-color: #3d3d3d; border-radius: 4px; color: white;")
        self.preview_popup.update_preview(self.w_units, self.h_units, self.color, self.shape_type)
        
        # Position the popup to the right of the sidebar
        global_pos = self.mapToGlobal(QPoint(self.width() + 5, -20))
        self.preview_popup.move(global_pos)
        self.preview_popup.show()

    def leaveEvent(self, event):
        """When mouse leaves: Hide preview"""
        self.setStyleSheet("background-color: transparent; color: white;")
        self.preview_popup.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mime_data = QMimeData()
            item_data = f"{self.w_units},{self.h_units},{self.color},{self.shape_type}"
            mime_data.setText(item_data)

            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # --- NEW DRAG PREVIEW LOGIC ---
            # Create the actual Lego shape pixmap
            pixmap = create_piece_pixmap(self.w_units, self.h_units, self.color, self.shape_type)
            
            # Set the 'ghost' image
            drag.setPixmap(pixmap)
            
            # Set the 'Hotspot' to the center of the piece so it feels 
            # like you are holding it by the middle.
            drag.setHotSpot(QPoint(0, 0))
            
            drag.exec(Qt.DropAction.CopyAction)

class Sidebar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #252525; border-right: 1px solid #444;")
        self.main_layout = QVBoxLayout(self)
        
        # One shared popup for the whole sidebar
        self.preview_popup = ShapePreviewPopup()

        title = QLabel("CONTROLS & LIBRARY")
        title.setStyleSheet("font-weight: bold; margin-bottom: 10px; color: #AAAAAA;")
        self.main_layout.addWidget(title)
        
        self.add_library_item(1, 1, "#e63946", "1x1 Stud (Red)", "rect")
        self.add_library_item(2, 4, "#2196F3", "2x4 Brick (Blue)", "rect")
        self.add_library_item(1, 1, "#FFD700", "1x1 Round Stud", "round")
        self.add_library_item(1, 1, "#A0A0A0", "1x1 Half-Round", "24246")
        self.add_library_item(2, 2, "#008080", "2x2 Macaroni", "27925")
        
        self.main_layout.addStretch()

    def add_library_item(self, w, h, color, name, shape_type="rect"):
        # Pass the preview_popup to every row
        item_row = LibraryItemRow(w, h, color, name, shape_type, self.preview_popup)
        self.main_layout.addWidget(item_row)