import logging
from core.utils import strutils


LOG_LEVEL_DICT = {
        logging.CRITICAL: "critical",
        logging.DEBUG: "debug",
        logging.ERROR: "error",
        logging.INFO: "info",
        logging.WARNING: "warning",
        }

LOG_LEVEL_LOOKUP_DICT = {
        "none": None,
        "critical": logging.CRITICAL,
        "debug": logging.DEBUG,
        "error": logging.ERROR,
        "info": logging.INFO,
        "warning": logging.WARNING
        }


def level_from_string(string_value):

    log_level = None
    
    if strutils.is_not_blank(string_value):
        if string_value.lower() in LOG_LEVEL_LOOKUP_DICT:
            log_level = LOG_LEVEL_LOOKUP_DICT[string_value.lower()]
        
    return log_level


def level_to_string(log_level):
    if log_level is None:
        return "none"
    else:
        return LOG_LEVEL_DICT[log_level]

