# app/ui/canvas/items.py
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor
from app import config

class LegoPiece(QGraphicsRectItem):
    def __init__(self, x, y, width_units, height_units, color):
        w = width_units * config.GRID_SIZE
        h = height_units * config.GRID_SIZE
        super().__init__(0, 0, w, h)
        
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        
        pen = QPen(Qt.GlobalColor.black, 1)
        pen.setCosmetic(True) 
        self.setPen(pen)
        
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | 
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value 
            
            # Snap to grid
            x = round(new_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
            y = round(new_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
            
            # Boundary Clamping (using the actual piece dimensions)
            rect = self.rect()
            x = max(0, min(x, config.BASEPLATE_SIZE - rect.width()))
            y = max(0, min(y, config.BASEPLATE_SIZE - rect.height()))
            
            return QPointF(x, y)
        return super().itemChange(change, value)