# team/images/config.py
import os

class Config:
    VERSION = 0.22
    DEFAULT_DPI = 96
    MIN_DPI = 72
    STR_SEPARATOR = "; "
    LIST_SEPARATOR = "|"
    CSV_SEPARATOR = ","
    EXIF_TAG_SEPARATOR = "|"
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
    FILE_UPLOAD_ENDPOINT = 'api/product/attachment/'
    UPLOAD_FILES = True
    IMAGE_CURRENT_ERROR_FOLDER = None
    PROCESS_TEMPLATES = True
    CORRELATION_TRESHOLD = 0.330 #no logo recognized below this level
    TEMPLATES = ['template_kalorik_h95_vertical.jpg', 'template_kalorik_w95_horizontal.jpg',
                'template_efbe_h95_vertical.jpg', 'template_efbe_w95_horizontal.jpg',
                'template_kitchen_h165_vertical.jpg', 'template_kitchen_w165_horizontal.jpg']
    VISUALIZE = False

    FILENAME_FILTER = '' #will process only files containing this string - case sensitive
    CREATE_THUMBNAILS = True
    THUMBNAIL_HEIGHT = 96
    THUMBNAIL_FORMAT = 'PNG'

    SQL_CONNECTION_STRING_TEMPLATE = 'Driver=%SQL_DRIVER%;Server=%SQL_SERVER%;Database=%SQL_DATABASE%;Uid=%SQL_LOGIN%;Pwd=%SQL_PASSWORD%;'
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root  
    IMAGE_TEMPLATE_FOLDER = os.path.join(ROOT_DIR, 'templates')       

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    API_USERNAME = 'a@pi.com'
    API_PWD = 'api123'
    APP_URL = 'http://127.0.0.1:5000/'
    TEAM_SERVER = 'localhost'
    TEAM_DATABASE = 'TeamExport'
    TEAM_USER = 'teampolska'
    TEAM_PWD = 'teampolska'
    LOG_LOCATION = 'C:\Project\TeamAssets\deploy\Logs'
    PARENT_FOLDER = 'C:\Project\TeamAssets\deploy\Pictures' 
    IMAGE_UNPROCESSED_FOLDER = os.path.join(PARENT_FOLDER, 'unprocessed')
    IMAGE_PROCESSED_FOLDER = os.path.join(PARENT_FOLDER, 'processed')
    IMAGE_ERROR_FOLDER = os.path.join(PARENT_FOLDER, 'errors')
    IMAGE_THUMBNAIL_FOLDER = os.path.join(PARENT_FOLDER, 'thumbnails')
    IMAGE_LOG_FOLDER = os.path.join(PARENT_FOLDER, 'logs')

class TestConfig(Config):
    """Development slawek configuration."""
    DEBUG = True
    API_USERNAME = 'a@pi.com'
    API_PWD = 'api123'
    APP_URL = 'http://127.0.0.1:5000/'
    TEAM_SERVER = 'localhost\MSSQLSERVER01'
    TEAM_DATABASE = 'TeamExport'
    TEAM_USER = 'teampolska'
    TEAM_PWD = 'teampolska'
    LOG_LOCATION = 'C:\Project\TeamAssets\deploy\Logs'
    PARENT_FOLDER = 'C:\Project\TeamAssets\deploy\Pictures'       
    IMAGE_UNPROCESSED_FOLDER = os.path.join(PARENT_FOLDER, 'unprocessed')
    IMAGE_PROCESSED_FOLDER = os.path.join(PARENT_FOLDER, 'processed')
    IMAGE_ERROR_FOLDER = os.path.join(PARENT_FOLDER, 'errors')
    IMAGE_THUMBNAIL_FOLDER = os.path.join(PARENT_FOLDER, 'thumbnails')
    IMAGE_LOG_FOLDER = os.path.join(PARENT_FOLDER, 'logs')     

class ProductionConfig(Config):
    """Development slawek configuration."""
    DEBUG = False
    API_USERNAME = os.getenv('APP_SETTINGS_API_USERNAME')
    API_PWD = os.getenv('APP_SETTINGS_API_PWD')
    APP_URL = os.getenv('APP_SETTINGS_URL')
    TEAM_SERVER = os.getenv('APP_SETTINGS_TEAM_SERVER')
    TEAM_DATABASE = os.getenv('APP_SETTINGS_TEAM_DATABASE')
    TEAM_USER = os.getenv('APP_SETTINGS_TEAM_USER')
    TEAM_PWD = os.getenv('APP_SETTINGS_TEAM_PWD')
    LOG_LOCATION = os.getenv('APP_SETTINGS_LOG_LOCATION')
    PARENT_FOLDER = 'C:\Project\TeamAssets\deploy\Pictures'       
    IMAGE_UNPROCESSED_FOLDER = os.path.join(PARENT_FOLDER, 'unprocessed')
    IMAGE_PROCESSED_FOLDER = os.path.join(PARENT_FOLDER, 'processed')
    IMAGE_ERROR_FOLDER = os.path.join(PARENT_FOLDER, 'errors')
    IMAGE_THUMBNAIL_FOLDER = os.path.join(PARENT_FOLDER, 'thumbnails')
    IMAGE_LOG_FOLDER = os.path.join(PARENT_FOLDER, 'logs')    
    

