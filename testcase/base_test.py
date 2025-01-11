import os
import json
import logging
import logging.config
from datetime import datetime


class BaseTest:
    @classmethod
    def setup_class(cls):
        """Set up test class - called before any tests are run."""
        cls._setup_logging()

    @classmethod
    def _setup_logging(cls):
        """Configure logging system."""
        # 取得專案根目錄
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 確保 logs 目錄存在
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 生成日誌檔案名稱
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = os.path.join(log_dir, f"test_execution_{timestamp}.log")

        # 基本日誌配置（如果找不到配置檔案時使用）
        basic_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": log_filename,
                    "mode": "a"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": True
                }
            }
        }
        try:
            # 嘗試讀取配置檔案
            config_path = os.path.join(project_root, "config", "log_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # 更新日誌檔案路徑
                    config['handlers']['file']['filename'] = log_filename
            else:
                config = basic_config
                
            # 應用日誌配置
            logging.config.dictConfig(config)
            
            # 建立測試開始的標記
            root_logger = logging.getLogger()
            root_logger.info("=" * 80)
            root_logger.info(f"Test session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            root_logger.info("=" * 80)
        except Exception as e:
            # 如果配置失敗，使用基本配置
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
                handlers=[
                    logging.FileHandler(log_filename),
                    logging.StreamHandler()
                ]
            )
            logging.warning(f"Could not load logging config: {str(e)}. Using basic configuration.")

        # 設定類別的 logger
        cls.logger = logging.getLogger(cls.__name__)
        cls.logger.info(f"Logger initialized for {cls.__name__}")

    def run_command(self, command):
        """Run a shell command and return its output."""
        self.logger.debug(f"Executing command: {command}")
        try:
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.debug(f"Command output: {result.stdout}")
                return result.stdout
            else:
                self.logger.error(f"Command failed with error: {result.stderr}")
                return None
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
            return None
