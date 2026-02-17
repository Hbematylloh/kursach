"""
Информационная система учёта аудиторного фонда
Скрипт для инициализации базы данных PostgreSQL
Запуск: python init_db.py
"""

import sys
import os
from datetime import datetime, date, time, timedelta

# Добавляем путь к проекту для импорта конфига
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Проверяем наличие необходимых модулей
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from psycopg2 import sql
    PSYCOPG2_INSTALLED = True
except ImportError:
    PSYCOPG2_INSTALLED = False
    print("❌ Модуль psycopg2 не установлен!")
    print("   Установите его командой: pip install psycopg2-binary")
    print()

try:
    from dotenv import load_dotenv
    DOTENV_INSTALLED = True
except ImportError:
    DOTENV_INSTALLED = False
    print("⚠️  Модуль python-dotenv не установлен (будет использовать значения по умолчанию)")
    print()

# Загружаем переменные окружения, если есть dotenv
if DOTENV_INSTALLED:
    load_dotenv()

# Конфигурация по умолчанию
class Config:
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'classroom_db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-12345')


def print_step(message):
    """Вывод сообщения с форматированием"""
    print(f"\n{'='*60}")
    print(f"🔧 {message}")
    print('='*60)


def print_success(message):
    """Вывод сообщения об успехе"""
    print(f"✅ {message}")


def print_error(message):
    """Вывод сообщения об ошибке"""
    print(f"❌ {message}")


def print_warning(message):
    """Вывод предупреждения"""
    print(f"⚠️  {message}")


def create_database():
    """Создание базы данных, если она не существует"""
    if not PSYCOPG2_INSTALLED:
        print_error("Не установлен модуль psycopg2. Невозможно создать базу данных.")
        print("Попробуйте установить его командой: pip install psycopg2-binary")
        return False
    
    print_step("Проверка наличия базы данных")
    
    try:
        # Подключаемся к PostgreSQL
        conn = psycopg2.connect(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем существование базы данных
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (Config.DB_NAME,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(Config.DB_NAME)
            ))
            print_success(f"База данных '{Config.DB_NAME}' успешно создана")
        else:
            print_success(f"База данных '{Config.DB_NAME}' уже существует")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print_error(f"Ошибка подключения к PostgreSQL: {str(e)}")
        print("\nВозможные причины:")
        print("  - PostgreSQL не запущен")
        print("  - Неправильный пароль или имя пользователя")
        print("  - Неправильный хост или порт")
        print("\nПроверьте настройки в файле .env или config.py")
        return False
    except Exception as e:
        print_error(f"Ошибка при создании базы данных: {str(e)}")
        return False


def create_tables():
    """Создание таблиц в базе данных"""
    print_step("Создание таблиц")
    
    try:
        # Проверяем наличие Flask и SQLAlchemy
        try:
            from app import app, db, Classroom, Lesson
        except ImportError as e:
            print_error(f"Не удалось импортировать модули приложения: {str(e)}")
            print("Убедитесь, что файл app.py существует в текущей директории")
            return False
        
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            print_success("Таблицы успешно созданы")
            
            # Проверяем, есть ли уже данные
            if Classroom.query.count() == 0:
                print_step("Добавление тестовых данных")
                add_test_data()
            else:
                print_success("В базе уже есть данные, пропускаем добавление тестовых данных")
            
            return True
            
    except Exception as e:
        print_error(f"Ошибка при создании таблиц: {str(e)}")
        return False


def add_test_data():
    """Добавление тестовых данных"""
    try:
        from app import app, db, Classroom, Lesson
    except ImportError as e:
        print_error(f"Не удалось импортировать модули: {str(e)}")
        return
    
    with app.app_context():
        try:
            # Тестовые аудитории
            test_classrooms = [
                Classroom(
                    number="101", floor=1, building="A", capacity=30, area=45.5,
                    has_projector=True, has_computers=False, has_board=True,
                    has_air_conditioner=False, computers_count=0
                ),
                Classroom(
                    number="102", floor=1, building="A", capacity=25, area=40.0,
                    has_projector=False, has_computers=True, has_board=True,
                    has_air_conditioner=False, computers_count=10
                ),
                Classroom(
                    number="103", floor=1, building="A", capacity=20, area=35.0,
                    has_projector=True, has_computers=True, has_board=True,
                    has_air_conditioner=False, computers_count=8
                ),
                Classroom(
                    number="201", floor=2, building="A", capacity=40, area=60.0,
                    has_projector=True, has_computers=True, has_board=True,
                    has_air_conditioner=True, computers_count=15
                ),
                Classroom(
                    number="202", floor=2, building="A", capacity=35, area=55.0,
                    has_projector=True, has_computers=False, has_board=True,
                    has_air_conditioner=False, computers_count=0
                ),
                Classroom(
                    number="203", floor=2, building="A", capacity=50, area=70.0,
                    has_projector=True, has_computers=True, has_board=True,
                    has_air_conditioner=True, computers_count=20
                ),
                Classroom(
                    number="301", floor=3, building="B", capacity=30, area=48.0,
                    has_projector=True, has_computers=False, has_board=True,
                    has_air_conditioner=True, computers_count=0
                ),
                Classroom(
                    number="302", floor=3, building="B", capacity=45, area=65.0,
                    has_projector=False, has_computers=True, has_board=True,
                    has_air_conditioner=True, computers_count=12
                ),
                Classroom(
                    number="303", floor=3, building="B", capacity=60, area=85.0,
                    has_projector=True, has_computers=True, has_board=True,
                    has_air_conditioner=True, computers_count=25
                ),
                Classroom(
                    number="401", floor=4, building="B", capacity=25, area=38.0,
                    has_projector=True, has_computers=True, has_board=True,
                    has_air_conditioner=True, computers_count=10
                ),
            ]
            
            db.session.add_all(test_classrooms)
            db.session.commit()
            print_success(f"Добавлено {len(test_classrooms)} тестовых аудиторий")
            
            # Получаем ID добавленных аудиторий
            classrooms = Classroom.query.all()
            
            # Тестовые занятия
            today = date.today()
            
            test_lessons = [
                # Занятия на сегодня
                Lesson(
                    classroom_id=classrooms[0].id,
                    lesson_date=today,
                    start_time=time(9, 0),
                    end_time=time(10, 30),
                    group_name="ИС-21",
                    teacher_name="Иванов И.И.",
                    subject_name="Математика"
                ),
                Lesson(
                    classroom_id=classrooms[1].id,
                    lesson_date=today,
                    start_time=time(9, 0),
                    end_time=time(10, 30),
                    group_name="П-31",
                    teacher_name="Петрова А.С.",
                    subject_name="Физика"
                ),
                Lesson(
                    classroom_id=classrooms[2].id,
                    lesson_date=today,
                    start_time=time(10, 45),
                    end_time=time(12, 15),
                    group_name="БД-22",
                    teacher_name="Сидоров М.П.",
                    subject_name="Базы данных"
                ),
                Lesson(
                    classroom_id=classrooms[3].id,
                    lesson_date=today,
                    start_time=time(10, 45),
                    end_time=time(12, 15),
                    group_name="ИС-21",
                    teacher_name="Иванов И.И.",
                    subject_name="Математика"
                ),
                Lesson(
                    classroom_id=classrooms[4].id,
                    lesson_date=today,
                    start_time=time(13, 30),
                    end_time=time(15, 0),
                    group_name="П-31",
                    teacher_name="Петрова А.С.",
                    subject_name="Физика"
                ),
                
                # Занятия на завтра
                Lesson(
                    classroom_id=classrooms[0].id,
                    lesson_date=today + timedelta(days=1),
                    start_time=time(9, 0),
                    end_time=time(10, 30),
                    group_name="ИС-21",
                    teacher_name="Иванов И.И.",
                    subject_name="Математика"
                ),
                Lesson(
                    classroom_id=classrooms[5].id,
                    lesson_date=today + timedelta(days=1),
                    start_time=time(9, 0),
                    end_time=time(10, 30),
                    group_name="БД-22",
                    teacher_name="Сидоров М.П.",
                    subject_name="ООП"
                ),
                Lesson(
                    classroom_id=classrooms[6].id,
                    lesson_date=today + timedelta(days=1),
                    start_time=time(10, 45),
                    end_time=time(12, 15),
                    group_name="П-31",
                    teacher_name="Петрова А.С.",
                    subject_name="Физика"
                ),
                
                # Занятия на послезавтра
                Lesson(
                    classroom_id=classrooms[7].id,
                    lesson_date=today + timedelta(days=2),
                    start_time=time(9, 0),
                    end_time=time(10, 30),
                    group_name="ИС-21",
                    teacher_name="Иванов И.И.",
                    subject_name="Математика"
                ),
                Lesson(
                    classroom_id=classrooms[8].id,
                    lesson_date=today + timedelta(days=2),
                    start_time=time(10, 45),
                    end_time=time(12, 15),
                    group_name="БД-22",
                    teacher_name="Сидоров М.П.",
                    subject_name="Web-программирование"
                ),
            ]
            
            db.session.add_all(test_lessons)
            db.session.commit()
            print_success(f"Добавлено {len(test_lessons)} тестовых занятий")
            
        except Exception as e:
            db.session.rollback()
            print_error(f"Ошибка при добавлении тестовых данных: {str(e)}")
            raise e


def show_connection_info():
    """Вывод информации о подключении"""
    print_step("Параметры подключения")
    print(f"СУБД: PostgreSQL")
    print(f"Хост: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"База данных: {Config.DB_NAME}")
    print(f"Пользователь: {Config.DB_USER}")
    print(f"Пароль: {'*' * len(Config.DB_PASSWORD)}")


def main():
    """Основная функция"""
    print("\n" + "★" * 60)
    print("   ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("   Информационная система учёта аудиторного фонда")
    print("★" * 60)
    
    # Проверка наличия необходимых модулей
    if not PSYCOPG2_INSTALLED:
        print_error("Модуль psycopg2 не установлен!")
        print("\nУстановите все необходимые пакеты командой:")
        print("  pip install -r requirements.txt")
        print("\nИли установите psycopg2 отдельно:")
        print("  pip install psycopg2-binary")
        return False
    
    # Показываем информацию о подключении
    show_connection_info()
    
    # Создаем базу данных
    if not create_database():
        print_error("Не удалось создать базу данных")
        return False
    
    # Создаем таблицы и добавляем тестовые данные
    if not create_tables():
        print_error("Не удалось создать таблицы")
        return False
    
    print("\n" + "★" * 60)
    print_success("Инициализация базы данных завершена успешно!")
    print("\nДля запуска приложения выполните:")
    print("  python app.py")
    print("\nПриложение будет доступно по адресу:")
    print("  http://localhost:5000")
    print("★" * 60 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Операция прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print_error(f"Непредвиденная ошибка: {str(e)}")
        sys.exit(1)