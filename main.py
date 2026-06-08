import sys
from PySide6.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, 
                             QGraphicsRectItem, QMainWindow, QVBoxLayout, QWidget, QGraphicsItem)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QPen, QColor, QPainter

# Global Settings
GRID_SIZE = 20
BASEPLATE_SIZE = 400 # 20x20 studs if grid is 20

class LegoPiece(QGraphicsRectItem):
    def __init__(self, x, y, width_units, height_units, color):
        # width_units/height_units is "how many studs"
        # We multiply by GRID_SIZE to get actual pixels
        w = width_units * GRID_SIZE
        h = height_units * GRID_SIZE
        super().__init__(0, 0, w, h)
        
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(color)))
        # Using Cosmetic pen ensures the line stays 1px regardless of zoom
        pen = QPen(Qt.GlobalColor.black, 1)
        pen.setCosmetic(True) 
        self.setPen(pen)
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            new_pos = value 
            
            # 1. Snap to Grid Logic
            x = round(new_pos.x() / GRID_SIZE) * GRID_SIZE
            y = round(new_pos.y() / GRID_SIZE) * GRID_SIZE
            
            # 2. Boundary Clamping (Prevent leaving the baseplate)
            # Get piece dimensions
            rect = self.rect()
            
            # Limit X (0 to Baseplate Width - Piece Width)
            x = max(0, min(x, BASEPLATE_SIZE - rect.width()))
            # Limit Y (0 to Baseplate Height - Piece Height)
            y = max(0, min(y, BASEPLATE_SIZE - rect.height()))
            
            return QPointF(x, y)
        
        return super().itemChange(change, value)

class LegoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Builder")
        self.resize(800, 600)

        # 1. Create the Scene
        self.scene = QGraphicsScene(0, 0, BASEPLATE_SIZE, BASEPLATE_SIZE)
        # Give the baseplate a distinct background color
        self.scene.setBackgroundBrush(QBrush(QColor(50, 50, 50))) 
        self.draw_grid()

        # 2. Create the View
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        # This keeps the baseplate in the center of the window
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.view)
        self.setCentralWidget(central_widget)

        # 4. Add test pieces (X, Y, Width in studs, Height in studs, Color)
        # A 2x1 brick
        brick1 = LegoPiece(40, 40, 2, 1, "#e63946")
        self.scene.addItem(brick1)
        
        # A 1x1 brick
        brick2 = LegoPiece(100, 100, 1, 1, "#a8dadc")
        self.scene.addItem(brick2)

    def draw_grid(self):
        pen = QPen(QColor(80, 80, 80), 1)
        pen.setCosmetic(True)
        
        for x in range(0, BASEPLATE_SIZE + 1, GRID_SIZE):
            self.scene.addLine(x, 0, x, BASEPLATE_SIZE, pen)
        for y in range(0, BASEPLATE_SIZE + 1, GRID_SIZE):
            self.scene.addLine(0, y, BASEPLATE_SIZE, y, pen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LegoApp()
    window.show()
    sys.exit(app.exec())