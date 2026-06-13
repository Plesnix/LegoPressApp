# app/ui/canvas/scene.py
import copy
from PySide6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsRectItem, 
                             QGraphicsLineItem, QGraphicsItemGroup, QGraphicsItem)
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QCursor, QFont
from app import config
from app.ui.canvas.items import LegoPiece

class LegoScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.setSceneRect(-1000, -1000, 3000, 3000)
        self.plate = QGraphicsRectItem(0, 0, config.BASEPLATE_SIZE, config.BASEPLATE_SIZE)
        self.plate.setBrush(QBrush(QColor(config.PLATE_COLOR)))
        self.plate.setPen(QPen(Qt.GlobalColor.black, 2))
        self.plate.setZValue(-100)
        self.addItem(self.plate)
        line_pen = QPen(QColor(config.GRID_LINE_COLOR), 1)
        line_pen.setCosmetic(True)
        for x in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(x, 0, x, config.BASEPLATE_SIZE)
            line.setPen(line_pen); line.setZValue(-99); self.addItem(line)
        for y in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(0, y, config.BASEPLATE_SIZE, y)
            line.setPen(line_pen); line.setZValue(-99); self.addItem(line)

class LegoView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(config.VOID_COLOR)))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.clipboard = []; self.ghost_group = None; self._last_pan_pos = QPoint()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key.Key_C: self.copy_selection()
            elif event.key() == Qt.Key.Key_V: self.start_paste_mode()
        if event.key() == Qt.Key.Key_T: self.rotate_selection_90()
        if event.key() == Qt.Key.Key_R:
            for item in self.scene().selectedItems():
                if hasattr(item, 'rotate_90'): item.rotate_90()
        elif event.key() in [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
            for item in self.scene().selectedItems():
                if isinstance(item, LegoPiece): self.scene().removeItem(item)
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel_paste_mode()
        super().keyPressEvent(event)

    def rotate_selection_90(self):
        selected_items = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not selected_items: return
        grid = config.GRID_SIZE
        min_gx, min_gy, max_gx, max_gy = float('inf'), float('inf'), float('-inf'), float('-inf')
        item_data = []
        for item in selected_items:
            gx, gy = item.pos().x()/grid, item.pos().y()/grid
            rect = item.boundingRect()
            min_gx, min_gy = min(min_gx, gx), min(min_gy, gy)
            max_gx, max_gy = max(max_gx, gx + rect.width()/grid), max(max_gy, gy + rect.height()/grid)
            item_data.append({'item': item, 'gx': gx, 'gy': gy, 'gw': rect.width()/grid, 'gh': rect.height()/grid})
        pgx, pgy = (min_gx + max_gx) / 2.0, (min_gy + max_gy) / 2.0
        for data in item_data:
            item = data['item']; cgx, cgy = data['gx'] + data['gw']/2.0, data['gy'] + data['gh']/2.0
            new_cgx, new_cgy = pgx - (cgy - pgy), pgy + (cgx - pgx)
            item.rotate_90(); nr = item.boundingRect()
            new_gx, new_gy = new_cgx - (nr.width()/grid)/2.0, new_cgy - (nr.height()/grid)/2.0
            item.setPos(QPointF(round(new_gx)*grid, round(new_gy)*grid))

    def copy_selection(self):
        selected = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not selected: return
        self.clipboard = []
        min_x = min(item.pos().x() for item in selected); min_y = min(item.pos().y() for item in selected)
        for item in selected:
            self.clipboard.append({
                'w': item.w_units, 'h': item.h_units, 'color': item.brush().color().name(),
                'shape': item.shape_type, 'angle': item.current_angle,
                'rel_x': item.pos().x() - min_x, 'rel_y': item.pos().y() - min_y
            })

    def start_paste_mode(self):
        if not self.clipboard: return
        self.cancel_paste_mode(); self.ghost_group = QGraphicsItemGroup(); self.scene().addItem(self.ghost_group)
        for data in self.clipboard:
            ghost = LegoPiece(data['rel_x'], data['rel_y'], data['w'], data['h'], data['color'], data['shape'])
            ghost.current_angle = data['angle']; ghost.refresh_shape(); ghost.setOpacity(0.5) 
            ghost.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False); ghost.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            self.ghost_group.addToGroup(ghost)
        self.update_ghost_pos(self.mapFromGlobal(QCursor.pos()))

    def cancel_paste_mode(self):
        if self.ghost_group: self.scene().removeItem(self.ghost_group); self.ghost_group = None

    def update_ghost_pos(self, mouse_pos):
        if not self.ghost_group: return
        view_pos = self.viewport().mapFromGlobal(QCursor.pos())
        scene_pos = self.mapToScene(view_pos)
        self.ghost_group.setPos(round(scene_pos.x()/config.GRID_SIZE)*config.GRID_SIZE, round(scene_pos.y()/config.GRID_SIZE)*config.GRID_SIZE)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            if self.ghost_group: self.cancel_paste_mode()
            else: self._last_pan_pos = event.pos(); self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton and self.ghost_group:
            self.scene().clearSelection(); bx, by = self.ghost_group.pos().x(), self.ghost_group.pos().y()
            for data in self.clipboard:
                np = LegoPiece(bx + data['rel_x'], by + data['rel_y'], data['w'], data['h'], data['color'], data['shape'])
                np.current_angle = data['angle']; np.refresh_shape(); self.scene().addItem(np); np.setSelected(True)
            self.cancel_paste_mode()
        else: super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.ghost_group: self.update_ghost_pos(event.pos())
        if event.buttons() & Qt.MouseButton.RightButton:
            delta = event.pos() - self._last_pan_pos; self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else: super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton: self.unsetCursor()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        f = 1.15 if event.angleDelta().y() > 0 else 0.85; self.scale(f, f)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
    def dragMoveEvent(self, event): event.acceptProposedAction()
    def dropEvent(self, event):
        try:
            parts = event.mimeData().text().split(",")
            w, h, col, shp = int(parts[0]), int(parts[1]), parts[2], parts[3] if len(parts)>3 else "rect"
            raw = self.mapToScene(event.pos())
            self.scene().addItem(LegoPiece(round(raw.x()/config.GRID_SIZE)*config.GRID_SIZE, round(raw.y()/config.GRID_SIZE)*config.GRID_SIZE, w, h, col, shp))
            event.acceptProposedAction()
        except: event.ignore()

class LegoPrintView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#000000")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scale(1, 1) 
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag) 
        self._last_pan_pos = QPoint(); self.mouse_scene_pos = QPointF(0, 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._last_pan_pos = event.pos(); self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            # FIX: Ensure clicking a brick doesn't kill the selection drag
            item = self.itemAt(event.pos())
            if item and isinstance(item, LegoPiece) and not (event.modifiers() & Qt.ControlModifier):
                self.scene().clearSelection(); item.setSelected(True)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.mouse_scene_pos = self.mapToScene(event.pos())
        if event.buttons() & Qt.MouseButton.RightButton:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            # FIX: Horizontal panning inverted (- delta.x instead of +) to match Hand drag logic in mirrored mode
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super().mouseMoveEvent(event)
        self.viewport().update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton: self.unsetCursor()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        f = 1.15 if event.angleDelta().y() > 0 else 0.85; self.scale(f, f)

    def drawForeground(self, painter, rect):
        mx, my = self.mouse_scene_pos.x(), self.mouse_scene_pos.y()
        s, grid = config.BASEPLATE_SIZE, config.GRID_SIZE
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(0, 0, 0))
        painter.drawRect(-2000, -2000, 5000, 2000); painter.drawRect(-2000, s, 5000, 2000); painter.drawRect(-2000, 0, 2000, s); painter.drawRect(s, 0, 2000, s)            
        if 0 <= mx <= s and 0 <= my <= s:
            painter.setPen(QPen(QColor(0,0,0,200), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(0, my), QPointF(s, my)); painter.drawLine(QPointF(mx, 0), QPointF(mx, s))
            items = [i for i in self.scene().items() if isinstance(i, LegoPiece) and i.isVisible()]
            dl, dr, du, dd = mx, s - mx, my, s - my
            for i in items:
                ir = i.sceneBoundingRect()
                if ir.top() <= my <= ir.bottom():
                    if ir.right() <= mx: dl = min(dl, mx - ir.right())
                    elif ir.left() >= mx: dr = min(dr, ir.left() - mx)
                if ir.left() <= mx <= ir.right():
                    if ir.bottom() <= my: du = min(du, my - ir.bottom())
                    elif ir.top() >= my: dd = min(dd, ir.top() - my)
            painter.save(); painter.scale(-1, 1); painter.setPen(QColor(0,0,0)); painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            def d_t(v, x, y):
                std = int(round(v/grid))
                if std > 0: painter.drawText(int(-x), int(y), f"{std}")
            d_t(dl, mx-dl/2, my-5); d_t(dr, mx+dr/2, my-5); d_t(du, mx+5, my-du/2); d_t(dd, mx+5, my+dd/2)
            painter.restore()