# app/ui/canvas/items.py
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath
from app import config

class LegoPiece(QGraphicsPathItem):
    def __init__(self, x, y, w_units, h_units, color, shape_type="rect"):
        super().__init__()
        self.w_units = w_units
        self.h_units = h_units
        self.shape_type = shape_type
        
        self.setPath(self._create_path())
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(Qt.GlobalColor.black, 1))
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def _create_path(self):
        path = QPainterPath()
        w = self.w_units * config.GRID_SIZE
        h = self.h_units * config.GRID_SIZE

        if self.shape_type == "27925":  # 2x2 Macaroni Tile
            # Draw outer arc from bottom-right (270°) to top-left (180°)
            path.moveTo(w, h)
            path.arcTo(0, 0, w*2, h*2, 90, 90) # Outer curve
            path.lineTo(w, h) # Back to center-point
            path.closeSubpath()

        elif self.shape_type == "24246":  # 1x1 Half Round
            path.moveTo(0, h)
            path.lineTo(w, h)
            path.lineTo(w, h/2)
            # Semi circle from 0 degrees to 180 degrees
            path.arcTo(0, 0, w, h, 0, 180) 
            path.closeSubpath()

        elif self.shape_type == "round": # 1x1 Round Stud
            # Draw a circle that fits perfectly in the grid square
            path.addEllipse(0, 0, w, h)    

        else: # Default Rectangle
            path.addRect(0, 0, w, h)
            
        return path

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value 
            x = round(new_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
            y = round(new_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
            return QPointF(x, y)
        return super().itemChange(change, value)