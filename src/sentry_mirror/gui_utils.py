import logging
from PySide6.QtCore import Signal, QObject

class QtHandler(logging.Handler):
    def __init__(self, signal: Signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        log_entry = self.format(record)
        self.signal.emit(log_entry)