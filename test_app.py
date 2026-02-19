"""
Тесты для информационной системы учёта аудиторного фонда
Сокращенная версия с 5 основными тестами
"""

import pytest
from app import app, db, Classroom, Lesson
from datetime import date, time, timedelta

@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        # Добавляем тестовую аудиторию
        test_classroom = Classroom(
            number="101", floor=1, building="A", capacity=30, area=45.5,
            has_projector=True, has_computers=False, has_board=True,
            has_air_conditioner=False, computers_count=0
        )
        db.session.add(test_classroom)
        db.session.commit()
    
    with app.test_client() as client:
        yield client
    
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_index_page(client):
    """Тест 1: Главная страница загружается"""
    response = client.get('/')
    assert response.status_code == 200
    print("✓ Главная страница загружается")


def test_add_classroom(client):
    """Тест 2: Добавление новой аудитории"""
    data = {
        'number': '501',
        'floor': '5',
        'building': 'C',
        'capacity': '25',
        'area': '42.5',
        'has_projector': 'on'
    }
    response = client.post('/classrooms/add', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    with app.app_context():
        classroom = Classroom.query.filter_by(number='501').first()
        assert classroom is not None
        assert classroom.floor == 5
    print("✓ Аудитория успешно добавляется")


def test_add_lesson_conflict(client):
    """Тест 3: Проверка конфликта расписания"""
    with app.app_context():
        classroom = Classroom.query.first()
        
        # Добавляем первое занятие
        data1 = {
            'classroom_id': str(classroom.id),
            'lesson_date': date.today().isoformat(),
            'start_time': '10:00',
            'end_time': '11:30',
            'group_name': 'Группа-1',
            'teacher_name': 'Иванов',
            'subject_name': 'Тест'
        }
        response1 = client.post('/schedule/add', data=data1, follow_redirects=True)
        
        # Пытаемся добавить пересекающееся занятие
        data2 = {
            'classroom_id': str(classroom.id),
            'lesson_date': date.today().isoformat(),
            'start_time': '10:30',
            'end_time': '12:00',
            'group_name': 'Группа-2',
            'teacher_name': 'Петров',
            'subject_name': 'Тест2'
        }
        response2 = client.post('/schedule/add', data=data2, follow_redirects=True)
        
        # Проверяем, что добавилось только одно занятие
        lessons_count = Lesson.query.count()
        assert lessons_count == 1
    print("✓ Конфликты расписания правильно обрабатываются")


def test_search_free_classrooms(client):
    """Тест 4: Поиск свободных аудиторий"""
    data = {
        'date': (date.today() + timedelta(days=1)).isoformat(),
        'start_time': '09:00',
        'end_time': '10:30',
        'min_capacity': 20,
        'building': '',
        'has_projector': False,
        'has_computers': False
    }
    
    response = client.post('/api/search-free-classrooms', json=data)
    assert response.status_code == 200
    result = response.get_json()
    assert isinstance(result, list)
    print("✓ Поиск свободных аудиторий работает")


def test_generate_report(client):
    """Тест 5: Генерация отчёта"""
    response = client.get('/api/generate-report?type=occupancy')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
    print("✓ Отчёты генерируются успешно")


if __name__ == '__main__':
    pytest.main(['-v'])