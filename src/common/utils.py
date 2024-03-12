from loguru import logger as LOGGER
import numpy as np
from datetime import datetime
from enum import Enum, auto
import os, sys
import copy

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOGGER.info(f"Project Root Path: {ROOT_PATH}")
if not os.path.exists(os.path.join(ROOT_PATH, "DEBUG LOGS")):
    os.makedirs(os.path.join(ROOT_PATH, "DEBUG LOGS"))
debugFp = f"{datetime.now().strftime("%Y%m%d_%H%M%S")}.log"
LOGGER.add(os.path.join(ROOT_PATH, "DEBUG LOGS", f"{debugFp}"), retention="1 day")