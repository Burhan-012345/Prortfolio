import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-12345'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'portfolio.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail Settings
    # Mail Settings - Optimized for Gmail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'fiscalflow.service@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'dtgo vxbp lcwi duek'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'fiscalflow.service@gmail.com'

# Add timeout settings
    MAIL_TIMEOUT = 30  # seconds
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-me-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_STRATEGY = os.environ.get('RATELIMIT_STRATEGY') or 'fixed-window'
    
    # IMPORTANT FIX — lists, not strings
    RATELIMIT_DEFAULT = [
        "200 per day",
        "50 per hour"
    ]
    
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() in ['true', '1', 't']
    
    # Feature Flags
    AI_CHAT_ENABLED = os.environ.get('AI_CHAT_ENABLED', 'True').lower() in ['true', '1', 't']
    EMAIL_NOTIFICATIONS = os.environ.get('EMAIL_NOTIFICATIONS', 'True').lower() in ['true', '1', 't']
    DEBUG_TB_ENABLED = os.environ.get('DEBUG_TB_ENABLED', 'False').lower() in ['true', '1', 't']
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ['true', '1', 't']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    RATELIMIT_STORAGE_URI = 'memory://'
    RATELIMIT_DEFAULT = [
        "500 per day",
        "100 per hour"
    ]
    
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    
    MAIL_SUPPRESS_SEND = False
    
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    SESSION_COOKIE_SECURE = True
    
    # Redis for production
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    RATELIMIT_STRATEGY = 'fixed-window'
    
    RATELIMIT_DEFAULT = [
        "200 per day",
        "50 per hour"
    ]
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = False
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    RATELIMIT_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    
    SESSION_COOKIE_SECURE = False
    
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key'


class StagingConfig(ProductionConfig):
    """Staging configuration"""
    DEBUG = True
    TESTING = False
    
    RATELIMIT_DEFAULT = [
        "500 per day",
        "100 per hour"
    ]
    
    SESSION_COOKIE_SECURE = True


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])


# Environment helpers
def is_development():
    return os.environ.get('FLASK_ENV') == 'development'

def is_production():
    return os.environ.get('FLASK_ENV') == 'production'

def is_testing():
    return os.environ.get('FLASK_ENV') == 'testing'
