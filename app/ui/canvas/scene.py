# app/ui/canvas/scene.py
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsLineItem
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from app import config
from app.ui.canvas.items import LegoPiece

class LegoScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        # Large workspace area
        self.setSceneRect(-1000, -1000, 3000, 3000)
        
        # 1. Create the Physical Baseplate
        self.plate = QGraphicsRectItem(0, 0, config.BASEPLATE_SIZE, config.BASEPLATE_SIZE)
        self.plate.setBrush(QBrush(QColor(config.PLATE_COLOR)))
        self.plate.setPen(QPen(Qt.GlobalColor.black, 2))
        self.plate.setZValue(-100)
        self.addItem(self.plate)

        # 2. Create the Grid Lines as actual items
        line_pen = QPen(QColor(config.GRID_LINE_COLOR), 1)
        line_pen.setCosmetic(True)
        
        for x in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(x, 0, x, config.BASEPLATE_SIZE)
            line.setPen(line_pen)
            line.setZValue(-99)
            self.addItem(line)
            
        for y in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(0, y, config.BASEPLATE_SIZE, y)
            line.setPen(line_pen)
            line.setZValue(-99)
            self.addItem(line)

class LegoView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(config.VOID_COLOR)))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Drag and Drop
        self.setAcceptDrops(True)
        
        # Interaction Modes
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self._last_pan_pos = QPoint()

    # --- DRAG AND DROP LOGIC (WITH SNAPPING) ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        data_string = event.mimeData().text()
        try:
            w_u, h_u, color = data_string.split(",")
            w_units, h_units = int(w_u), int(h_u)
            
            # Map mouse to scene
            raw_pos = self.mapToScene(event.pos())
            
            # Snap to grid
            snap_x = round(raw_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
            snap_y = round(raw_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
            
            # Clamp to boundaries
            snap_x = max(0, min(snap_x, config.BASEPLATE_SIZE - (w_units * config.GRID_SIZE)))
            snap_y = max(0, min(snap_y, config.BASEPLATE_SIZE - (h_units * config.GRID_SIZE)))
            
            new_piece = LegoPiece(snap_x, snap_y, w_units, h_units, color)
            self.scene().addItem(new_piece)
            
            event.acceptProposedAction()
        except Exception as e:
            print(f"Drop error: {e}")
            event.ignore()

    # --- NAVIGATION LOGIC (RIGHT-CLICK PAN & ZOOM) ---
    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.RightButton:
            delta = self._last_pan_pos - event.pos()
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)