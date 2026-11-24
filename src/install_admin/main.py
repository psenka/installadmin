import sys
import logging
from install_admin.ui.main_window import MainWindow


def setup_logging():
    """Configure logging to write to both console and logs.txt"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler("logs.txt", mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # Redirect stdout/stderr to also log
    class LogRedirect:
        def __init__(self, level):
            self.level = level
            self.buffer = ""
        
        def write(self, message):
            if message.strip():
                logger.log(self.level, message.rstrip())
            self.buffer += message
        
        def flush(self):
            pass
    
    sys.stdout = LogRedirect(logging.INFO)
    sys.stderr = LogRedirect(logging.ERROR)


def main():
    setup_logging()
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()