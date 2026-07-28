import sys
from src.logger import logger
from src.exception import MyException

logger.info("Hi khushal from demo.py")

try:
    a = 1 / 0
except Exception as e:
    raise MyException(e, sys)