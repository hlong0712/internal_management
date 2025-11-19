"""
Configuration file for Internal Management System
Tách riêng cấu hình để dễ quản lý giữa development và production
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Thư mục gốc
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Secret key - PHẢI thay đổi trong production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this-in-production'
    
    # Database & Storage
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    # SQLAlchemy Database Configuration
    # Railway PostgreSQL URL starts with postgres:// but SQLAlchemy needs postgresql://
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url or f'sqlite:///{os.path.join(DATA_DIR, "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True để debug SQL queries
    
    # Session configuration
    # Session sẽ tự động hết hạn sau PERMANENT_SESSION_LIFETIME kể từ request cuối cùng
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)  # Session timeout: 1 giờ
    SESSION_COOKIE_SECURE = False  # Set True nếu dùng HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Bảo vệ khỏi XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Bảo vệ khỏi CSRF
    SESSION_COOKIE_NAME = 'session'
    SESSION_REFRESH_EACH_REQUEST = True  # Refresh session timeout mỗi request
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size per upload (tạm thời cho import)
    MAX_STORAGE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB total storage limit
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
    
    # Application settings
    DOMAIN_NAME = os.environ.get('DOMAIN_NAME', None)
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    
    # Railway specific
    RAILWAY_ENVIRONMENT = os.environ.get('RAILWAY_ENVIRONMENT', None)
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(DATA_DIR, 'app.log')
    
    # Edit logs cleanup
    EDIT_LOGS_RETENTION_DAYS = int(os.environ.get('EDIT_LOGS_RETENTION_DAYS', 30))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production nên dùng HTTPS
    SESSION_COOKIE_SECURE = True
    
    # Tăng thời gian session trong production
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Bắt buộc phải có SECRET_KEY từ environment
    @property
    def SECRET_KEY(self):
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable must be set in production!")
        return secret_key


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Sử dụng database test riêng
    DATA_DIR = os.path.join(Config.BASE_DIR, 'data_test')


# Mapping configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """Get configuration based on environment"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
