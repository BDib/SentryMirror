import sys
import asyncio
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, 
                               QPushButton, QSpinBox, QDoubleSpinBox, QTextEdit, QLabel, QFormLayout)
from PySide6.QtCore import QThread, Signal, Slot
from sentry_mirror.crawler import Crawler
from sentry_mirror.config import settings
from sentry_mirror.logger import logger
from sentry_mirror.gui_utils import QtHandler

class CrawlerWorker(QThread):
    log_signal = Signal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        # Update settings dynamically
        settings.max_depth = self.params['depth']
        settings.delay_between_requests = self.params['delay']
        
        asyncio.run(self.execute_crawl(self.params['url']))

    async def execute_crawl(self, url):
        self.log_signal.emit(f"🚀 Initializing crawl: {url}")
        crawler = Crawler(url)
        await crawler.crawl(url)
        self.log_signal.emit(f"✅ Crawl complete. Total pages: {len(crawler.visited)}")

class SentryMirrorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SentryMirror Professional UI")
        self.setup_ui()
        
        # Connect logger to UI
        handler = QtHandler(self.worker_signal)
        logger.addHandler(handler)
        logger.setLevel("INFO")

    worker_signal = Signal(str)

    def setup_ui(self):
        layout = QFormLayout(self)

        self.url_edit = QLineEdit()
        layout.addRow("Target URL:", self.url_edit)
        
        # Output Folder Picker
        self.output_edit = QLineEdit("./my_offline_site")
        output_btn = QPushButton("Browse")
        output_btn.clicked.connect(self.browse_output)
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_btn)
        layout.addRow("Output Folder:", output_layout)
        
        # Database File Picker
        self.db_edit = QLineEdit("./my_database.db")
        db_btn = QPushButton("Browse")
        db_btn.clicked.connect(self.browse_db)
        db_layout = QHBoxLayout()
        db_layout.addWidget(self.db_edit)
        db_layout.addWidget(db_btn)
        layout.addRow("Database File:", db_layout)

        self.depth_spin = QSpinBox(minimum=1, maximum=10, value=settings.max_depth)
        layout.addRow("Crawl Depth:", self.depth_spin)

        self.delay_spin = QDoubleSpinBox(minimum=0.1, maximum=5.0, value=settings.delay_between_requests)
        layout.addRow("Delay (s):", self.delay_spin)

        self.btn = QPushButton("Start Analysis")
        self.btn.clicked.connect(self.start_analysis)
        layout.addRow(self.btn)

        self.log_output = QTextEdit(readOnly=True)
        layout.addRow("Process Logs:", self.log_output)
        
        self.worker_signal.connect(self.log_output.append)
        
    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder: self.output_edit.setText(folder)

    def browse_db(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Database File", filter="SQLite DB (*.db)")
        if file_path: self.db_edit.setText(file_path)

    def start_analysis(self):
        params = {
            'url': self.url_edit.text(),
            'depth': self.depth_spin.value(),
            'delay': self.delay_spin.value()
        }
        self.worker = CrawlerWorker(params)
        self.worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SentryMirrorGUI()
    window.show()
    sys.exit(app.exec())