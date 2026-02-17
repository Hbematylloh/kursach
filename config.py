"""
Конфигурационный файл приложения
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Настройки PostgreSQL
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'classroom_db')
    
    # Формируем URI для подключения к БД
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Секретный ключ для сессий
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Дополнительные настройки
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'