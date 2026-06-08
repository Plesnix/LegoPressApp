# app/ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QLabel, QPushButton
from app.ui.canvas.scene import LegoScene, LegoView
from app.ui.canvas.items import LegoPiece

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1100, 700)

        # Layout Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 1. SIDEBAR (Left)
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #252525; border-right: 1px solid #444;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(QLabel("CONTROLS & LIBRARY"))
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # 2. TABS AREA (Right)
        self.tabs = QTabWidget()
        
        # TAB 1: BUILDER
        self.builder_tab = QWidget()
        builder_layout = QVBoxLayout(self.builder_tab)
        
        # Initialize Scene and View
        self.scene = LegoScene()
        self.view = LegoView(self.scene)
        builder_layout.addWidget(self.view)
        
        # Add a test piece
        test_brick = LegoPiece(40, 40, 2, 4, "red")
        self.scene.addItem(test_brick)

        self.tabs.addTab(self.builder_tab, "Lego Builder")
        
        # TAB 2: FUTURE
        self.ai_tab = QWidget()
        self.tabs.addTab(self.ai_tab, "Image Converter")

        main_layout.addWidget(self.tabs)