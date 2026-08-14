import os

class Config:
    """应用配置"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "pbc.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'pbc-performance-secret-2026'
    JWT_SECRET_KEY = 'pbc-performance-jwt-secret-2026'
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24 * 7  # 7天
