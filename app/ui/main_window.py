# app/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QTabWidget, QLabel, QPushButton, QApplication, 
                             QColorDialog, QFileDialog, QScrollArea, QMessageBox, 
                             QTabBar, QSpinBox, QGraphicsPixmapItem, QGraphicsItem)
from PySide6.QtGui import QColor, QPixmap, QPalette, QBrush, QImage, QPainter
from PySide6.QtCore import Qt, QBuffer, QIODevice, QPoint, QRectF
from app.ui.sidebar import Sidebar
from app.ui.canvas.scene import LegoScene, LegoView, LegoPrintView, LegoConverterView 
from app.ui.canvas.items import LegoPiece
from app import config
from PIL import Image
import io

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1200, 800)

        # State
        self.shared_clipboard = [] 
        self.unicolor = "#FF0000"
        self.group_colors = {} 
        self.current_img_item = None 

        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        self.sidebar = Sidebar()
        
        # Selection Info Panel
        self.selection_panel = QWidget(); self.selection_panel.setStyleSheet("background: #1a1a1a; border-top: 1px solid #333;")
        sel_layout = QVBoxLayout(self.selection_panel)
        sel_header = QLabel("SELECTION INFO")
        sel_header.setStyleSheet("font-weight:bold; color:#555; font-size:10px; margin-top:5px;")
        self.selection_label = QLabel("Nothing Selected")
        self.selection_label.setStyleSheet("color:#AAA; font-size:11px;")
        self.selection_label.setWordWrap(True)
        sel_layout.addWidget(sel_header); sel_layout.addWidget(self.selection_label); sel_layout.addStretch()
        self.sidebar.layout().addWidget(self.selection_panel); main_layout.addWidget(self.sidebar)

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab); main_layout.addWidget(self.tabs)
        self.shared_scene = LegoScene(); self.shared_scene.selectionChanged.connect(self.update_selection_info)

        # Permanent Tabs
        self.builder_view = LegoView(self.shared_scene); self.tabs.addTab(self.builder_view, "Main Builder")
        self.print_tab = QWidget(); p_layout = QVBoxLayout(self.print_tab); self.print_view = LegoPrintView(self.shared_scene)
        pc = QHBoxLayout(); self.toggle_color_btn = QPushButton("Toggle Global Unicolor"); self.toggle_color_btn.setCheckable(True)
        self.override_color_btn = QPushButton(); self.override_color_btn.setFixedSize(25, 25); self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor};")
        self.add_group_btn = QPushButton("+ Add Color Group")
        pc.addWidget(self.toggle_color_btn); pc.addWidget(self.override_color_btn); pc.addWidget(self.add_group_btn); pc.addStretch()
        p_layout.addLayout(pc); p_layout.addWidget(self.print_view); self.tabs.addTab(self.print_tab, "Print View")

        # --- IMAGE CONVERTER TAB ---
        self.ai_tab = QWidget(); ai_layout = QVBoxLayout(self.ai_tab)
        self.ai_scene = LegoScene(board_size=60*config.GRID_SIZE, show_plate=False)
        self.ai_view = LegoConverterView(self.ai_scene)
        controls = QHBoxLayout()
        self.import_btn = QPushButton("📁 Import"); self.paste_btn = QPushButton("📋 Paste")
        self.rot_input = QSpinBox(); self.rot_input.setRange(-180, 180); self.rot_input.setSuffix("°")
        self.zoom_input = QSpinBox(); self.zoom_input.setRange(10, 2000); self.zoom_input.setValue(100); self.zoom_input.setSuffix("%")
        self.grid_col_btn = QPushButton(); self.grid_col_btn.setFixedSize(20, 20); self.grid_col_btn.setStyleSheet("background-color: red; border: 1px solid white;")
        self.convert_btn = QPushButton("🚀 1x1 Studs"); self.smart_convert_btn = QPushButton("🧠 Smart Tile Pack")
        self.smart_convert_btn.setStyleSheet("background-color: #1565c0; font-weight: bold; color: white;")
        
        controls.addWidget(self.import_btn); controls.addWidget(self.paste_btn)
        controls.addWidget(QLabel("Rot:")); controls.addWidget(self.rot_input)
        controls.addWidget(QLabel("Zoom:")); controls.addWidget(self.zoom_input)
        controls.addWidget(QLabel("Grid:")); controls.addWidget(self.grid_col_btn)
        controls.addWidget(self.convert_btn); controls.addWidget(self.smart_convert_btn)
        ai_layout.addLayout(controls); ai_layout.addWidget(self.ai_view); self.tabs.addTab(self.ai_tab, "Image Converter")

        self.res_scene = LegoScene(board_size=60*config.GRID_SIZE); self.res_view = LegoView(self.res_scene); self.tabs.addTab(self.res_view, "Converter Result")

        for i in range(4): self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
        self.tabs.tabBar().setTabTextColor(2, QColor("#4CAF50")); self.tabs.tabBar().setTabTextColor(3, QColor("#4CAF50"))

        # Connections
        self.tabs.currentChanged.connect(self.refresh_all_colors) 
        self.toggle_color_btn.clicked.connect(self.refresh_all_colors); self.override_color_btn.clicked.connect(self.pick_global_unicolor)
        self.add_group_btn.clicked.connect(self.create_color_group); self.import_btn.clicked.connect(self.load_image_file); self.paste_btn.clicked.connect(self.paste_image_clip)
        self.grid_col_btn.clicked.connect(self.pick_grid_color)
        self.rot_input.valueChanged.connect(self.update_image_transform); self.zoom_input.valueChanged.connect(self.update_image_transform)
        self.convert_btn.clicked.connect(lambda: self.run_conversion(smart=False))
        self.smart_convert_btn.clicked.connect(lambda: self.run_conversion(smart=True))

    def pick_grid_color(self):
        c = QColorDialog.getColor()
        if c.isValid():
            self.grid_col_btn.setStyleSheet(f"background-color: {c.name()}; border: 1px solid white;")
            self.ai_view.grid_color = c; self.ai_view.viewport().update()

    def update_selection_info(self):
        idx = self.tabs.currentIndex()
        scene = self.res_scene if idx == 3 else self.shared_scene
        sel = [i for i in scene.selectedItems() if isinstance(i, LegoPiece)]
        if not sel: self.selection_label.setText("Nothing Selected"); return
        counts = {}
        for i in sel:
            k = f"{i.w_units}x{i.h_units} {i.shape_type.capitalize()}"
            counts[k] = counts.get(k, 0) + 1
        self.selection_label.setText("\n".join([f"• {c}x {n}" for n, c in counts.items()]))

    def get_adapted_color(self, w, h, shape, hex_in):
        if self.tabs.currentIndex() == 0:
            for lw, lh, lc, ln, ls in config.LIBRARY_DATA:
                if lw == w and lh == h and ls == shape: return lc
            return "#A0A0A0"
        return hex_in

    def close_tab(self, index):
        if index > 3: self.tabs.removeTab(index)

    def pick_global_unicolor(self):
        c = QColorDialog.getColor()
        if c.isValid(): self.unicolor = c.name(); self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor};"); self.refresh_all_colors()

    def create_color_group(self):
        self.group_counter += 1; gid = self.group_counter; self.group_colors[gid] = "#FF00FF"
        row_w = QWidget(); row = QHBoxLayout(row_w); row.setContentsMargins(2,2,2,2)
        c_btn = QPushButton(); c_btn.setFixedSize(20, 20); c_btn.setStyleSheet(f"background-color: #FF00FF;")
        s_btn = QPushButton(f"Assign Group {gid}"); d_btn = QPushButton("X"); d_btn.setFixedSize(20, 20); d_btn.setStyleSheet("color: red;")
        row.addWidget(c_btn); row.addWidget(s_btn); row.addWidget(d_btn); row.addStretch()
        def delete_group(): row_w.deleteLater(); del self.group_colors[gid]; self.refresh_all_colors()
        def pick_group_color():
            c = QColorDialog.getColor(); 
            if c.isValid(): self.group_colors[gid] = c.name(); c_btn.setStyleSheet(f"background-color: {c.name()};"); self.refresh_all_colors()
        def assign_selection():
            for i in self.shared_scene.selectedItems():
                if isinstance(i, LegoPiece): i.color_group_id = gid
            self.refresh_all_colors()
        c_btn.clicked.connect(pick_group_color); s_btn.clicked.connect(assign_selection); d_btn.clicked.connect(delete_group)
        self.groups_layout.insertWidget(self.groups_layout.count() - 1, row_w)

    def refresh_all_colors(self):
        is_p = (self.tabs.currentIndex() == 1)
        for i in self.shared_scene.items():
            if isinstance(i, LegoPiece):
                i.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not is_p)
                if not is_p: i.set_color_override(None)
                else:
                    if self.toggle_color_btn.isChecked(): i.set_color_override(self.unicolor)
                    elif getattr(i, 'color_group_id', None) in self.group_colors: i.set_color_override(self.group_colors[i.color_group_id])
                    else: i.set_color_override(None)

    def load_image_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if p: self.set_converter_image(QPixmap(p))

    def paste_image_clip(self):
        cb = QApplication.clipboard().mimeData()
        if cb.hasImage(): self.set_converter_image(QPixmap(cb.imageData()))

    def set_converter_image(self, pix):
        if self.current_img_item: self.ai_scene.removeItem(self.current_img_item)
        self.current_img_item = QGraphicsPixmapItem(pix); self.current_img_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.current_img_item.setZValue(-200); self.ai_scene.addItem(self.current_img_item)
        self.ai_view.centerOn(self.current_img_item); self.rot_input.setValue(0); self.zoom_input.setValue(100)
        self.update_image_transform()

    def update_image_transform(self):
        if self.current_img_item:
            angle, scale = self.rot_input.value(), self.zoom_input.value() / 100.0
            center = self.current_img_item.pixmap().rect().center()
            self.current_img_item.setTransformOriginPoint(center)
            self.current_img_item.setRotation(angle); self.current_img_item.setScale(scale)

    def run_conversion(self, smart=False):
        if not self.current_img_item: return
        res = 60; grid = config.GRID_SIZE; size = res * grid
        self.res_scene = LegoScene(board_size=size)
        self.res_scene.selectionChanged.connect(self.update_selection_info)
        self.res_view.setScene(self.res_scene)
        img = QImage(size, size, QImage.Format.Format_RGB32); img.fill(Qt.GlobalColor.white)
        p = QPainter(img); self.ai_scene.render(p, QRectF(0, 0, size, size), QRectF(0, 0, size, size)); p.end()
        mask = [[False for _ in range(res)] for _ in range(res)]
        for y in range(res):
            for x in range(res):
                if img.pixelColor(x*grid+grid//2, y*grid+grid//2).lightness() < 245: mask[y][x] = True
        if not smart:
            for y in range(res):
                for x in range(res):
                    if mask[y][x]: self.res_scene.addItem(LegoPiece(x*grid, y*grid, 1, 1, self.unicolor, "round"))
        else:
            rects = sorted([p for p in config.LIBRARY_DATA if p[4] == "Rectangle"], key=lambda x: x[0]*x[1], reverse=True)
            for y in range(res):
                for x in range(res):
                    if not mask[y][x]: continue
                    placed = False
                    for rw, rh, rcol, rname, rsid in rects:
                        if x + rw <= res and y + rh <= res:
                            if all(mask[y+iy][x+ix] for iy in range(rh) for ix in range(rw)):
                                for iy in range(rh):
                                    for ix in range(rw): mask[y+iy][x+ix] = False
                                self.res_scene.addItem(LegoPiece(x*grid, y*grid, rw, rh, self.unicolor, "rect"))
                                placed = True; break
                    if not placed:
                        self.res_scene.addItem(LegoPiece(x*grid, y*grid, 1, 1, self.unicolor, "round"))
                        mask[y][x] = False
        self.tabs.setCurrentIndex(3); self.res_view.centerOn(self.res_scene.plate)