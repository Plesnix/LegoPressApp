import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt
from app.ui.main_window import MainWindow

def setup_dark_theme(app):
    # 1. Force the 'Fusion' style (This removes the Windows 98 look)
    app.setStyle("Fusion")

    # 2. Define the Dark Palette
    dark_palette = QPalette()
    
    # Background and Window colors
    dark_gray = QColor(45, 45, 45)
    darker_gray = QColor(35, 35, 35)
    text_color = QColor(255, 255, 255)
    accent_color = QColor(42, 130, 218) # Modern Blue

    dark_palette.setColor(QPalette.Window, dark_gray)
    dark_palette.setColor(QPalette.WindowText, text_color)
    dark_palette.setColor(QPalette.Base, darker_gray)
    dark_palette.setColor(QPalette.AlternateBase, dark_gray)
    dark_palette.setColor(QPalette.ToolTipBase, text_color)
    dark_palette.setColor(QPalette.ToolTipText, text_color)
    dark_palette.setColor(QPalette.Text, text_color)
    dark_palette.setColor(QPalette.Button, dark_gray)
    dark_palette.setColor(QPalette.ButtonText, text_color)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, accent_color)
    dark_palette.setColor(QPalette.Highlight, accent_color)
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    # 3. Apply the palette to the entire app
    app.setPalette(dark_palette)

if __name__ == "__main__":
    # --- High DPI Scaling (Makes it look sharp on 4K monitors) ---
    import os
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    
    # Apply the sleek theme
    setup_dark_theme(app)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())