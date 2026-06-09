# app/ui/canvas/items.py
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QTransform
from app import config

class LegoPiece(QGraphicsPathItem):
    def __init__(self, x, y, w_units, h_units, color, shape_type="rect"):
        super().__init__()
        self.w_units = w_units
        self.h_units = h_units
        self.color = color
        self.shape_type = shape_type
        self.current_angle = 0  # 0, 90, 180, 270

        # Initial drawing
        self.refresh_shape()
        self.setPos(x, y)
        
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.GlobalColor.black, 1))

        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def refresh_shape(self):
        """Redraws the path and ensures top-left is at (0,0)"""
        # 1. Create the basic shape path
        path = self._create_base_path()

        # 2. Rotate the path geometry around its local (0,0)
        tr = QTransform()
        tr.rotate(self.current_angle)
        path = tr.map(path)

        # 3. "Normalize" the path
        # After rotation, the top-left might be at (-40, 0). 
        # We shift it so the top-left of the bounding box is ALWAYS (0,0).
        offset = path.boundingRect().topLeft()
        path.translate(-offset)

        self.setPath(path)

    def _create_base_path(self):
        """Internal logic to draw the basic un-rotated shape"""
        path = QPainterPath()
        w = self.w_units * config.GRID_SIZE
        h = self.h_units * config.GRID_SIZE

        if self.shape_type == "27925": # Macaroni 2x2
            # Draw a quarter circle wedge
            path.moveTo(w, h)
            path.arcTo(0, 0, w*2, h*2, 90, 90)
            path.lineTo(w, h)
            path.closeSubpath()
        elif self.shape_type == "24246": # Half Round 1x1
            path.moveTo(0, h)
            path.lineTo(w, h)
            path.lineTo(w, h/2)
            path.arcTo(0, 0, w, h, 0, 180)
            path.closeSubpath()
        elif self.shape_type == "round": 
            path.addEllipse(0, 0, w, h)
        else: # Standard Rectangle
            path.addRect(0, 0, w, h)
        return path

    def rotate_90(self):
        """Update angle and redraw"""
        self.current_angle = (self.current_angle + 90) % 360
        self.refresh_shape()
        # Ensure it stays snapped after dimensions change
        self.setPos(self.pos()) 

    def mouseDoubleClickEvent(self, event):
        self.rotate_90()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value 
            x = round(new_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
            y = round(new_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
            
            # Boundary Clamping (Always uses updated bounding box)
            rect = self.path().boundingRect()
            x = max(0, min(x, config.BASEPLATE_SIZE - rect.width()))
            y = max(0, min(y, config.BASEPLATE_SIZE - rect.height()))
            
            return QPointF(x, y)
        return super().itemChange(change, value)