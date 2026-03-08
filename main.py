import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow, apply_light_theme

def main():
    app = QApplication(sys.argv)
    
    # Apply professional light theme
    apply_light_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
