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
        
        # 1. Create the Physical Baseplate
        self.plate = QGraphicsRectItem(0, 0, config.BASEPLATE_SIZE, config.BASEPLATE_SIZE)
        self.plate.setBrush(QBrush(QColor(config.PLATE_COLOR)))
        self.plate.setPen(QPen(Qt.GlobalColor.black, 2))
        self.plate.setZValue(-100)
        self.addItem(self.plate)

        # 2. Create the Grid Lines
        line_pen = QPen(QColor(config.GRID_LINE_COLOR), 1)
        line_pen.setCosmetic(True)
        for x in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(x, 0, x, config.BASEPLATE_SIZE)
            line.setPen(line_pen); line.setZValue(-99); self.addItem(line)
        for y in range(0, config.BASEPLATE_SIZE + 1, config.GRID_SIZE):
            line = QGraphicsLineItem(0, y, config.BASEPLATE_SIZE, y)
            line.setPen(line_pen); line.setZValue(-99); self.addItem(line)

class LegoView(QGraphicsView):
    """ The Standard Builder View """
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(config.VOID_COLOR)))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.clipboard = []  
        self.ghost_group = None 
        self._last_pan_pos = QPoint()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key.Key_C: self.copy_selection()
            elif event.key() == Qt.Key.Key_V: self.start_paste_mode()
 
        if event.key() == Qt.Key.Key_T:
            self.rotate_selection_90()

        
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
        """Rotates all selected items around their common center in grid coordinates."""
        selected_items = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not selected_items:
            return

        grid = config.GRID_SIZE

        # 1. Find the bounding box of the whole group in GRID UNITS (Studs)
        min_gx, min_gy = float('inf'), float('inf')
        max_gx, max_gy = float('-inf'), float('-inf')

        item_data = [] # Temporary storage to keep track of current states

        for item in selected_items:
            # Current position in studs
            gx, gy = item.pos().x() / grid, item.pos().y() / grid
            
            # Current width/height in studs based on current orientation
            rect = item.boundingRect()
            gw, gh = rect.width() / grid, rect.height() / grid
            
            min_gx = min(min_gx, gx)
            min_gy = min(min_gy, gy)
            max_gx = max(max_gx, gx + gw)
            max_gy = max(max_gy, gy + gh)
            
            item_data.append({
                'item': item,
                'gx': gx,
                'gy': gy,
                'gw': gw,
                'gh': gh
            })

        # 2. Calculate the Group Pivot Point in Studs
        pgx = (min_gx + max_gx) / 2.0
        pgy = (min_gy + max_gy) / 2.0

        # 3. Process each item
        for data in item_data:
            item = data['item']
            
            # Calculate current center in studs
            cgx = data['gx'] + data['gw'] / 2.0
            cgy = data['gy'] + data['gh'] / 2.0

            # 4. Rotate the Center Point 90 degrees around the Group Pivot
            # Formula for rotating point (x,y) around pivot (px,py):
            # new_x = px - (y - py)
            # new_y = py + (x - px)
            new_cgx = pgx - (cgy - pgy)
            new_cgy = pgy + (cgx - pgx)

            # 5. Spin the piece itself (swaps its width and height)
            item.rotate_90()

            # 6. Get the NEW dimensions in studs
            new_rect = item.boundingRect()
            new_gw = new_rect.width() / grid
            new_gh = new_rect.height() / grid

            # 7. Calculate new Top-Left position in studs
            # (TopLeft = New Center - New Half Size)
            new_gx = new_cgx - new_gw / 2.0
            new_gy = new_cgy - new_gh / 2.0

            # 8. Snap to grid and set pixel position
            # Rounding to the nearest stud (int) removes all "disjointed" drift
            final_x = round(new_gx) * grid
            final_y = round(new_gy) * grid
            
            item.setPos(QPointF(final_x, final_y))

    def copy_selection(self):
        selected = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not selected: return
        self.clipboard = []
        min_x = min(item.pos().x() for item in selected)
        min_y = min(item.pos().y() for item in selected)
        for item in selected:
            self.clipboard.append({
                'w': item.w_units, 'h': item.h_units, 'color': item.color,
                'shape': item.shape_type, 'angle': item.current_angle,
                'rel_x': item.pos().x() - min_x, 'rel_y': item.pos().y() - min_y
            })

    def start_paste_mode(self):
        if not self.clipboard: return
        self.cancel_paste_mode() 
        self.ghost_group = QGraphicsItemGroup()
        self.scene().addItem(self.ghost_group)
        for data in self.clipboard:
            ghost = LegoPiece(data['rel_x'], data['rel_y'], data['w'], data['h'], data['color'], data['shape'])
            ghost.current_angle = data['angle']
            ghost.refresh_shape()
            ghost.setOpacity(0.5) 
            ghost.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            ghost.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            self.ghost_group.addToGroup(ghost)
        self.update_ghost_pos(self.mapFromGlobal(QCursor.pos()))

    def cancel_paste_mode(self):
        if self.ghost_group:
            self.scene().removeItem(self.ghost_group)
            self.ghost_group = None

    def update_ghost_pos(self, mouse_pos):
        if not self.ghost_group: return
        scene_pos = self.mapToScene(self.mapFromFrame(mouse_pos) if hasattr(self, 'mapFromFrame') else self.mapFromGlobal(QCursor.pos()))
        # If standard map fails, just use global cursor relative to viewport
        view_pos = self.mapFromGlobal(QCursor.pos())
        scene_pos = self.mapToScene(view_pos)
        snap_x = round(scene_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
        snap_y = round(scene_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
        self.ghost_group.setPos(snap_x, snap_y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            if self.ghost_group: self.cancel_paste_mode()
            else:
                self._last_pan_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton and self.ghost_group:
            self.scene().clearSelection()
            base_x, base_y = self.ghost_group.pos().x(), self.ghost_group.pos().y()
            for data in self.clipboard:
                new_p = LegoPiece(base_x + data['rel_x'], base_y + data['rel_y'], data['w'], data['h'], data['color'], data['shape'])
                new_p.current_angle = data['angle']; new_p.refresh_shape(); self.scene().addItem(new_p); new_p.setSelected(True)
            self.cancel_paste_mode()
        else: super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.ghost_group: self.update_ghost_pos(event.pos())
        if event.buttons() & Qt.MouseButton.RightButton:
            delta = self._last_pan_pos - event.pos()
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
        else: super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton: self.unsetCursor()
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
    def dragMoveEvent(self, event): event.acceptProposedAction()
    def dropEvent(self, event):
        try:
            parts = event.mimeData().text().split(",")
            w, h, col, shp = int(parts[0]), int(parts[1]), parts[2], parts[3] if len(parts)>3 else "rect"
            raw = self.mapToScene(event.pos())
            sx = round(raw.x() / config.GRID_SIZE) * config.GRID_SIZE
            sy = round(raw.y() / config.GRID_SIZE) * config.GRID_SIZE
            self.scene().addItem(LegoPiece(sx, sy, w, h, col, shp))
            event.acceptProposedAction()
        except: event.ignore()

class LegoPrintView(QGraphicsView):
    """ The Mirrored Print View with Smart Guides """
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#000000")))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 1. Mirror horizontally (X-axis)
        self.scale(-1, 1) 
        
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        self._last_pan_pos = QPoint()
        self.mouse_scene_pos = QPointF(0, 0)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.mouse_scene_pos = self.mapToScene(event.pos())
        
        if event.buttons() & Qt.MouseButton.RightButton:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            
            # --- THE PANNING FIX ---
            # Standard: value - delta
            # Mirrored: Because scale is -1, horizontal delta must be ADDED 
            # to make the 'camera' move with the mouse.
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            
        self.viewport().update() 
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.unsetCursor()
        super().mouseReleaseEvent(event)

    def drawForeground(self, painter, rect):
        mx, my = self.mouse_scene_pos.x(), self.mouse_scene_pos.y()
        s = config.BASEPLATE_SIZE
        grid = config.GRID_SIZE

        # 1. Mask (Black background outside baseplate)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 255))
        painter.drawRect(-2000, -2000, 5000, 2000) 
        painter.drawRect(-2000, s, 5000, 2000)     
        painter.drawRect(-2000, 0, 2000, s)        
        painter.drawRect(s, 0, 2000, s)            

        # 2. Measurement Tool (Only inside plate)
        if 0 <= mx <= s and 0 <= my <= s:
            # Change Pen to Black for the Crosshairs
            guide_pen = QPen(QColor(0, 0, 0, 200), 1, Qt.PenStyle.DashLine)
            guide_pen.setCosmetic(True)
            painter.setPen(guide_pen)

            painter.drawLine(QPointF(0, my), QPointF(s, my))
            painter.drawLine(QPointF(mx, 0), QPointF(mx, s))

            # Measurement Logic
            all_items = [i for i in self.scene().items() if isinstance(i, LegoPiece) and i.isVisible()]
            dl, dr, du, dd = mx, s - mx, my, s - my

            for item in all_items:
                ir = item.sceneBoundingRect()
                if ir.top() <= my <= ir.bottom():
                    if ir.right() <= mx: dl = min(dl, mx - ir.right())
                    elif ir.left() >= mx: dr = min(dr, ir.left() - mx)
                if ir.left() <= mx <= ir.right():
                    if ir.bottom() <= my: du = min(du, my - ir.bottom())
                    elif ir.top() >= my: dd = min(dd, ir.top() - my)

            # 3. Draw Black Labels
            painter.save()
            # Un-mirror the coordinate system for text so it isn't backward
            painter.scale(-1, 1) 
            painter.setPen(QColor(0, 0, 0)) # Set text to Black
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            
            def d_txt(v, x, y):
                std = round(v / grid)
                if std > 0:
                    # Because we scaled -1, we must pass negative X to get it back on screen
                    painter.drawText(int(-x), int(y), f"{std}")

            d_txt(dl, mx - dl/2, my - 5)
            d_txt(dr, mx + dr/2, my - 5)
            d_txt(du, mx + 5, my - du/2)
            d_txt(dd, mx + 5, my + dd/2)
            painter.restore()