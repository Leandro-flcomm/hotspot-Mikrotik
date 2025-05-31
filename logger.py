import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
import traceback
import time

# Configuração de timezone
# Usar o timezone local do sistema em vez de UTC
SYSTEM_TIMEZONE = datetime.now().astimezone().tzinfo

def get_current_datetime():
    """Retorna o datetime atual no timezone do sistema"""
    # Usar datetime.now().astimezone() para garantir que a data seja a atual do sistema
    # com o timezone local
    return datetime.now().astimezone(SYSTEM_TIMEZONE)

def convert_to_system_timezone(dt):
    """Converte um datetime para o timezone do sistema"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SYSTEM_TIMEZONE)

# Configuração do logger
class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        # Garantir que o timestamp seja no formato ISO 8601 com timezone
        current_time = get_current_datetime()
        
        log_record = {
            'timestamp': current_time.isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            # Adicionar data e hora separadamente para facilitar filtragem
            'date': current_time.strftime('%Y-%m-%d'),
            'time': current_time.strftime('%H:%M:%S')
        }
        
        # Adicionar exceção se existir
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        
        # Adicionar atributos extras
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                          'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                          'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                          'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_record[key] = value
        
        return json.dumps(log_record)

def setup_logger(name='mikrotik_manager', log_dir='logs'):
    # Criar diretório de logs se não existir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Handler para logs de erro (rotativo por tamanho)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CustomJsonFormatter())
    
    # Handler para logs de informação (rotativo por tempo - diário)
    info_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'info.log'),
        when='midnight',
        interval=1,
        backupCount=7
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(CustomJsonFormatter())
    
    # Handler para logs de depuração (rotativo por tempo - diário)
    debug_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'debug.log'),
        when='midnight',
        interval=1,
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(CustomJsonFormatter())
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(error_handler)
    logger.addHandler(info_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)
    
    # Criar logs iniciais para garantir que os arquivos existam
    logger.debug("Logger inicializado - debug")
    logger.info("Logger inicializado - info")
    logger.error("Logger inicializado - error")
    
    return logger

# Criar logger global
logger = setup_logger()

# Função para adicionar contexto ao log
def log_with_context(level, message, task="general", **kwargs):
    try:
        # Adicionar a tarefa aos kwargs
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
            
        # Garantir que o log seja escrito imediatamente
        for handler in logger.handlers:
            handler.flush()
    except Exception as e:
        print(f"Erro ao registrar log: {str(e)}")
        print(traceback.format_exc())
