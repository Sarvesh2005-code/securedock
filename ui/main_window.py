import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QLineEdit, QTextEdit, QSplitter, QDateEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QColor, QPalette, QFont

from core.hasher import generate_file_hash, create_custody_log
from core.db_parser import auto_detect_and_parse
from core.carver import carve_deleted_messages
from core.analyzer import sort_by_timestamp, deduplicate_messages, filter_by_keyword
from core.reporter import export_to_csv, export_forensic_report_pdf

def apply_dark_theme(app):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(40, 44, 52))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(215, 218, 224))
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 33, 39))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 44, 52))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(215, 218, 224))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(40, 44, 52))
    palette.setColor(QPalette.ColorRole.Text, QColor(215, 218, 224))
    palette.setColor(QPalette.ColorRole.Button, QColor(50, 56, 66))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(215, 218, 224))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(97, 175, 239))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(97, 175, 239))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(40, 44, 52))
    app.setPalette(palette)
    
    app.setStyleSheet("""
        QToolTip { color: #ffffff; background-color: #282c34; border: 1px solid white; }
        QPushButton { border: 1px solid #3b4048; border-radius: 4px; padding: 6px; background-color: #3b4048; font-weight: bold;}
        QPushButton:hover { background-color: #4b5263; }
        QLineEdit, QDateEdit, QTextEdit { border: 1px solid #4b5263; border-radius: 4px; padding: 4px; background-color: #1e2227; color: #abb2bf;}
        QTableWidget { gridline-color: #3b4048; border: 1px solid #4b5263; }
        QHeaderView::section { background-color: #282c34; border: 1px solid #3b4048; padding: 4px; font-weight: bold; color: #abb2bf;}
        QTableWidget::item:selected { background-color: #3e4451; }
    """)

class RecoveryWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(list, str) # returns messages list, file_hash
    error = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            self.log.emit("Computing forensic SHA-256 hash...")
            file_hash = generate_file_hash(self.filepath)
            self.progress.emit(10)
            
            # Optionally create a custody log in the same dir
            log_path = self.filepath + "_custody.txt"
            create_custody_log(self.filepath, log_path)
            self.log.emit(f"Chain of custody log created at: {log_path}")
            
            self.log.emit("Parsing active/allocated database records...")
            active_messages = auto_detect_and_parse(self.filepath)
            self.progress.emit(40)
            
            self.log.emit(f"Extracted {len(active_messages)} allocated records. Carving for deleted artifacts...")
            # For a massive DB, carving can be slow. Simulated progress.
            self.progress.emit(60)
            deleted_messages = carve_deleted_messages(self.filepath, active_messages)
            
            self.progress.emit(85)
            self.log.emit(f"Carved {len(deleted_messages)} orphaned/deleted fragments. Finalizing results...")
            
            all_messages = active_messages + deleted_messages
            # Deduplicate just in case 
            all_messages = deduplicate_messages(all_messages)
            # Sort chronologically
            all_messages = sort_by_timestamp(all_messages)
            
            self.progress.emit(100)
            self.log.emit("Analysis Complete.")
            self.finished.emit(all_messages, file_hash)
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecureDock - Forensic Mobile Chat Recovery")
        self.resize(1100, 750)
        
        # State
        self.current_filepath = None
        self.evidence_hash = None
        self.all_messages = []
        self.filtered_messages = []
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header Area
        header_layout = QHBoxLayout()
        self.lbl_file = QLabel("No Evidence Loaded")
        font = self.lbl_file.font()
        font.setPointSize(11)
        font.setBold(True)
        self.lbl_file.setFont(font)
        
        btn_load = QPushButton("Load Database File")
        btn_load.setMinimumHeight(35)
        btn_load.clicked.connect(self.load_file)
        
        header_layout.addWidget(btn_load)
        header_layout.addWidget(self.lbl_file, stretch=1)
        main_layout.addLayout(header_layout)
        
        # Stats Area
        stats_layout = QHBoxLayout()
        self.lbl_stats_total = QLabel("Total: 0")
        self.lbl_stats_active = QLabel("Active: 0")
        self.lbl_stats_deleted = QLabel("Deleted (Carved): 0")
        
        # Styling stats labels slightly larger and distinct
        stat_style = "background-color: #282c34; padding: 6px; border-radius: 4px; border: 1px solid #3b4048;"
        self.lbl_stats_total.setStyleSheet(stat_style + " color: #abb2bf;")
        self.lbl_stats_active.setStyleSheet(stat_style + " color: #98c379; font-weight: bold;")
        self.lbl_stats_deleted.setStyleSheet(stat_style + " color: #e06c75; font-weight: bold;") 
        
        stats_layout.addWidget(self.lbl_stats_total)
        stats_layout.addWidget(self.lbl_stats_active)
        stats_layout.addWidget(self.lbl_stats_deleted)
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)
        
        # Controls Area (Filters)
        controls_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter by keyword...")
        self.search_box.textChanged.connect(self.apply_filter)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate(2000, 1, 1))
        self.date_from.dateChanged.connect(self.apply_filter)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addDays(1))
        self.date_to.dateChanged.connect(self.apply_filter)
        
        btn_export_csv = QPushButton("Export CSV  ")
        btn_export_csv.clicked.connect(self.export_csv)
        
        btn_export_pdf = QPushButton("Forensic PDF  ")
        btn_export_pdf.clicked.connect(self.export_pdf)
        
        controls_layout.addWidget(QLabel("Search:"))
        controls_layout.addWidget(self.search_box, stretch=1)
        controls_layout.addWidget(QLabel("From:"))
        controls_layout.addWidget(self.date_from)
        controls_layout.addWidget(QLabel("To:"))
        controls_layout.addWidget(self.date_to)
        controls_layout.addWidget(btn_export_csv)
        controls_layout.addWidget(btn_export_pdf)
        main_layout.addLayout(controls_layout)
        
        # Splitter to hold Table and Details Pane
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Timestamp (UTC)", "Sender", "Receiver", "Message Body", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        splitter.addWidget(self.table)
        
        # Details Pane
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 5, 0, 0)
        lbl_details = QLabel("Message Details / Hex Viewer")
        lbl_details.setStyleSheet("font-weight: bold; color: #61afef;")
        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setStyleSheet("background-color: #1e2227; color: #abb2bf; font-family: Consolas, monospace;")
        details_layout.addWidget(lbl_details)
        details_layout.addWidget(self.txt_details)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([500, 150])
        main_layout.addWidget(splitter, stretch=1)
        
        # Footer
        footer_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(15)
        self.lbl_status = QLabel("Ready.")
        
        footer_layout.addWidget(self.progress_bar)
        footer_layout.addWidget(self.lbl_status, stretch=1)
        main_layout.addLayout(footer_layout)
        
    def load_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select DB File", "", "Database Files (*.db);;All Files (*)")
        if filepath:
            self.current_filepath = filepath
            self.lbl_file.setText(f"Loaded: {os.path.basename(filepath)}")
            self.progress_bar.setValue(0)
            self.table.setRowCount(0)
            self.txt_details.clear()
            self.all_messages.clear()
            self.filtered_messages.clear()
            self.evidence_hash = None
            
            # Start Background Thread
            self.worker = RecoveryWorker(filepath)
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.log.connect(self.lbl_status.setText)
            self.worker.finished.connect(self.on_analysis_finished)
            self.worker.error.connect(self.on_analysis_error)
            self.worker.start()
            
    def on_analysis_finished(self, messages, file_hash):
        self.all_messages = messages
        self.filtered_messages = messages
        self.evidence_hash = file_hash
        
        # Update Stats
        total = len(messages)
        deleted = sum(1 for m in messages if m.is_deleted)
        active = total - deleted
        self.lbl_stats_total.setText(f"Total Records: {total}")
        self.lbl_stats_active.setText(f"Allocated (Active): {active}")
        self.lbl_stats_deleted.setText(f"Carved (Deleted): {deleted}")
        
        self.apply_filter()
        QMessageBox.information(self, "Analysis Complete", f"Successfully analyzed {len(messages)} records.\nEvidence Hash: {file_hash}")
        
    def on_analysis_error(self, err_msg):
        self.lbl_status.setText("Error during analysis.")
        QMessageBox.critical(self, "Error", f"An error occurred:\n{err_msg}")
        self.progress_bar.setValue(0)
        
    def apply_filter(self, *args, **kwargs):
        if not self.all_messages:
            return
            
        text = self.search_box.text().strip().lower()
        from_date = self.date_from.date().toPyDate()
        to_date = self.date_to.date().toPyDate()
        
        filtered = []
        for msg in self.all_messages:
            # Date check
            msg_date = msg.timestamp.date() if msg.timestamp else None
            # If there's no timestamp, we usually put it to max, but let's just include it or check bounds
            if msg_date:
                if msg_date < from_date or msg_date > to_date:
                    continue
            
            # Text check
            if text:
                body_lower = (msg.body or "").lower()
                if text not in body_lower:
                    continue
                    
            filtered.append(msg)
            
        self.filtered_messages = filtered
        self.update_table(self.filtered_messages)
            
    def update_table(self, messages_to_show):
        self.table.setRowCount(len(messages_to_show))
        for row, msg in enumerate(messages_to_show):
            time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else "Unknown"
            status_str = "Deleted (Carved)" if msg.is_deleted else "Active"
            
            item_time = QTableWidgetItem(time_str)
            item_sender = QTableWidgetItem(msg.sender)
            item_receiver = QTableWidgetItem(msg.receiver)
            item_body = QTableWidgetItem(msg.body)
            item_status = QTableWidgetItem(status_str)
            
            # Store full message in item data for easy retrieval
            item_body.setData(Qt.ItemDataRole.UserRole, msg)
            
            # Highlight deleted messages
            if msg.is_deleted:
                item_status.setForeground(QColor("#e06c75"))
                item_time.setForeground(QColor("#e06c75"))
                item_sender.setForeground(QColor("#e06c75"))
                item_receiver.setForeground(QColor("#e06c75"))
                # slightly darker for body so it isn't overwhelming red
                item_body.setForeground(QColor("#d25d5d")) 
                
            # Make table read-only
            for item in (item_time, item_sender, item_receiver, item_body, item_status):
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(row, 0, item_time)
            self.table.setItem(row, 1, item_sender)
            self.table.setItem(row, 2, item_receiver)
            self.table.setItem(row, 3, item_body)
            self.table.setItem(row, 4, item_status)

    def on_table_selection_changed(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.txt_details.clear()
            return
            
        # Get the row of the first selected item
        row = selected_items[0].row()
        # The 4th column (index 3) is the body, which contains our user_data object
        item_body = self.table.item(row, 3)
        if item_body is None:
            return
        
        msg = item_body.data(Qt.ItemDataRole.UserRole)
        
        if msg:
            time_str = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if msg.timestamp else "Unknown"
            details = (
                f"Status      : {'Deleted (Carved)' if msg.is_deleted else 'Active'}\n"
                f"Service     : {msg.service}\n"
                f"Timestamp   : {time_str}\n"
                f"Sender      : {msg.sender}\n"
                f"Receiver    : {msg.receiver}\n"
                f"Source File : {msg.source_file}\n"
                f"{'-'*60}\n"
                f"{msg.body}\n"
            )
            self.txt_details.setPlainText(details)

    def export_csv(self):
        if not self.filtered_messages:
            QMessageBox.warning(self, "No Data", "No messages to export.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(self, "Save CSV Report", "SecureDock_Export.csv", "CSV Files (*.csv)")
        if filepath:
            try:
                export_to_csv(self.filtered_messages, filepath)
                QMessageBox.information(self, "Export Complete", f"CSV Exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_pdf(self):
        if not self.filtered_messages or not self.evidence_hash:
            QMessageBox.warning(self, "No Data", "No messages to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "SecureDock_Report.pdf", "PDF Files (*.pdf)")
        if filepath:
            try:
                case_id = "CASE-" + datetime.now().strftime("%Y%m%d")
                investigator_name = "SecureDock Analyst"
                
                export_forensic_report_pdf(
                    case_id=case_id,
                    investigator_name=investigator_name,
                    evidence_hash=self.evidence_hash,
                    filepath=self.current_filepath,
                    messages=self.filtered_messages, # export filtered
                    output_path=filepath
                )
                QMessageBox.information(self, "Export Complete", f"Forensic PDF Exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
