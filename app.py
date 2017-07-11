from app import app_core

# Setup:
app_data_dir = app_core.find_app_data_dir()
app_core.create_default_dirs(app_data_dir)

app_settings = app_core.retrieve_app_settings(app_data_dir)
# logger = app_core.new_logger(app_settings)
# app_core.log_app_settings(app_settings, logger)

