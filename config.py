import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'learntrack-dev-secret-key-18239')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

    # MySQL Configuration (individual vars only — no DATABASE_URL parsing)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'learntrack-abimani27112003-3e8c.j.aivencloud.com')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'avnadmin')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'AVNS_1XEbzIhtrDRF0MrIsq3')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'defaultdb')
    MYSQL_PORT = 23879
    MYSQL_CURSORCLASS = 'DictCursor'
    MYSQL_CHARSET = 'utf8mb4'
    MYSQL_SSL_MODE = 'required'

    # SSL for Aiven (always required)
    MYSQL_CUSTOM_OPTIONS = {"ssl": {"mode": "required"}}

    # File Upload Settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads'
    ))
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}