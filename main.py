import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow, apply_dark_theme

def main():
    app = QApplication(sys.argv)
    
    # Apply professional dark theme
    apply_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
