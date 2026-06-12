import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Base configuration class for LearnTrack."""
    # Flask application secret key for session signing
    SECRET_KEY = os.environ.get('SECRET_KEY', 'learntrack-dev-secret-key-18239')
    
    # Debug mode setting
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'mysqlroot@123')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'learntrack_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    
    # Parse connection URL if available (common on Heroku, Railway, Render)
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or os.environ.get('JAWSDB_URL') or os.environ.get('CLEARDB_DATABASE_URL')
    if db_url and db_url.startswith('mysql'):
        try:
            from urllib.parse import urlparse, unquote
            # Clean mysql+pymysql prefix if present
            clean_url = db_url
            if clean_url.startswith('mysql+pymysql://'):
                clean_url = clean_url.replace('mysql+pymysql://', 'mysql://')
                
            url = urlparse(clean_url)
            MYSQL_HOST = url.hostname or MYSQL_HOST
            MYSQL_USER = unquote(url.username) if url.username else MYSQL_USER
            MYSQL_PASSWORD = unquote(url.password) if url.password else MYSQL_PASSWORD
            MYSQL_DB = url.path.lstrip('/') or MYSQL_DB
            if url.port:
                MYSQL_PORT = int(url.port)
        except Exception as parse_err:
            print(f"Error parsing database URL: {parse_err}")
    
    # Set cursor class to DictCursor to access query results by column names
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Establish connection with UTF-8 Multibyte charset to support emojis
    MYSQL_CHARSET = 'utf8mb4'

    
    # File Upload Settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads'
    ))
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB maximum file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
