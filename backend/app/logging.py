# backend/app/utils/logging.py
"""
日誌系統配置模組
提供統一的日誌記錄功能和API調用追蹤
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional
from pathlib import Path

from app.config import settings


class ColoredFormatter(logging.Formatter):
    """彩色日誌格式化器"""
    
    # 定義顏色代碼
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 綠色
        'WARNING': '\033[33m',    # 黃色
        'ERROR': '\033[31m',      # 紅色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record):
        # 原始格式化
        log_message = super().format(record)
        
        # 添加顏色（僅在終端輸出時）
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            return f"{color}{log_message}{reset}"
        
        return log_message


class JSONFormatter(logging.Formatter):
    """JSON格式日誌格式化器（適用於生產環境）"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加額外資訊
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """設定日誌系統"""
    
    # 建立日誌目錄
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 設定根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # 清除現有的處理器
    root_logger.handlers.clear()
    
    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    if settings.ENVIRONMENT == "production":
        # 生產環境使用JSON格式
        console_formatter = JSONFormatter()
    else:
        # 開發環境使用彩色格式
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 檔案處理器（輪轉日誌）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 檔案日誌使用JSON格式
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 設定特定模組的日誌級別
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    # 禁用一些嘈雜的日誌
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"日誌系統初始化完成 - 級別: {settings.LOG_LEVEL}, 檔案: {settings.LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """取得指定名稱的日誌器"""
    return logging.getLogger(name)


class APILogger:
    """API調用日誌記錄器"""
    
    def __init__(self, logger_name: str = "api"):
        self.logger = get_logger(logger_name)
    
    def log_request(self, request, response=None, execution_time=None, error=None):
        """記錄API請求"""
        log_data = {
            'method': request.method,
            'url': str(request.url),
            'client_ip': getattr(request.client, 'host', 'unknown'),
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        if response:
            log_data['status_code'] = response.status_code
        
        if execution_time:
            log_data['execution_time'] = f"{execution_time:.3f}s"
        
        if error:
            log_data['error'] = str(error)
            self.logger.error(f"API Request Failed: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.info(f"API Request: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_data_collection(self, source: str, symbol: str, success: bool, 
                          records_count: int = 0, error: str = None):
        """記錄資料收集活動"""
        log_data = {
            'source': source,
            'symbol': symbol,
            'success': success,
            'records_count': records_count,
            'timestamp': datetime.now().isoformat()
        }
        
        if error:
            log_data['error'] = error
            self.logger.error(f"Data Collection Failed: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.info(f"Data Collection: {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_task_execution(self, task_name: str, success: bool, 
                          execution_time: float = None, result: Any = None, error: str = None):
        """記錄任務執行"""
        log_data = {
            'task_name': task_name,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if execution_time:
            log_data['execution_time'] = f"{execution_time:.3f}s"
        
        if result:
            log_data['result'] = str(result)[:500]  # 限制長度
        
        if error:
            log_data['error'] = error
            self.logger.error(f"Task Failed: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            self.logger.info(f"Task Completed: {json.dumps(log_data, ensure_ascii=False)}")


# 裝飾器：API調用記錄
def log_api_call(func):
    """API調用日誌記錄裝飾器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger = get_logger(f"api.{func.__module__}.{func.__name__}")
        
        try:
            # 執行原函數
            result = await func(*args, **kwargs)
            
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 記錄成功日誌
            logger.info(f"API call successful: {func.__name__}, execution_time: {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 記錄錯誤日誌
            logger.error(f"API call failed: {func.__name__}, execution_time: {execution_time:.3f}s, error: {str(e)}")
            raise
    
    return wrapper


# 裝飾器：資料收集記錄
def log_data_collection(source: str):
    """資料收集日誌記錄裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_logger(f"data_collection.{source}")
            
            # 嘗試從參數中提取symbol
            symbol = 'unknown'
            if args:
                if hasattr(args[0], 'symbol'):
                    symbol = args[0].symbol
                elif isinstance(args[0], str):
                    symbol = args[0]
            
            try:
                # 執行原函數
                result = await func(*args, **kwargs)
                
                # 計算執行時間
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # 判斷結果
                success = result is not None
                records_count = len(result) if isinstance(result, (list, dict)) else 1 if result else 0
                
                # 記錄日誌
                logger.info(f"Data collection {source}: {symbol}, "
                          f"success: {success}, records: {records_count}, "
                          f"time: {execution_time:.3f}s")
                
                return result
                
            except Exception as e:
                # 計算執行時間
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # 記錄錯誤日誌
                logger.error(f"Data collection {source} failed: {symbol}, "
                           f"time: {execution_time:.3f}s, error: {str(e)}")
                raise
        
        return wrapper
    return decorator


# 日誌分析工具
class LogAnalyzer:
    """日誌分析工具"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or settings.LOG_FILE
    
    def get_error_summary(self, hours: int = 24) -> Dict:
        """取得錯誤摘要"""
        # 這裡可以實作日誌分析邏輯
        # 例如：統計錯誤次數、錯誤類型等
        return {
            'total_errors': 0,
            'error_types': {},
            'most_frequent_errors': []
        }
    
    def get_performance_metrics(self, hours: int = 24) -> Dict:
        """取得效能指標"""
        # 實作效能分析邏輯
        return {
            'avg_response_time': 0.0,
            'slow_requests': [],
            'request_count': 0
        }


# 建立全域日誌記錄器實例
api_logger = APILogger()

# 在模組載入時設定日誌系統
if not logging.getLogger().handlers:
    setup_logging()

# 導出主要功能
__all__ = [
    'setup_logging',
    'get_logger', 
    'APILogger',
    'api_logger',
    'log_api_call',
    'log_data_collection',
    'LogAnalyzer',
    'ColoredFormatter',
    'JSONFormatter'
]