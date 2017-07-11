import configparser
from core.utils import boolutils
from core.utils import loggingutils

class Settings:
    ''' Encapsulates access to Pythons ConfigParser class.
        It provides more robust methods for accessing data items.
    '''
    
    def __init__(self, settings_file_path):
        self._config_parser = configparser.ConfigParser();
        self._config_parser.read(settings_file_path)
    
    def get_bool(self, section_name, property_name, default_value = False):
        value = self.get_string(section_name, property_name)
        if value != None:
            return boolutils.from_string(value)
        else:
            return default_value
        
    def get_log_level(self, section_name, property_name, default_value):
        value = self.get_string(section_name, property_name)
        if value != None:
            return loggingutils.level_from_string(value)
        else:
            return default_value
        
    def get_string(self, section_name, property_name, default_value = None):
        if self.has_property(section_name, property_name):
            return self._config_parser[section_name][property_name]
        else:
            return default_value
        
    def has_property(self, section_name, property_name):
        return self.has_section(section_name) and property_name in self._config_parser[section_name]

    def has_section(self, section_name):
        return section_name in self._config_parser

