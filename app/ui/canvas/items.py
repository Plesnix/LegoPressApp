# app/ui/canvas/items.py
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QTransform
from app import config

def get_lego_path(w_units, h_units, shape_type):
    """Universal function to get the geometry of any Lego piece"""
    path = QPainterPath()
    grid = config.GRID_SIZE
    w = w_units * grid
    h = h_units * grid

    # --- ROUND SHAPES (98138, 14769, 79393) ---
    if shape_type in ["round", "98138", "14769", "79393"]:
        path.addEllipse(0, 0, w, h)

    # --- HALF ROUND (24246) ---
    elif shape_type == "24246":
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.lineTo(w, h/2)
        path.arcTo(0, 0, w, h, 0, 180)
        path.closeSubpath()

    # --- MACARONI / QUARTER ROUND STRIPS (Generic) ---
    elif shape_type in ["macaroni", "25269", "27925", "27507"]:
        outer_r = w
        inner_r = w - grid 
        path.arcMoveTo(0, 0, outer_r*2, outer_r*2, 180)
        path.arcTo(0, 0, outer_r*2, outer_r*2, 180, -90)
        path.lineTo(w, h - inner_r) 
        if inner_r > 0:
            path.arcTo(w - inner_r, h - inner_r, inner_r*2, inner_r*2, 90, 90)
        else:
            path.lineTo(w, h)
        path.closeSubpath()

    # --- CORNER L-SHAPE (14719) ---
    elif shape_type in ["L", "14719"]:
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, grid)
        path.lineTo(grid, grid)
        path.lineTo(grid, h)
        path.lineTo(0, h)
        path.closeSubpath()

    # --- TRIANGLE (35787) ---
    elif shape_type in ["triangle", "35787"]:
        path.moveTo(0, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()

    # --- 1x2 HALF CIRCLE (1748) ---
    elif shape_type == "1748":
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.arcTo(0, -h, w, h*2, 0, 180) 
        path.closeSubpath()

    # --- 2x2 HALF ROUND (5520) ---
    elif shape_type == "5520":
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.lineTo(w, h/2)
        path.arcTo(0, 0, w, h, 0, 180)
        path.closeSubpath()

     # --- 1x1 HEART (39739) ---
    elif shape_type == "39739":
        # Reduced margin from 10% to 2% to make it fill the cell
        margin = grid * 0.02
        sw = w - (margin * 2)
        sh = h - (margin * 2)

        # Start at the sharp bottom tip
        path.moveTo(sw/2, sh * 0.98) 
        
        # Left Side:
        # We pushed the control points further out (-sw * 0.35) 
        # to create a much fuller "bulge"
        path.cubicTo(-sw * 0.35, sh * 0.4, 
                     sw * 0.25, -sh * 0.3, 
                     sw/2, sh * 0.25)
        
        # Right Side:
        path.cubicTo(sw * 0.75, -sh * 0.3, 
                     sw * 1.35, sh * 0.4, 
                     sw/2, sh * 0.98)
        path.closeSubpath()

    # --- 1x2 WEDGE / SLOPE (5092) ---
    elif shape_type == "5092":
        path.moveTo(0, 0)
        path.lineTo(w/2, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()

    # --- DEFAULT RECTANGLE ---
    else:
        path.addRect(0, 0, w, h)
        
    return path

class LegoPiece(QGraphicsPathItem):
    def __init__(self, x, y, w_units, h_units, color, shape_type="rect"):
        super().__init__()
        self.w_units = w_units
        self.h_units = h_units
        self.color = color
        self.shape_type = shape_type
        self.current_angle = 0 

        self.refresh_shape()
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def refresh_shape(self):
        """Redraws the path, rotates it, and centers it in the grid cell."""
        path = get_lego_path(self.w_units, self.h_units, self.shape_type)
        
        tr = QTransform()
        tr.rotate(self.current_angle)
        path = tr.map(path)

        # Determine target footprint
        if self.current_angle % 180 != 0:
            target_w, target_h = self.h_units * config.GRID_SIZE, self.w_units * config.GRID_SIZE
        else:
            target_w, target_h = self.w_units * config.GRID_SIZE, self.h_units * config.GRID_SIZE

        # Center logic
        rect = path.boundingRect()
        path.translate(-rect.topLeft()) # Reset to 0,0
        
        pad_x = (target_w - rect.width()) / 2
        pad_y = (target_h - rect.height()) / 2
        path.translate(pad_x, pad_y)

        self.setPath(path)

    def rotate_90(self):
        self.current_angle = (self.current_angle + 90) % 360
        self.refresh_shape()
        self.setPos(self.pos()) 

    def mouseDoubleClickEvent(self, event):
        self.rotate_90()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value 
            x = round(new_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
            y = round(new_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
            return QPointF(x, y)
        return super().itemChange(change, value)