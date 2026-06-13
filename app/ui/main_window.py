# app/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QTabWidget, QLabel, QPushButton, QApplication, 
                             QColorDialog, QFileDialog, QScrollArea)
from PySide6.QtGui import QColor, QPixmap, QPalette, QBrush
from PySide6.QtCore import Qt
from app.ui.sidebar import Sidebar
from app.ui.canvas.scene import LegoScene, LegoView, LegoPrintView 
from app.ui.canvas.items import LegoPiece

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1200, 800)

        self.unicolor = "#FFFFFF"
        self.group_counter = 0
        self.group_colors = {} 

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.shared_scene = LegoScene()

        # TAB 1: Builder
        self.builder_tab = QWidget()
        builder_layout = QVBoxLayout(self.builder_tab)
        self.builder_view = LegoView(self.shared_scene)
        builder_layout.addWidget(self.builder_view)
        self.tabs.addTab(self.builder_tab, "Lego Builder")

        # TAB 2: Print
        self.print_tab = QWidget()
        print_layout = QVBoxLayout(self.print_tab)
        self.print_view = LegoPrintView(self.shared_scene)

        self.print_controls = QHBoxLayout()
        self.toggle_color_btn = QPushButton("Toggle Global Unicolor")
        self.toggle_color_btn.setCheckable(True)
        self.override_color_btn = QPushButton()
        self.override_color_btn.setFixedSize(25, 25)
        self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor}; border: 1px solid white;")
        self.add_group_btn = QPushButton("+ Add Color Group")
        self.print_controls.addWidget(self.toggle_color_btn)
        self.print_controls.addWidget(self.override_color_btn)
        self.print_controls.addWidget(self.add_group_btn)
        self.print_controls.addStretch()

        self.groups_scroll = QScrollArea()
        self.groups_scroll.setWidgetResizable(True)
        self.groups_scroll.setMaximumHeight(200)
        self.groups_scroll.setStyleSheet("border: none; background: transparent;")
        self.groups_container = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_container)
        self.groups_layout.setContentsMargins(5, 0, 5, 0); self.groups_layout.setSpacing(2); self.groups_layout.addStretch()
        self.groups_scroll.setWidget(self.groups_container)
        self.groups_scroll.hide()

        print_layout.addLayout(self.print_controls)
        print_layout.addWidget(self.groups_scroll); print_layout.addWidget(self.print_view)
        self.tabs.addTab(self.print_tab, "Print View")

        # TAB 3: Image
        self.ai_tab = QWidget(); ai_layout = QVBoxLayout(self.ai_tab)
        self.image_display = QLabel("No Image Loaded")
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display.setStyleSheet("border: 2px dashed #444; background: #111; color: #555;")
        img_btns = QHBoxLayout()
        self.import_file_btn = QPushButton("Import from File"); self.paste_clip_btn = QPushButton("Paste from Clipboard")
        img_btns.addWidget(self.import_file_btn); img_btns.addWidget(self.paste_clip_btn)
        ai_layout.addLayout(img_btns); ai_layout.addWidget(self.image_display)
        self.tabs.addTab(self.ai_tab, "Image Converter")

        # Connections
        self.tabs.currentChanged.connect(self.refresh_all_colors) 
        self.toggle_color_btn.clicked.connect(self.refresh_all_colors)
        self.override_color_btn.clicked.connect(self.pick_global_unicolor)
        self.add_group_btn.clicked.connect(self.create_color_group)
        self.import_file_btn.clicked.connect(self.load_image_file)
        self.paste_clip_btn.clicked.connect(self.paste_image_clip)

    def pick_global_unicolor(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.unicolor = c.name()
            self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor}; border: 1px solid white;")
            self.refresh_all_colors()

    def create_color_group(self):
        self.group_counter += 1; gid = self.group_counter; self.group_colors[gid] = "#FF00FF"; self.groups_scroll.show()
        row_w = QWidget(); row = QHBoxLayout(row_w); row.setContentsMargins(2,2,2,2)
        c_btn = QPushButton(); c_btn.setFixedSize(20, 20); c_btn.setStyleSheet(f"background-color: {self.group_colors[gid]};")
        s_btn = QPushButton(f"Assign Selected to Group {gid}")
        d_btn = QPushButton("X"); d_btn.setFixedSize(20, 20); d_btn.setStyleSheet("color: red; font-weight: bold;")
        row.addWidget(c_btn); row.addWidget(s_btn); row.addWidget(d_btn); row.addStretch()
        self.groups_layout.insertWidget(self.groups_layout.count() - 1, row_w)

        def delete_group():
            row_w.deleteLater(); del self.group_colors[gid]
            for i in self.shared_scene.items():
                if isinstance(i, LegoPiece) and getattr(i, 'color_group_id', None) == gid: i.color_group_id = None
            self.refresh_all_colors()
            if not self.group_colors: self.groups_scroll.hide()

        def pick_group_color():
            c = QColorDialog.getColor()
            if c.isValid():
                self.group_colors[gid] = c.name(); c_btn.setStyleSheet(f"background-color: {c.name()};"); self.refresh_all_colors()

        def assign_selection():
            for i in self.shared_scene.selectedItems():
                if isinstance(i, LegoPiece): i.color_group_id = gid
            self.refresh_all_colors()

        c_btn.clicked.connect(pick_group_color); s_btn.clicked.connect(assign_selection); d_btn.clicked.connect(delete_group)

    def refresh_all_colors(self):
        is_print_tab = (self.tabs.currentIndex() == 1)
        is_global_unicolor = self.toggle_color_btn.isChecked()

        for item in self.shared_scene.items():
            if isinstance(item, LegoPiece):
                # Freeze movement in Print View, allow in Builder
                item.setFlag(item.GraphicsItemFlag.ItemIsMovable, not is_print_tab)
                
                if not hasattr(item, 'original_color'): 
                    item.original_color = item.brush().color().name()
                
                if not is_print_tab:
                    target = item.original_color
                else:
                    if is_global_unicolor:
                        target = self.unicolor
                    elif getattr(item, 'color_group_id', None) in self.group_colors:
                        target = self.group_colors[item.color_group_id]
                    else:
                        target = item.original_color
                
                item.setBrush(QBrush(QColor(target)))

    def load_image_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if p: self.show_image(QPixmap(p))

    def paste_image_clip(self):
        cb = QApplication.clipboard().mimeData()
        if cb.hasImage(): self.show_image(QPixmap(cb.imageData()))

    def show_image(self, pix):
        self.image_display.setPixmap(pix.scaled(self.image_display.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.image_display.setText("")