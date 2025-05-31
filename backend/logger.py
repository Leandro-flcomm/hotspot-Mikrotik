import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
import traceback

SYSTEM_TIMEZONE = datetime.now().astimezone().tzinfo

def get_current_datetime():
    return datetime.now().astimezone(SYSTEM_TIMEZONE)

class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        current_time = get_current_datetime()
        
        log_record = {
            'timestamp': current_time.isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'date': current_time.strftime('%Y-%m-%d'),
            'time': current_time.strftime('%H:%M:%S')
        }
        
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                          'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                          'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_record[key] = value
        
        return json.dumps(log_record)

def setup_logger(name='mikrotik_manager', log_dir='logs'):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CustomJsonFormatter())
    
    info_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'info.log'),
        when='midnight',
        interval=1,
        backupCount=7
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(CustomJsonFormatter())
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(error_handler)
    logger.addHandler(info_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

def log_with_context(level, message, task="general", **kwargs):
    try:
        kwargs['task'] = task
        
        if level == 'debug':
            logger.debug(message, extra=kwargs)
        elif level == 'info':
            logger.info(message, extra=kwargs)
        elif level == 'warning':
            logger.warning(message, extra=kwargs)
        elif level == 'error':
            logger.error(message, extra=kwargs)
        elif level == 'critical':
            logger.critical(message, extra=kwargs)
            
        for handler in logger.handlers:
            handler.flush()
    except Exception as e:
        print(f"Erro ao registrar log: {str(e)}")
