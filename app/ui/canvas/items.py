# app/ui/canvas/items.py
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QTransform
from app import config

def get_lego_path(w_units, h_units, shape_type):
    path = QPainterPath()
    grid = config.GRID_SIZE
    w = w_units * grid
    h = h_units * grid

    # --- ROUND SHAPES (98138, 14769, 79393) ---
    if shape_type in ["round"]:
        path.addEllipse(0, 0, w, h)

    # --- HALF ROUND (24246) ---
    elif shape_type in ["24246"]:
        # 1x1 Tile with one rounded end
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.lineTo(w, h/2)
        # Semi-circle top: bounding box is the full 1x1 area
        path.arcTo(0, 0, w, h, 0, 180)
        path.closeSubpath()

    # --- MACARONI / QUARTER ROUND STRIPS  ---
    elif shape_type in ["macaroni"]:
        # These are strips 1-stud wide. 
        # For 27925 (2x2), Outer Radius = 2, Inner Radius = 1.
        # For 27507 (4x4), Outer Radius = 4, Inner Radius = 3.
        
        # We place the 'center' of the circle at the bottom-right corner (w, h)
        outer_r = w
        inner_r = w - grid # The strip is always 1 stud wide
        
        # Outer Arc (from left to top)
        path.arcMoveTo(0, 0, outer_r*2, outer_r*2, 180)
        path.arcTo(0, 0, outer_r*2, outer_r*2, 180, -90)
        
        # Line to inner arc
        path.lineTo(w, h - inner_r) 
        
        # Inner Arc (back to left)
        if inner_r > 0:
            path.arcTo(w - inner_r, h - inner_r, inner_r*2, inner_r*2, 90, 90)
        else:
            # For 1x1 Quarter Tile (25269), inner radius is 0, so it's a pie slice
            path.lineTo(w, h)
            
        path.closeSubpath()

    # --- CORNER L-SHAPE (14719) ---
    elif shape_type == "L":
        # A 2x2 L-shape tile
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, grid) # 1 stud down
        path.lineTo(grid, grid) # 1 stud left
        path.lineTo(grid, h) # all the way down
        path.lineTo(0, h)
        path.closeSubpath()

    # --- TRIANGLE (35787) ---
    elif shape_type == "triangle":
        # 2x2 Right Triangle
        path.moveTo(0, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()

          # --- 1x2 HALF CIRCLE (1748) ---
    elif shape_type == "1748":
        # Imagine a 2x2 circle cut in half. 
        # Footprint is 2 studs wide (w) by 1 stud deep (h).
        path.moveTo(0, h)
        path.lineTo(w, h)
        # We draw an arc using a 2x2 bounding box (0, 0, w, w)
        # Starting at 0 degrees (middle-right) to 180 degrees (middle-left)
        path.arcTo(0, 0, w, w, 0, 180) 
        path.closeSubpath()

    # --- 2x2 HALF ROUND (5520) ---
    elif shape_type == "5520":
        # Square 2x2 base with one side rounded (like 24246)
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.lineTo(w, h/2)
        # Semi-circle on the top half
        path.arcTo(0, 0, w, h, 0, 180)
        path.closeSubpath()

    # --- 1x1 HEART (39739) ---
    elif shape_type == "39739":
        # Stylized heart shape within 1x1
        # Drawing two arcs and a V-shape bottom
        path.moveTo(w/2, h) # Bottom tip
        path.lineTo(0, h/2) # Left side
        path.arcTo(0, 0, w/2, h/2, 180, -180) # Left lobe
        path.arcTo(w/2, 0, w/2, h/2, 180, -180) # Right lobe
        path.lineTo(w/2, h) # Back to bottom
        path.closeSubpath()

    # --- 1x2 WEDGE / SLOPE (5092) ---
    elif shape_type == "5092":
        # 1x1 Square + 1x1 Triangle
        path.moveTo(0, 0)
        path.lineTo(w/2, 0) # Top edge of square
        path.lineTo(w, h)   # Diagonal down to bottom right
        path.lineTo(0, h)   # Bottom edge
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
        # Use the shared function
        path = get_lego_path(self.w_units, self.h_units, self.shape_type)
        tr = QTransform()
        tr.rotate(self.current_angle)
        path = tr.map(path)
        offset = path.boundingRect().topLeft()
        path.translate(-offset)
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