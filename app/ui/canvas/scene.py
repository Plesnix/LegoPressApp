# app/ui/canvas/scene.py
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QCursor
from app import config

class LegoScene(QGraphicsScene):
    def __init__(self):
        super().__init__(0, 0, config.BASEPLATE_SIZE, config.BASEPLATE_SIZE)
        self.setBackgroundBrush(QBrush(QColor(config.BG_COLOR)))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        pen = QPen(QColor(config.GRID_LINE_COLOR), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        
        for x in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            painter.addLine(x, 0, x, config.BASEPLATE_SIZE)
        for y in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            painter.addLine(0, y, config.BASEPLATE_SIZE, y)

class LegoView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Left click defaults to RubberBand (Box selection + Item moving)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Store mouse position for panning
        self._last_pan_pos = QPoint()

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # Start Panning: Change cursor and record position
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept() # Tell the app we handled this click
        else:
            # Let standard logic handle Left Click (Select/Move)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.RightButton:
            # Calculate how far we moved since the last frame
            delta = self._last_pan_pos - event.pos()
            self._last_pan_pos = event.pos()
            
            # Manually move the scrollbars to pan the view
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            # Stop Panning: Reset cursor
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)