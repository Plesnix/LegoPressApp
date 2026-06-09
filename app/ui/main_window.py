# app/ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget
from app.ui.sidebar import Sidebar  # Import the new sidebar
from app.ui.canvas.scene import LegoScene, LegoView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 1. Use the new Sidebar class
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 2. Tabs and Builder
        self.tabs = QTabWidget()
        self.builder_tab = QWidget()
        builder_layout = QVBoxLayout(self.builder_tab)
        
        self.scene = LegoScene()
        self.view = LegoView(self.scene)
        builder_layout.addWidget(self.view)

        self.tabs.addTab(self.builder_tab, "Lego Builder")
        main_layout.addWidget(self.tabs)