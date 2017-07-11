from app import app_core

# Setup:

def retrieve_app_settngs_and_logger():
    ''' Locates the app data directory, reads the app settings, creates the
        logger and records the settings to the log file.
        
        Call this as the first part of the program.
    '''

    app_data_dir = app_core.find_app_data_dir()
    app_core.create_default_dirs(app_data_dir)
    
    app_settings = app_core.retrieve_app_settings(app_data_dir)
    
    logger = app_core.new_logger(app_settings)
    app_core.log_app_settings(app_settings, logger)
    
    return app_settings, logger
