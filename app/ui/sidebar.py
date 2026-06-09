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
        self.setFixedWidth(260)
        self.setStyleSheet("background-color: #252525; border-right: 1px solid #444;")
        self.main_layout = QVBoxLayout(self)
        self.preview_popup = ShapePreviewPopup()

        title = QLabel("PIECE LIBRARY")
        title.setStyleSheet("font-weight: bold; color: #AAAAAA; margin-bottom: 5px;")
        self.main_layout.addWidget(title)

        # YOUR PHYSICAL INVENTORY
        # Format: (Width, Height, Color, Display Name, ID/Shape)
        LIBRARY_DATA = [
            # RECTANGULAR TILES
            (1, 1, "#A0A0A0", "1x1 Tile (3070b)", "Rectangle"),
            (1, 2, "#A0A0A0", "1x2 Tile (3069b)", "Rectangle"),
            (1, 3, "#A0A0A0", "1x3 Tile (63864)", "Rectangle"),
            (1, 4, "#A0A0A0", "1x4 Tile (2431)", "Rectangle"),
            (1, 6, "#A0A0A0", "1x6 Tile (6636)", "Rectangle"),
            (2, 2, "#A0A0A0", "2x2 Tile (3068b)", "Rectangle"),
            (2, 1, "#A0A0A0", "1x2 Wedge Tile (5092)", "5092"),

            # ROUND TILES
            (1, 1, "#FFD700", "1x1 Circle (98138)", "round"),
            (2, 2, "#FFD700", "2x2 Circle (14769)", "round"),
            (3, 3, "#FFD700", "3x3 Circle (79393)", "round"),
            (4, 4, "#FFD700", "4x4 Circle (GDS-21071)", "round"),
            (2, 1, "#FFD700", "1x2 Half Circle (1748)", "1748"),
            
            # CURVED / SPECIAL TILES
            (1, 1, "#4FB0C6", "1x1 Half Round (24246)", "24246"),
            (2, 2, "#4FB0C6", "2x2 Half Round (5520)", "5520"),
            (1, 1, "#4FB0C6", "1x1 Quarter (25269)", "macaroni"),
            (2, 2, "#4FB0C6", "2x2 Macaroni (27925)", "macaroni"),
            (3, 3, "#4FB0C6", "3x3 Macaroni (79393)", "macaroni"),
            (4, 4, "#4FB0C6", "4x4 Macaroni (27507)", "macaroni"),
            (2, 2, "#E63946", "2x2 Corner (14719)", "L"),
            (2, 2, "#E63946", "2x2 Triangle (35787)", "triangle"),

            # SPECIAL SHAPES
            (1, 1, "#EC34CE", "1x1 Heart (39739)", "heart"),
            
        ]

        # Create a scroll area in case the list gets long
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        for w, h, col, name, sid in LIBRARY_DATA:
            item = LibraryItemRow(w, h, col, name, sid, self.preview_popup)
            container_layout.addWidget(item)
            
        container_layout.addStretch()
        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)