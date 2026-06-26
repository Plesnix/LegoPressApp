# app/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QLabel, QPushButton, 
                             QApplication, QColorDialog, QFileDialog, QScrollArea, QMessageBox, QTabBar, 
                             QDoubleSpinBox, QSpinBox, QGraphicsPixmapItem, QGraphicsItem, QComboBox, QGraphicsView)
from PySide6.QtGui import QColor, QPixmap, QPalette, QBrush, QImage, QPainter
from PySide6.QtCore import Qt, QBuffer, QIODevice, QPoint, QRectF
from app.ui.sidebar import Sidebar
from app.ui.canvas.scene import LegoScene, LegoView, LegoPrintView, LegoConverterView 
from app.ui.canvas.items import LegoPiece
from app import config
from PIL import Image
import io
from collections import Counter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lego Press Suite")
        self.resize(1300, 850)

        # --- STATE ---
        self.shared_clipboard = []; self.unicolor = "#FF0000"; self.group_colors = {}; self.current_img_item = None 
        self.library_colors = {"round": "#FFD700", "1748": "#FFD700", "heart": "#EC34CE", "L": "#E63946", "triangle": "#E63946", "24246": "#4FB0C6", "5520": "#4FB0C6", "macaroni": "#4FB0C6", "5092": "#A0A0A0", "Rectangle": "#A0A0A0"}

        central_widget = QWidget(); self.setCentralWidget(central_widget); main_layout = QHBoxLayout(central_widget)
        self.sidebar = Sidebar()
        
        # Selection Info Panel
        self.selection_panel = QWidget(); self.selection_panel.setStyleSheet("background: #1a1a1a; border-top: 1px solid #333;")
        sel_layout = QVBoxLayout(self.selection_panel)
        sel_header = QLabel("SELECTION INFO"); sel_header.setStyleSheet("color:#555; font-size:10px; font-weight:bold; margin-top:5px;")
        self.selection_label = QLabel("Nothing Selected"); self.selection_label.setStyleSheet("color:#AAA; font-size:11px;"); self.selection_label.setWordWrap(True)
        sel_layout.addWidget(sel_header); sel_layout.addWidget(self.selection_label); sel_layout.addStretch()
        self.sidebar.layout().addWidget(self.selection_panel); main_layout.addWidget(self.sidebar)

        self.tabs = QTabWidget(); self.tabs.setTabsClosable(True); self.tabs.tabCloseRequested.connect(self.close_tab); main_layout.addWidget(self.tabs)
        self.shared_scene = LegoScene(); self.shared_scene.selectionChanged.connect(self.update_selection_info)

        # TAB 1: Builder
        self.builder_tab = QWidget(); b_layout = QVBoxLayout(self.builder_tab)
        b_bar = QHBoxLayout(); self.plate_w_input = QSpinBox(); self.plate_w_input.setRange(1, 100); self.plate_w_input.setValue(config.DEFAULT_PRINT_W)
        self.plate_h_input = QSpinBox(); self.plate_h_input.setRange(1, 100); self.plate_h_input.setValue(config.DEFAULT_PRINT_H)
        b_bar.addWidget(QLabel("Print Area W:")); b_bar.addWidget(self.plate_w_input); b_bar.addWidget(QLabel("H:")); b_bar.addWidget(self.plate_h_input)
        b_bar.addWidget(self.create_color_pickers(self.shared_scene, "builder")); b_bar.addStretch(); b_layout.addLayout(b_bar)
        self.builder_view = LegoView(self.shared_scene); b_layout.addWidget(self.builder_view); self.tabs.addTab(self.builder_tab, "Main Builder")

        # TAB 2: Print View
        self.print_tab = QWidget(); p_layout = QVBoxLayout(self.print_tab); self.print_view = LegoPrintView(self.shared_scene)
        p_bar = QHBoxLayout(); self.toggle_color_btn = QPushButton("Toggle Global Unicolor"); self.toggle_color_btn.setCheckable(True)
        self.override_color_btn = QPushButton(); self.override_color_btn.setFixedSize(25, 25); self.override_color_btn.setStyleSheet(f"background-color: {self.unicolor};")
        self.add_group_btn = QPushButton("+ Add Color Group"); p_bar.addWidget(self.toggle_color_btn); p_bar.addWidget(self.override_color_btn); p_bar.addWidget(self.add_group_btn)
        p_bar.addWidget(self.create_color_pickers(self.print_view, "print")); p_bar.addStretch(); p_layout.addLayout(p_bar); p_layout.addWidget(self.print_view); self.tabs.addTab(self.print_tab, "Print View")

        # TAB 3: Converter
        self.ai_tab = QWidget(); ai_layout = QVBoxLayout(self.ai_tab); self.ai_scene = LegoScene(board_size=60*config.GRID_SIZE, show_plate=False); self.ai_view = LegoConverterView(self.ai_scene)
        c_bar = QVBoxLayout(); r1 = QHBoxLayout(); r2 = QHBoxLayout()
        self.import_btn = QPushButton("📁 Import"); self.paste_btn = QPushButton("📋 Paste"); self.auto_align_btn = QPushButton("✨ Auto-Align")
        self.rot_input = QDoubleSpinBox(); self.rot_input.setRange(-180.0, 180.0); self.rot_input.setDecimals(2); self.zoom_input = QDoubleSpinBox(); self.zoom_input.setRange(1.0, 5000.0); self.zoom_input.setValue(100.0); self.zoom_input.setDecimals(2)
        r1.addWidget(self.import_btn); r1.addWidget(self.paste_btn); r1.addWidget(self.auto_align_btn); r1.addWidget(QLabel("Rot:")); r1.addWidget(self.rot_input); r1.addWidget(QLabel("Zoom:")); r1.addWidget(self.zoom_input); r1.addWidget(self.create_color_pickers(self.ai_view, "converter")); r1.addStretch()
        self.mode_selector = QComboBox(); self.mode_selector.addItems(["1x1 Only", "Compact (Greedy)", "Dreamlike (experimental)"])
        self.shape_selector = QComboBox()
        # FIXED: Populating 1x1 style options
        for w, h, col, name, sid in config.LIBRARY_DATA:
            if w == 1 and h == 1: self.shape_selector.addItem(name, sid)
        self.convert_btn = QPushButton("🚀 START CONVERSION"); self.convert_btn.setStyleSheet("background-color: #2e7d32; font-weight: bold; color: white;")
        r2.addWidget(QLabel("Mode:")); r2.addWidget(self.mode_selector); r2.addWidget(QLabel("1x1 Style:")); r2.addWidget(self.shape_selector); r2.addWidget(self.convert_btn); r2.addStretch()
        c_bar.addLayout(r1); c_bar.addLayout(r2); ai_layout.addLayout(c_bar); ai_layout.addWidget(self.ai_view)
        self.tabs.addTab(self.ai_tab, "Image Converter")

        self.res_scene = LegoScene(board_size=60*config.GRID_SIZE); self.res_view = LegoView(self.res_scene); self.tabs.addTab(self.res_view, "Converter Result")

        for i in range(4): self.tabs.tabBar().setTabButton(i, QTabBar.ButtonPosition.RightSide, None)
        self.tabs.tabBar().setTabTextColor(2, QColor("#4CAF50")); self.tabs.tabBar().setTabTextColor(3, QColor("#4CAF50"))

        # Connections
        self.tabs.currentChanged.connect(self.refresh_all_colors); self.plate_w_input.valueChanged.connect(self.update_plate_boundary); self.plate_h_input.valueChanged.connect(self.update_plate_boundary)
        self.toggle_color_btn.clicked.connect(self.refresh_all_colors); self.override_color_btn.clicked.connect(self.pick_global_unicolor); self.add_group_btn.clicked.connect(self.create_color_group)
        self.import_btn.clicked.connect(self.load_image_file); self.paste_btn.clicked.connect(self.paste_image_clip); self.auto_align_btn.clicked.connect(self.auto_align_image)
        self.rot_input.valueChanged.connect(self.update_image_transform); self.zoom_input.valueChanged.connect(self.update_image_transform); self.convert_btn.clicked.connect(self.run_logic_conversion)
        self.mode_selector.currentIndexChanged.connect(lambda i: self.shape_selector.setEnabled(i == 0))

    def create_color_pickers(self, target, context):
        w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0)
        bg = QPushButton("🎨 BG"); gr = QPushButton("🏁 Grid")
        def p_bg(): 
            c = QColorDialog.getColor()
            if c.isValid(): (target if isinstance(target, QGraphicsView) else target.views()[0]).setBackgroundBrush(QBrush(c))
        def p_gr(): 
            c = QColorDialog.getColor(); scene = target.scene() if isinstance(target, QGraphicsView) else target
            if c.isValid(): scene.grid_color = c; scene.refresh_grid()
        bg.clicked.connect(p_bg); gr.clicked.connect(p_gr); l.addWidget(bg); l.addWidget(gr); return w

    def update_plate_boundary(self): self.shared_scene.update_boundary(self.plate_w_input.value(), self.plate_h_input.value())

    def update_selection_info(self):
        idx = self.tabs.currentIndex(); scene = self.res_scene if idx == 3 else self.shared_scene
        try:
            sel = [i for i in scene.selectedItems() if isinstance(i, LegoPiece)]
            if not sel: self.selection_label.setText("Nothing Selected"); return
            counts = {}
            for i in sel: k = f"{i.w_units}x{i.h_units} {i.shape_type.capitalize()}"; counts[k] = counts.get(k, 0) + 1
            self.selection_label.setText("\n".join([f"• {c}x {n}" for n, c in counts.items()]))
        except: pass

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
            c = QColorDialog.getColor(); self.group_colors[gid] = c.name(); c_btn.setStyleSheet(f"background-color: {c.name()};"); self.refresh_all_colors()
        def assign_selection():
            for i in self.shared_scene.selectedItems():
                if isinstance(i, LegoPiece): i.color_group_id = gid
            self.refresh_all_colors()
        c_btn.clicked.connect(pick_group_color); s_btn.clicked.connect(assign_selection); d_btn.clicked.connect(delete_group); self.groups_layout.insertWidget(self.groups_layout.count() - 1, row_w)

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
        self.update_selection_info()

    def load_image_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)"); (self.set_converter_image(QPixmap(p)) if p else None)

    def paste_image_clip(self):
        cb = QApplication.clipboard().mimeData(); (self.set_converter_image(QPixmap(cb.imageData())) if cb.hasImage() else None)

    def set_converter_image(self, pix):
        if self.current_img_item: self.ai_scene.removeItem(self.current_img_item)
        self.current_img_item = QGraphicsPixmapItem(pix); self.current_img_item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable); self.current_img_item.setZValue(-200); self.ai_scene.addItem(self.current_img_item); self.ai_view.centerOn(self.current_img_item); self.rot_input.setValue(0.0); self.zoom_input.setValue(100.0); self.update_image_transform()

    def update_image_transform(self):
        if self.current_img_item:
            self.current_img_item.setTransformOriginPoint(self.current_img_item.pixmap().rect().center()); self.current_img_item.setRotation(self.rot_input.value()); self.current_img_item.setScale(self.zoom_input.value() / 100.0)

    def auto_align_image(self):
        if not self.current_img_item: return
        pix = self.current_img_item.pixmap(); buf = QBuffer(); buf.open(QIODevice.WriteOnly); pix.save(buf, "PNG"); img = Image.open(io.BytesIO(buf.data().data())).convert("L")
        bw = img.point(lambda x: 0 if x < 230 else 255, '1'); bbox = bw.getbbox()
        if bbox:
            cw = bbox[2] - bbox[0]; zf = (32 * config.GRID_SIZE / cw); self.zoom_input.setValue(zf * 100.0)
            self.current_img_item.setPos(600 - ((bbox[0]+bbox[2])/2 * zf), 600 - ((bbox[1]+bbox[3])/2 * zf))

    def run_logic_conversion(self):
        if not self.current_img_item: return
        res, grid = 60, config.GRID_SIZE; size = res * grid
        self.ai_view.show_overlay = False; self.ai_scene.grid_group.hide()
        img = QImage(size, size, QImage.Format.Format_RGB32); img.fill(Qt.GlobalColor.white); p = QPainter(img); self.ai_scene.render(p, QRectF(0,0,size,size), QRectF(0,0,size,size)); p.end()
        self.ai_view.show_overlay = True; self.ai_scene.grid_group.show()
        self.res_scene = LegoScene(board_size=size); self.res_view.setScene(self.res_scene)
        # CRITICAL FIX: Re-connect selection Changed for the new scene
        self.res_scene.selectionChanged.connect(self.update_selection_info)

        mask = [[False for _ in range(res)] for _ in range(res)]
        for y in range(res):
            for x in range(res):
                dark = 0
                for dy in [0.2, 0.4, 0.6, 0.8]:
                    for dx in [0.2, 0.4, 0.6, 0.8]:
                        if img.pixelColor(int(x*grid+grid*dx), int(y*grid+grid*dy)).lightness() < 240: dark += 1
                if dark >= 5: mask[y][x] = True
        
        m_idx = self.mode_selector.currentIndex(); ds = self.shape_selector.currentData()
        if m_idx == 0: # 1x1 only
            for y in range(res):
                for x in range(res):
                    if mask[y][x]: self.res_scene.addItem(LegoPiece(x*grid, y*grid, 1, 1, self.unicolor, ds))
        elif m_idx == 1: # Compact
            rects = sorted([p for p in config.LIBRARY_DATA if p[4] == "Rectangle"], key=lambda x: x[0]*x[1], reverse=True)
            for y in range(res):
                for x in range(res):
                    if not mask[y][x]: continue
                    placed = False
                    for rw, rh, rc, rn, rs in rects:
                        if x+rw <= res and y+rh <= res:
                            if all(mask[y+iy][x+ix] for iy in range(rh) for ix in range(rw)):
                                for iy in range(rh):
                                    for ix in range(rw): mask[y+iy][x+ix] = False
                                self.res_scene.addItem(LegoPiece(x*grid, y*grid, rw, rh, self.unicolor, "Rectangle")); placed = True; break
                    if not placed: self.res_scene.addItem(LegoPiece(x*grid, y*grid, 1, 1, self.unicolor, ds)); mask[y][x] = False
        else: # Dreamlike (Experimental)
            for y in range(res):
                for x in range(res):
                    if not mask[y][x]: continue
                    if x+1 < res and y+1 < res:
                        bl = [[mask[y+iy][x+ix] for ix in range(2)] for iy in range(2)]
                        t = sum(sum(row) for row in bl)
                        if t == 4:
                            self.res_scene.addItem(LegoPiece(x*grid, y*grid, 2, 2, self.unicolor, "Rectangle"))
                            for iy in [0,1]:
                                for ix in [0,1]: mask[y+iy][x+ix] = False
                            continue
                        if t == 3:
                            p = LegoPiece(x*grid, y*grid, 2, 2, self.unicolor, "L")
                            if not bl[0][0]: p.current_angle=270
                            elif not bl[0][1]: p.current_angle=0
                            elif not bl[1][1]: p.current_angle=90
                            else: p.current_angle=180
                            p.refresh_shape(); self.res_scene.addItem(p)
                            for iy in [0,1]:
                                for ix in [0,1]: mask[y+iy][x+ix] = False
                            continue
                    self.res_scene.addItem(LegoPiece(x*grid, y*grid, 1, 1, self.unicolor, ds)); mask[y][x] = False
        self.tabs.setCurrentIndex(3); self.res_view.centerOn(self.res_scene.plate)