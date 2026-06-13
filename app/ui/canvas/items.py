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

    if shape_type in ["round"]:
        path.addEllipse(0, 0, w, h)

    elif shape_type == "24246":
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.lineTo(w, h/2)
        path.arcTo(0, 0, w, h, 0, 180)
        path.closeSubpath()

    elif shape_type in ["macaroni"]:
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

    elif shape_type in ["L", "14719"]:
        path.moveTo(0, 0)
        path.lineTo(w, 0)
        path.lineTo(w, grid)
        path.lineTo(grid, grid)
        path.lineTo(grid, h)
        path.lineTo(0, h)
        path.closeSubpath()

    elif shape_type in ["triangle", "35787"]:
        path.moveTo(0, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()

    elif shape_type == "1748":
        path.moveTo(w, h)
        path.arcTo(0, 0, w, w, 0, 180) 
        path.closeSubpath()

    elif shape_type == "5520":
        path.moveTo(0, h)
        path.lineTo(w, h)
        path.lineTo(w, h/2)
        path.arcTo(0, 0, w, h, 0, 180)
        path.closeSubpath()

    elif shape_type in ["39739", "heart"]:
        # We removed the 'margin' variable to let the heart fill the space
        
        # Start at the exact bottom center
        path.moveTo(w/2, h)

        # Left side: 
        # We move the control points to the extreme edges (0 and h)
        # to force the curve to touch the left and top grid lines.
        path.cubicTo(-w * 0.1, h * 0.8,   # Pulls curve to the left wall
                     w * 0.1, -h * 0.1,   # Pulls curve to the top wall
                     w/2, h * 0.22)       # Center Cleft (dip)

        # Right side:
        # Symmetrical extreme points for the right side
        path.cubicTo(w * 0.9, -h * 0.1, 
                     w * 1.1, h * 0.8, 
                     w/2, h)
        
        path.closeSubpath()

    elif shape_type == "5092":
        path.moveTo(0, 0)
        path.lineTo(w/2, 0)
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()

    else:
        path.addRect(0, 0, w, h)
        
    return path

class LegoPiece(QGraphicsPathItem):
    def __init__(self, x, y, w_units, h_units, color, shape_type="rect"):
        super().__init__()
        self.w_units = w_units
        self.h_units = h_units
        self.color = color
        self.original_color = color
        self.shape_type = shape_type
        self.current_angle = 0 
        

        self.refresh_shape()
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)


    def boundingRect(self):
        """Forces the selection box (dotted line) to be exactly the grid footprint."""
        if self.current_angle % 180 != 0:
            return QRectF(0, 0, self.h_units * config.GRID_SIZE, self.w_units * config.GRID_SIZE)
        return QRectF(0, 0, self.w_units * config.GRID_SIZE, self.h_units * config.GRID_SIZE)

    def refresh_shape(self):
        """Redraws the path and centers it within the bounding box."""
        path = get_lego_path(self.w_units, self.h_units, self.shape_type)
        
        tr = QTransform()
        tr.rotate(self.current_angle)
        path = tr.map(path)

        # Get the rect of the footprint we established in boundingRect
        target_rect = self.boundingRect()

        # Center the visual path inside the footprint
        path_rect = path.boundingRect()
        path.translate(-path_rect.topLeft()) # Move path to 0,0
        
        pad_x = (target_rect.width() - path_rect.width()) / 2
        pad_y = (target_rect.height() - path_rect.height()) / 2
        path.translate(pad_x, pad_y)

        self.setPath(path)

    def rotate_90(self):
        """Update internal angle and refresh the visual geometry."""
        self.current_angle = (self.current_angle + 90) % 360
        self.prepareGeometryChange() # Important: lets Qt know the bounding box moved
        self.refresh_shape()

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
    
    def set_color_override(self, override_color=None):
        """If an override color is provided, use it. Otherwise, revert to the original color."""
        target_color = override_color if override_color else self.original_color
        self.setBrush(QBrush(QColor(target_color)))