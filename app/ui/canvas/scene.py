# app/ui/canvas/scene.py
from PySide6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsRectItem, 
                             QGraphicsLineItem, QGraphicsItemGroup, QGraphicsItem, QGraphicsPixmapItem)
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QCursor, QFont
from app import config
from app.ui.canvas.items import LegoPiece

class LegoScene(QGraphicsScene):
    def __init__(self, board_size=None, show_plate=True):
        super().__init__()
        self.s = board_size if board_size else config.BASEPLATE_SIZE
        self.setSceneRect(-2000, -2000, 5000, 5000)
        if show_plate:
            self.plate = QGraphicsRectItem(0, 0, self.s, self.s)
            self.plate.setBrush(QBrush(QColor(config.PLATE_COLOR)))
            self.plate.setPen(QPen(Qt.GlobalColor.black, 2))
            self.plate.setZValue(-100); self.addItem(self.plate)
        lp = QPen(QColor(config.GRID_LINE_COLOR), 1); lp.setCosmetic(True)
        for x in range(0, int(self.s) + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(x, 0, x, self.s); line.setPen(lp); line.setZValue(-99); self.addItem(line)
        for y in range(0, int(self.s) + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(0, y, self.s, y); line.setPen(lp); line.setZValue(-99); self.addItem(line)

class LegoView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing); self.setBackgroundBrush(QBrush(QColor(config.VOID_COLOR)))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setAcceptDrops(True); self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ghost_group = None; self._last_pan_pos = QPoint()

    def keyPressEvent(self, ev):
        if ev.modifiers() & Qt.ControlModifier:
            if ev.key() == Qt.Key.Key_C: self.copy_selection()
            elif ev.key() == Qt.Key.Key_V: self.start_paste_mode()
        if ev.key() == Qt.Key.Key_T: self.rotate_selection_90()
        if ev.key() == Qt.Key.Key_R:
            for i in self.scene().selectedItems():
                if hasattr(i, 'rotate_90'): i.rotate_90()
        elif ev.key() in [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
            for i in self.scene().selectedItems():
                if isinstance(i, LegoPiece): self.scene().removeItem(i)
        elif ev.key() == Qt.Key.Key_Escape:
            self.cancel_paste_mode()
        super().keyPressEvent(ev)

    def rotate_selection_90(self):
        sel = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not sel: return
        grid = config.GRID_SIZE; min_gx, min_gy, max_gx, max_gy = float('inf'), float('inf'), float('-inf'), float('-inf')
        item_data = []
        for i in sel:
            gx, gy = i.pos().x()/grid, i.pos().y()/grid; r = i.boundingRect()
            min_gx, min_gy = min(min_gx, gx), min(min_gy, gy); max_gx, max_gy = max(max_gx, gx+r.width()/grid), max(max_gy, gy+r.height()/grid)
            item_data.append({'item': i, 'gx': gx, 'gy': gy, 'gw': r.width()/grid, 'gh': r.height()/grid})
        pgx, pgy = (min_gx + max_gx) / 2.0, (min_gy + max_gy) / 2.0
        for d in item_data:
            item = d['item']; cgx, cgy = d['gx'] + d['gw']/2.0, d['gy'] + d['gh']/2.0
            new_cgx, new_cgy = pgx - (cgy - pgy), pgy + (cgx - pgx); item.rotate_90(); nr = item.boundingRect()
            new_gx, new_gy = new_cgx - (nr.width()/grid)/2.0, new_cgy - (nr.height()/grid)/2.0
            item.setPos(QPointF(round(new_gx)*grid, round(new_gy)*grid))

    def copy_selection(self):
        sel = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not sel: return
        self.window().shared_clipboard = []
        min_x = min(i.pos().x() for i in sel); min_y = min(i.pos().y() for i in sel)
        for i in sel:
            self.window().shared_clipboard.append({
                'w': i.w_units, 'h': i.h_units, 'color': i.brush().color().name(),
                'shape': i.shape_type, 'angle': i.current_angle,
                'rel_x': i.pos().x() - min_x, 'rel_y': i.pos().y() - min_y
            })

    def start_paste_mode(self):
        clip = getattr(self.window(), 'shared_clipboard', [])
        if not clip: return
        self.cancel_paste_mode(); self.ghost_group = QGraphicsItemGroup(); self.scene().addItem(self.ghost_group)
        for d in clip:
            c = self.window().get_adapted_color(d['w'], d['h'], d['shape'], d['color'])
            g = LegoPiece(d['rel_x'], d['rel_y'], d['w'], d['h'], c, d['shape']); g.current_angle = d['angle']; g.refresh_shape(); g.setOpacity(0.5) 
            g.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False); g.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False); self.ghost_group.addToGroup(g)
        self.update_ghost_pos()

    def cancel_paste_mode(self):
        if self.ghost_group: self.scene().removeItem(self.ghost_group); self.ghost_group = None

    def update_ghost_pos(self):
        if not self.ghost_group: return
        view_pos = self.viewport().mapFromGlobal(QCursor.pos()); s_pos = self.mapToScene(view_pos)
        self.ghost_group.setPos(round(s_pos.x()/config.GRID_SIZE)*config.GRID_SIZE, round(s_pos.y()/config.GRID_SIZE)*config.GRID_SIZE)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton:
            if self.ghost_group: self.cancel_paste_mode()
            else: self._last_pan_pos = ev.pos(); self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif ev.button() == Qt.MouseButton.LeftButton and self.ghost_group:
            self.scene().clearSelection(); bx, by = self.ghost_group.pos().x(), self.ghost_group.pos().y()
            for d in getattr(self.window(), 'shared_clipboard', []):
                c = self.window().get_adapted_color(d['w'], d['h'], d['shape'], d['color'])
                np = LegoPiece(bx+d['rel_x'], by+d['rel_y'], d['w'], d['h'], c, d['shape']); np.current_angle=d['angle']; np.refresh_shape(); self.scene().addItem(np); np.setSelected(True)
            self.cancel_paste_mode()
        else: super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self.ghost_group: self.update_ghost_pos()
        if ev.buttons() & Qt.MouseButton.RightButton:
            delta = ev.pos() - self._last_pan_pos; self._last_pan_pos = ev.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x()); self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else: super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton: self.unsetCursor()
        super().mouseReleaseEvent(ev)

    def wheelEvent(self, ev):
        f = 1.15 if ev.angleDelta().y() > 0 else 0.85; self.scale(f, f)

    def dragEnterEvent(self, ev):
        if ev.mimeData().hasText(): ev.acceptProposedAction()
    def dragMoveEvent(self, ev): ev.acceptProposedAction()
    def dropEvent(self, ev):
        try:
            p = ev.mimeData().text().split(","); w, h, col, shp = int(p[0]), int(p[1]), p[2], p[3] if len(p)>3 else "rect"
            raw = self.mapToScene(ev.pos())
            self.scene().addItem(LegoPiece(round(raw.x()/config.GRID_SIZE)*config.GRID_SIZE, round(raw.y()/config.GRID_SIZE)*config.GRID_SIZE, w, h, col, shp))
            ev.acceptProposedAction()
        except: ev.ignore()

class LegoPrintView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene); self.setRenderHint(QPainter.RenderHint.Antialiasing); self.setBackgroundBrush(QBrush(QColor("#000000")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.scale(-1, 1); self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True); self.setDragMode(QGraphicsView.DragMode.RubberBandDrag) 
        self._last_pan_pos = QPoint(); self.mouse_scene_pos = QPointF(0, 0)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton: self._last_pan_pos = ev.pos(); self.setCursor(Qt.CursorShape.ClosedHandCursor); ev.accept()
        else:
            item = self.itemAt(ev.pos())
            if item and isinstance(item, LegoPiece) and not (ev.modifiers() & Qt.ControlModifier):
                self.scene().clearSelection(); item.setSelected(True)
            super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        self.mouse_scene_pos = self.mapToScene(ev.pos())
        if ev.buttons() & Qt.MouseButton.RightButton:
            delta = ev.pos() - self._last_pan_pos; self._last_pan_pos = ev.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x()); self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else: super().mouseMoveEvent(ev)
        self.viewport().update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton: self.unsetCursor()
        super().mouseReleaseEvent(ev)

    def wheelEvent(self, ev):
        f = 1.15 if ev.angleDelta().y() > 0 else 0.85; self.scale(f, f)

    def drawForeground(self, painter, rect):
        mx, my = self.mouse_scene_pos.x(), self.mouse_scene_pos.y(); s = self.scene().plate.rect().width() if hasattr(self.scene(), 'plate') else 600; grid = config.GRID_SIZE
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
            painter.save(); painter.scale(-1, 1); painter.setPen(QColor(0, 0, 0)); painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            def d_t(v, x, y):
                std = int(round(v/grid))
                if std > 0: painter.drawText(int(-x), int(y), f"{std}")
            d_t(dl, mx-dl/2, my-5); d_t(dr, mx+dr/2, my-5); d_t(du, mx+5, my-du/2); d_t(dd, mx+5, my+dd/2)
            painter.restore()

class LegoConverterView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene); self.setRenderHint(QPainter.RenderHint.Antialiasing); self.setBackgroundBrush(QBrush(QColor("#111")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.grid_color = QColor(255, 0, 0, 150)

    def drawForeground(self, painter, rect):
        grid = config.GRID_SIZE; res = 60; size = res * grid
        pen = QPen(self.grid_color, 1); pen.setCosmetic(True); painter.setPen(pen)
        for x in range(0, size + 1, grid): painter.drawLine(x, 0, x, size)
        for y in range(0, size + 1, grid): painter.drawLine(0, y, size, y)
        bp = QPen(self.grid_color, 2); bp.setCosmetic(True); painter.setPen(bp); painter.drawRect(0, 0, size, size)