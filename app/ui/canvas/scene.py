# app/ui/canvas/scene.py
import copy
from PySide6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsRectItem, 
                             QGraphicsLineItem, QGraphicsItemGroup, QGraphicsItem)
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QCursor
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
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Clipboard and Ghosting state
        self.clipboard = []  
        self.ghost_group = None 
        self._last_pan_pos = QPoint()

    # --- UNIFIED KEYBOARD LOGIC ---
    def keyPressEvent(self, event):
        # 1. Copy (Ctrl+C)
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.ControlModifier:
            self.copy_selection()
        
        # 2. Paste (Ctrl+V)
        elif event.key() == Qt.Key.Key_V and event.modifiers() & Qt.ControlModifier:
            self.start_paste_mode()

        # 3. Rotate (R)
        elif event.key() == Qt.Key.Key_R:
            for item in self.scene().selectedItems():
                if hasattr(item, 'rotate_90'):
                    item.rotate_90()

        # 4. Delete (Delete/Backspace)
        elif event.key() in [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]:
            for item in self.scene().selectedItems():
                self.scene().removeItem(item)

        # 5. Cancel Paste (Escape)
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel_paste_mode()

        super().keyPressEvent(event)

    def copy_selection(self):
        # We only want to copy actual Lego pieces
        selected = [i for i in self.scene().selectedItems() if isinstance(i, LegoPiece)]
        if not selected: return

        self.clipboard = []
        # Find the reference point (top-left of the whole group)
        min_x = min(item.pos().x() for item in selected)
        min_y = min(item.pos().y() for item in selected)

        for item in selected:
            self.clipboard.append({
                'w': item.w_units,
                'h': item.h_units,
                'color': item.color,
                'shape': item.shape_type,
                'angle': item.current_angle,
                'rel_x': item.pos().x() - min_x, # Offset from the top-left
                'rel_y': item.pos().y() - min_y
            })
        print(f"Copied {len(self.clipboard)} items.")

    def start_paste_mode(self):
        if not self.clipboard: return
        self.cancel_paste_mode() 

        self.ghost_group = QGraphicsItemGroup()
        self.scene().addItem(self.ghost_group)
        self.ghost_group.setZValue(1000) 

        for data in self.clipboard:
            ghost = LegoPiece(data['rel_x'], data['rel_y'], data['w'], data['h'], data['color'], data['shape'])
            ghost.current_angle = data['angle']
            ghost.refresh_shape()
            ghost.setOpacity(0.4) 
            # Disable interaction for the ghosts
            ghost.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            ghost.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            self.ghost_group.addToGroup(ghost)
        
        # Position the ghost immediately at the mouse
        self.update_ghost_pos(self.mapFromGlobal(QCursor.pos()))

    def cancel_paste_mode(self):
        if self.ghost_group:
            self.scene().removeItem(self.ghost_group)
            self.ghost_group = None

    def update_ghost_pos(self, mouse_pos):
        if not self.ghost_group: return
        scene_pos = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
        
        # Snap the whole group to the grid
        snap_x = round(scene_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
        snap_y = round(scene_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
        self.ghost_group.setPos(snap_x, snap_y)

    # --- UNIFIED MOUSE LOGIC ---
    def mousePressEvent(self, event):
        # 1. Right Click: Pan OR Cancel Paste
        if event.button() == Qt.MouseButton.RightButton:
            if self.ghost_group:
                self.cancel_paste_mode()
            else:
                self._last_pan_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

          # 2. Left Click: "Stamp" Paste OR Standard Selection
        elif event.button() == Qt.MouseButton.LeftButton:
            if self.ghost_group:
                # COMMIT PASTE
                base_x = self.ghost_group.pos().x()
                base_y = self.ghost_group.pos().y()
                
                # --- NEW: Clear selection so we can select the new pieces ---
                self.scene().clearSelection()

                for data in self.clipboard:
                    new_piece = LegoPiece(base_x + data['rel_x'], base_y + data['rel_y'], 
                                         data['w'], data['h'], data['color'], data['shape'])
                    new_piece.current_angle = data['angle']
                    new_piece.refresh_shape()
                    self.scene().addItem(new_piece)
                    
                    # --- NEW: Select the newly created piece ---
                    new_piece.setSelected(True)
                
                self.cancel_paste_mode()
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.ghost_group:
            self.update_ghost_pos(event.pos())
        
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

    # --- DRAG AND DROP ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        data_string = event.mimeData().text()
        try:
            parts = data_string.split(",")
            w_u, h_u, color = int(parts[0]), int(parts[1]), parts[2]
            shape = parts[3] if len(parts) > 3 else "rect"
            raw_pos = self.mapToScene(event.pos())
            snap_x = round(raw_pos.x() / config.GRID_SIZE) * config.GRID_SIZE
            snap_y = round(raw_pos.y() / config.GRID_SIZE) * config.GRID_SIZE
            new_piece = LegoPiece(snap_x, snap_y, w_u, h_u, color, shape)
            self.scene().addItem(new_piece)
            event.acceptProposedAction()
        except Exception as e:
            print(f"Drop error: {e}")
            event.ignore()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.scale(factor, factor)

class LegoPrintView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor("#000000"))) # Pure black void
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- HORIZONTAL MIRRORING ---
        # scale(-1, 1) flips the X-axis (Left <-> Right)
        # scale(1, -1) would have flipped the Y-axis (Top <-> Bottom)
        self.scale(-1, 1)
        
        # 2. LOCK THE VIEW
        # We don't want to move pieces or drag things in the Print View
        self.setInteractive(False) 
        
        # Set the view to look ONLY at the baseplate
        self.setSceneRect(0, 0, config.BASEPLATE_SIZE, config.BASEPLATE_SIZE)

    def drawForeground(self, painter, rect):
        """This acts as a 'Mask' to hide pieces outside the baseplate."""
        # We draw a giant black frame around the baseplate area 
        # so any pieces in the 'void' are hidden in this tab.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0)) # Match the background color
        
        s = config.BASEPLATE_SIZE
        # Draw 4 large rectangles around the 0,0 to s,s area
        painter.drawRect(-2000, -2000, 5000, 2000) # Top
        painter.drawRect(-2000, s, 5000, 2000)     # Bottom
        painter.drawRect(-2000, 0, 2000, s)        # Left
        painter.drawRect(s, 0, 2000, s)            # Right