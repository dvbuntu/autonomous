import logging
import os
from core.errors import ItemNotFound
from core.settings import Settings
from core.utils import fileutils
from core.utils import loggingutils

# Data Directory Structure:
#
#     otto_data/
#     otto_data/app_main.settings
#     otto_data/collect_auto
#     otto_data/collect_remote
#     otto_data/logs

APP_NAME = "otto"

APP_CONFIG_FILE_NAME = 'app_main.settings'
APP_DATA_PATH_ENVIRONMENT_VARIABLE = "OTTO_PATH"
DEFAULT_APP_DATA_PATH = "${HOME}/otto_data"

AUTONOMOUS_DATA_SUBDIR = "collect_auto"
REMOTE_CONTROL_DATA_SUBDIR = "collect_remote"
LOG_SUBDIR = "logs"
LOG_FILE = "app_main.log"

# Settings File Properties:

APP_CONFIG_SECTION = "AppSettings"
DEBUG_CONFIG_PROPERTY = "debug"
CONSOLE_LOG_LEVEL_PROPERTY = "log.console.level"
FILE_LOG_LEVEL_PROPERTY = "log.file.level"
SERIAL_PORT_CONFIG_PROPERTY = "serial.port"

# Default Values:

DEFAULT_DEBUG_VALUE = True
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_SERIAL_PORT_VALUE = "/dev/ttyACM0"

DEFAULT_CONFIG_FILE_LINES = [
        "# Place your settings here.",
        "",
        "[" + APP_CONFIG_SECTION + "]",
        "",
        DEBUG_CONFIG_PROPERTY + " = " + str (DEFAULT_DEBUG_VALUE),
        SERIAL_PORT_CONFIG_PROPERTY + " = " + DEFAULT_SERIAL_PORT_VALUE,
        "",
        CONSOLE_LOG_LEVEL_PROPERTY + " = " + loggingutils.level_to_string (DEFAULT_LOG_LEVEL),
        FILE_LOG_LEVEL_PROPERTY + " = " + loggingutils.level_to_string (DEFAULT_LOG_LEVEL),
        "",
        ]


class AppSettings:
    
    def __init__(self, debug = None, app_data_dir = None):

        self.debug = debug
        self.app_data_dir = app_data_dir
        
        # Derived settings:
        
        self.config_file_path = fileutils.join (self.app_data_dir, APP_CONFIG_FILE_NAME)
        
        self.autonomous_data_dir = fileutils.join (self.app_data_dir, AUTONOMOUS_DATA_SUBDIR)
        self.remote_data_dir = fileutils.join (self.app_data_dir, REMOTE_CONTROL_DATA_SUBDIR)
        self.log_dir = fileutils.join (self.app_data_dir, LOG_SUBDIR)
        self.log_file_path = fileutils.join (self.log_dir, LOG_FILE) 
        
        # Defaults
        
        self.serial_port = DEFAULT_SERIAL_PORT_VALUE
        self.log_console_level = DEFAULT_LOG_LEVEL
        self.log_file_level = DEFAULT_LOG_LEVEL

    def __repr__ (self):

        return "AppSettings [" + \
            "app_data_dir=" + (self.app_data_dir if self.app_data_dir is not None else "[None]") + \
            ", autonomous_data_dir=" + (self.autonomous_data_dir if self.autonomous_data_dir is not None else "[None]") + \
            ", remote_data_dir=" + (self.remote_data_dir if self.remote_data_dir is not None else "[None]") + \
            ", log_dir=" + (self.log_dir if self.log_dir is not None else "[None]") + \
            ", serial_port=" + (self.serial_port if self.serial_port is not None else "[None]") + \
            ", debug=" + (str(self.debug) if self.debug is not None else "[None]") + \
            "]"


def create_default_dirs (app_data_dir):
    ''' Create the default data directory structure if required.
    '''
    app_settings = new_default_app_settings(app_data_dir)

    if not fileutils.is_dir_exists(app_settings.autonomous_data_dir):
        fileutils.create_dir(app_settings.autonomous_data_dir)
    
    if not fileutils.is_dir_exists(app_settings.remote_data_dir):
        fileutils.create_dir(app_settings.remote_data_dir)
    
    if not fileutils.is_dir_exists(app_settings.log_dir):
        fileutils.create_dir(app_settings.log_dir)
        
    if not fileutils.is_file_exists(app_settings.config_file_path):
        fileutils.create_text_file(app_settings.config_file_path, DEFAULT_CONFIG_FILE_LINES)
    

def find_app_data_dir():
    ''' Finds the app_main data directory either using the environment variable or
        defaulting to the user home directory. Will use the home directory if
        none is found.
    '''
    app_data_dir = None
    
    if APP_DATA_PATH_ENVIRONMENT_VARIABLE in os.environ:
        app_data_dir = os.environ[APP_DATA_PATH_ENVIRONMENT_VARIABLE]
    
    if not app_data_dir:
        app_data_dir = os.path.expandvars(DEFAULT_APP_DATA_PATH)

    return app_data_dir


def log_app_settings (app_settings, logger):
    ''' Logs the current settings.
    '''

    logger.info ("App Settings:")
    logger.info ("Debug Mode            %s", str(app_settings.debug))
    logger.info ("Dir - Main            %s", app_settings.app_data_dir)
    logger.info ("Dir - Autonomous Data %s", app_settings.autonomous_data_dir)
    logger.info ("Dir - Remote Data     %s", app_settings.remote_data_dir)
    logger.info ("Dir - Logs            %s", app_settings.log_dir)
    logger.info ("Log - File            %s", app_settings.log_file_path)
    logger.info ("Log - Console Level   %s", loggingutils.level_to_string (app_settings.log_console_level))
    logger.info ("Log - File Level      %s", loggingutils.level_to_string (app_settings.log_file_level))
    logger.info ("Serial Port           %s", app_settings.serial_port)


def new_default_app_settings(app_data_dir):
    ''' Create app_main settings with the default app_main data directory and default
        setting values.
    '''
    return AppSettings(DEFAULT_DEBUG_VALUE, app_data_dir)


def new_logger(app_settings):
    ''' Creates a new logger that sends to the console and the file system.
        It uses the log levels in app_settings.
    '''
    
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(min (app_settings.log_console_level, app_settings.log_file_level))
    logger_format = logging.Formatter(
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt = "%Y-%m-%d %H:%M:%S"
            )
    
    if app_settings.log_console_level is not None:
        console_log_handler = logging.StreamHandler()
        console_log_handler.setLevel(app_settings.log_console_level)
        console_log_handler.setFormatter(logger_format)
        logger.addHandler(console_log_handler)

    if app_settings.log_file_level is not None:
        file_log_handler = logging.FileHandler(app_settings.log_file_path)
        file_log_handler.setLevel(app_settings.log_file_level)
        file_log_handler.setFormatter(logger_format)
        logger.addHandler(file_log_handler)
        
    if app_settings.log_console_level is None and app_settings.log_file_level is None:
        # None set. Set console to Error:
        console_log_handler = logging.StreamHandler()
        console_log_handler.setLevel(logging.ERROR)
        console_log_handler.setFormatter(logger_format)
        logger.addHandler(console_log_handler)
        
        logger.error("No log configured. Defaulting to console log, level Error.")
        print ("doh!")

    return logger

def print_app_settings (app_settings, logger):
    ''' Debugging method to be called when the logger is misbehaving.
    '''
    
    print ("App Settings:")
    print ("    Debug Mode            " + str(app_settings.debug))
    print ("    Dir - Main            " + app_settings.app_data_dir)
    print ("    Dir - Autonomous Data " + app_settings.autonomous_data_dir)
    print ("    Dir - Remote Data     " + app_settings.remote_data_dir)
    print ("    Dir - Logs            " + app_settings.log_dir)
    print ("    Log - File            " + app_settings.log_file_path)
    print ("    Log - Console Level   " + loggingutils.level_to_string (app_settings.log_console_level))
    print ("    Log - File Level      " + loggingutils.level_to_string (app_settings.log_file_level))
    print ("    Serial Port           " + app_settings.serial_port)


def retrieve_app_settings(app_data_dir):
    ''' Read in the app_main settings from the file system.
    '''
    
    app_settings_path = fileutils.join(app_data_dir, APP_CONFIG_FILE_NAME)
    
    if not fileutils.is_file_exists(app_settings_path):
        raise ItemNotFound("Settings file not found '" + app_settings_path + "'")
    
    app_settings = AppSettings (DEFAULT_DEBUG_VALUE, app_data_dir)

    settings = Settings(app_settings_path)    
    app_settings.debug = settings.get_bool(APP_CONFIG_SECTION, DEBUG_CONFIG_PROPERTY, DEFAULT_DEBUG_VALUE)
    app_settings.serial_port = settings.get_string(APP_CONFIG_SECTION, SERIAL_PORT_CONFIG_PROPERTY, DEFAULT_SERIAL_PORT_VALUE)
    app_settings.log_console_level = settings.get_log_level(APP_CONFIG_SECTION, CONSOLE_LOG_LEVEL_PROPERTY, DEFAULT_LOG_LEVEL)
    app_settings.log_file_level = settings.get_log_level(APP_CONFIG_SECTION, FILE_LOG_LEVEL_PROPERTY, DEFAULT_LOG_LEVEL)
    
    return app_settings

