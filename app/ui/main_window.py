# app/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                             QVBoxLayout, QTabWidget, QLabel, QPushButton, QApplication)
from PySide6.QtGui import QColor, QPixmap, QPalette
from PySide6.QtCore import Qt
from app.ui.sidebar import Sidebar
from app.ui.canvas.scene import LegoScene, LegoView, LegoPrintView 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1100, 700)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 1. Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 2. Tabs Area
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- Create the SHARED scene ---
        self.shared_scene = LegoScene()

        # --- TAB 1: Lego Builder ---
        self.builder_tab = QWidget()
        builder_layout = QVBoxLayout(self.builder_tab)
        self.builder_view = LegoView(self.shared_scene)
        builder_layout.addWidget(self.builder_view)
        self.tabs.addTab(self.builder_tab, "Lego Builder")

        # --- TAB 2: Print View ---
        self.print_view = LegoPrintView(self.shared_scene) # Create the object FIRST
        self.print_tab = QWidget()
        print_layout = QVBoxLayout(self.print_tab)

        # Controls for Print View
        self.print_controls = QHBoxLayout()
        self.toggle_color_btn = QPushButton("Toggle Unicolor")
        self.toggle_color_btn.setCheckable(True)

        self.override_color_btn = QPushButton()
        self.override_color_btn.setFixedSize(25, 25)
        self.unicolor = "#FFFFFF" 
        self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor}; border: 1px solid white;")

        self.print_controls.addWidget(self.toggle_color_btn)
        self.print_controls.addWidget(self.override_color_btn)
        self.print_controls.addStretch()

        print_layout.addLayout(self.print_controls)
        print_layout.addWidget(self.print_view)
        self.tabs.addTab(self.print_tab, "Print View") # ADD the tab to the widget

        # --- TAB 3: Image Converter ---
        self.ai_tab = QWidget()
        ai_layout = QVBoxLayout(self.ai_tab)

        self.import_img_btn = QPushButton("Import / Paste Image")
        self.image_display = QLabel("No Image Loaded")
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display.setStyleSheet("border: 2px dashed #444; background: #111;")
        
        ai_layout.addWidget(self.import_img_btn)
        ai_layout.addWidget(self.image_display)
        self.tabs.addTab(self.ai_tab, "Image Converter")

        # --- Button Connections ---
        self.toggle_color_btn.clicked.connect(self.apply_color_toggle)
        self.override_color_btn.clicked.connect(self.pick_override_color)
        self.import_img_btn.clicked.connect(self.load_image)

    # --- Methods (Moved outside of __init__ and indented correctly) ---

    def load_image(self):
        from PySide6.QtWidgets import QFileDialog
        
        # 1. Try to Load from File
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            pixmap = QPixmap(file_path)
            self.image_display.setPixmap(pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio))
            self.image_display.setText("")
            return

        # 2. Try to Paste from Clipboard if no file chosen
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasImage():
            pixmap = QPixmap(mime_data.imageData())
            self.image_display.setPixmap(pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio))
            self.image_display.setText("")

    def pick_override_color(self):
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            self.unicolor = color.name()
            self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor}; border: 1px solid white;")
            if self.toggle_color_btn.isChecked():
                self.apply_color_toggle()

    def apply_color_toggle(self):
        is_on = self.toggle_color_btn.isChecked()
        color_to_apply = self.unicolor if is_on else None
        
        from app.ui.canvas.items import LegoPiece
        for item in self.shared_scene.items():
            if isinstance(item, LegoPiece):
                item.set_color_override(color_to_apply)