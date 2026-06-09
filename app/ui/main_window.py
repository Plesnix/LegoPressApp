# app/ui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget
from app.ui.sidebar import Sidebar
from app.ui.canvas.scene import LegoScene, LegoView, LegoPrintView # Import the new view

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1100, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 1. Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 2. Tabs Area
        self.tabs = QTabWidget()
        
        # --- Create the SHARED scene ---
        self.shared_scene = LegoScene()

        # TAB 1: Lego Builder
        self.builder_tab = QWidget()
        builder_layout = QVBoxLayout(self.builder_tab)
        self.builder_view = LegoView(self.shared_scene) # Uses shared scene
        builder_layout.addWidget(self.builder_view)
        self.tabs.addTab(self.builder_tab, "Lego Builder")

        # TAB 2: Print View (The New Tab)
        self.print_tab = QWidget()
        print_layout = QVBoxLayout(self.print_tab)
        self.print_view = LegoPrintView(self.shared_scene) # Uses SAME shared scene
        print_layout.addWidget(self.print_view)
        self.tabs.addTab(self.print_tab, "Print View")

        # TAB 3: Future AI
        self.ai_tab = QWidget()
        self.tabs.addTab(self.ai_tab, "Image Converter")

        main_layout.addWidget(self.tabs)