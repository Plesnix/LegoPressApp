# app/config.py
GRID_SIZE = 20
BOARD_SIZE_STUDS = 100
BOARD_SIZE_PX = BOARD_SIZE_STUDS * GRID_SIZE

# Default Print Area (The bold outline)
DEFAULT_PRINT_W = 32
DEFAULT_PRINT_H = 32

PLATE_COLOR = "#FFFFFF"
GRID_LINE_COLOR = "#F50000"
VOID_COLOR = "#121212"

# PHYSICAL INVENTORY
LIBRARY_DATA = [
    (4, 4, "#FFD700", "4x4 Circle", "round"),
    (4, 4, "#4FB0C6", "4x4 Macaroni", "macaroni"),
    (2, 2, "#A0A0A0", "2x2 Tile", "Rectangle"),
    (2, 2, "#FFD700", "2x2 Circle", "round"),
    (2, 2, "#4FB0C6", "2x2 Macaroni", "macaroni"),
    (2, 2, "#E63946", "2x2 Corner", "L"),
    (2, 2, "#E63946", "2x2 Triangle", "triangle"),
    (1, 6, "#A0A0A0", "1x6 Tile", "Rectangle"),
    (1, 4, "#A0A0A0", "1x4 Tile", "Rectangle"),
    (1, 3, "#A0A0A0", "1x3 Tile", "Rectangle"),
    (2, 1, "#FFD700", "1x2 Half Circle", "1748"),
    (2, 1, "#A0A0A0", "1x2 Wedge Tile", "5092"),
    (1, 2, "#A0A0A0", "1x2 Tile", "Rectangle"),
    (1, 1, "#A0A0A0", "1x1 Tile", "Rectangle"),
    (1, 1, "#FFD700", "1x1 Circle", "round"),
    (1, 1, "#4FB0C6", "1x1 Half Round", "24246"),
    (1, 1, "#4FB0C6", "1x1 Quarter", "macaroni"),
    (1, 1, "#EC34CE", "1x1 Heart", "heart"),
]