"""
Информационная система учёта аудиторного фонда
Основной файл приложения
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time, timedelta, date
import csv
import io
import os
import sys
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Используем SQLite для тестирования
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///classroom.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'pool_recycle': 300,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)


# Модели базы данных
class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), nullable=False)
    floor = db.Column(db.Integer)
    building = db.Column(db.String(10))
    capacity = db.Column(db.Integer)
    area = db.Column(db.Float)
    has_projector = db.Column(db.Boolean, default=False)
    has_computers = db.Column(db.Boolean, default=False)
    has_board = db.Column(db.Boolean, default=True)
    has_air_conditioner = db.Column(db.Boolean, default=False)
    computers_count = db.Column(db.Integer, default=0)
    
    lessons = db.relationship('Lesson', backref='classroom', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Classroom {self.number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'floor': self.floor,
            'building': self.building,
            'capacity': self.capacity,
            'area': self.area,
            'has_projector': self.has_projector,
            'has_computers': self.has_computers,
            'has_board': self.has_board,
            'has_air_conditioner': self.has_air_conditioner,
            'computers_count': self.computers_count
        }


class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    lesson_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    group_name = db.Column(db.String(50))
    teacher_name = db.Column(db.String(100))
    subject_name = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Lesson {self.subject_name} {self.lesson_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'classroom_id': self.classroom_id,
            'classroom_number': self.classroom.number if self.classroom else None,
            'lesson_date': self.lesson_date.strftime('%Y-%m-%d'),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'group_name': self.group_name,
            'teacher_name': self.teacher_name,
            'subject_name': self.subject_name
        }


# Контекстный процессор для передачи функций в шаблоны
@app.context_processor
def utility_processor():
    return {
        'now': datetime.now,
        'timedelta': timedelta,
        'date': date
    }


# Главная страница
@app.route('/')
def index():
    """Главная страница с общей статистикой"""
    try:
        total_classrooms = Classroom.query.count()
        total_lessons = Lesson.query.count()
        busy_today = Lesson.query.filter(Lesson.lesson_date == datetime.now().date()).count()
        
        stats = {
            'total_classrooms': total_classrooms,
            'total_lessons': total_lessons,
            'busy_today': busy_today,
            'free_today': total_classrooms - busy_today
        }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        flash(f'Ошибка подключения к БД: {str(e)}', 'danger')
        return render_template('index.html', stats={'total_classrooms': 0, 'total_lessons': 0, 'busy_today': 0, 'free_today': 0})


# Управление аудиториями
@app.route('/classrooms')
def classrooms():
    """Список всех аудиторий"""
    try:
        classrooms_list = Classroom.query.order_by(Classroom.building, Classroom.floor, Classroom.number).all()
        return render_template('classrooms.html', classrooms=classrooms_list)
    except Exception as e:
        flash(f'Ошибка загрузки аудиторий: {str(e)}', 'danger')
        return render_template('classrooms.html', classrooms=[])


@app.route('/classrooms/add', methods=['GET', 'POST'])
def add_classroom():
    """Добавление новой аудитории"""
    if request.method == 'POST':
        try:
            # Проверка обязательных полей
            if not request.form.get('number') or not request.form.get('building'):
                flash('Заполните все обязательные поля!', 'danger')
                return redirect(url_for('add_classroom'))
            
            classroom = Classroom(
                number=request.form['number'],
                floor=int(request.form.get('floor', 1)),
                building=request.form['building'],
                capacity=int(request.form.get('capacity', 20)),
                area=float(request.form.get('area', 30.0)),
                has_projector='has_projector' in request.form,
                has_computers='has_computers' in request.form,
                has_board='has_board' in request.form,
                has_air_conditioner='has_air_conditioner' in request.form,
                computers_count=int(request.form.get('computers_count', 0))
            )
            
            db.session.add(classroom)
            db.session.commit()
            flash('Аудитория успешно добавлена!', 'success')
            return redirect(url_for('classrooms'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении: {str(e)}', 'danger')
    
    return render_template('add_classroom.html')


@app.route('/classrooms/edit/<int:id>', methods=['GET', 'POST'])
def edit_classroom(id):
    """Редактирование аудитории"""
    classroom = Classroom.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            classroom.number = request.form['number']
            classroom.floor = int(request.form['floor'])
            classroom.building = request.form['building']
            classroom.capacity = int(request.form['capacity'])
            classroom.area = float(request.form['area'])
            classroom.has_projector = 'has_projector' in request.form
            classroom.has_computers = 'has_computers' in request.form
            classroom.has_board = 'has_board' in request.form
            classroom.has_air_conditioner = 'has_air_conditioner' in request.form
            classroom.computers_count = int(request.form.get('computers_count', 0))
            
            db.session.commit()
            flash('Аудитория успешно обновлена!', 'success')
            return redirect(url_for('classrooms'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'danger')
    
    return render_template('edit_classroom.html', classroom=classroom)


@app.route('/classrooms/delete/<int:id>')
def delete_classroom(id):
    """Удаление аудитории"""
    classroom = Classroom.query.get_or_404(id)
    
    # Проверяем, есть ли занятия в этой аудитории
    if classroom.lessons:
        flash('Нельзя удалить аудиторию, в которой есть занятия!', 'warning')
        return redirect(url_for('classrooms'))
    
    try:
        db.session.delete(classroom)
        db.session.commit()
        flash('Аудитория успешно удалена!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('classrooms'))


# Расписание занятий
@app.route('/schedule')
def schedule():
    """Просмотр расписания на день"""
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.now().date()
    
    try:
        lessons = Lesson.query.filter_by(lesson_date=selected_date).order_by(Lesson.start_time).all()
        return render_template('schedule.html', lessons=lessons, selected_date=selected_date)
    except Exception as e:
        flash(f'Ошибка загрузки расписания: {str(e)}', 'danger')
        return render_template('schedule.html', lessons=[], selected_date=selected_date)


@app.route('/schedule/add', methods=['GET', 'POST'])
def add_lesson():
    """Добавление нового занятия"""
    if request.method == 'POST':
        try:
            classroom_id = int(request.form['classroom_id'])
            lesson_date = datetime.strptime(request.form['lesson_date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            
            if start_time >= end_time:
                flash('Ошибка: Время начала должно быть меньше времени окончания!', 'warning')
                return redirect(url_for('add_lesson'))
            
            # Проверка на пересечение
            conflicting = Lesson.query.filter(
                Lesson.classroom_id == classroom_id,
                Lesson.lesson_date == lesson_date,
                Lesson.start_time < end_time,
                Lesson.end_time > start_time
            ).first()
            
            if conflicting:
                flash('Это время уже занято в выбранной аудитории!', 'warning')
                return redirect(url_for('add_lesson'))
            
            lesson = Lesson(
                classroom_id=classroom_id,
                lesson_date=lesson_date,
                start_time=start_time,
                end_time=end_time,
                group_name=request.form['group_name'],
                teacher_name=request.form['teacher_name'],
                subject_name=request.form['subject_name']
            )
            
            db.session.add(lesson)
            db.session.commit()
            flash('Занятие успешно добавлено!', 'success')
            return redirect(url_for('schedule'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении: {str(e)}', 'danger')
    
    try:
        classrooms = Classroom.query.all()
    except:
        classrooms = []
    return render_template('add_lesson.html', classrooms=classrooms, today=datetime.now().date())


@app.route('/schedule/delete/<int:id>')
def delete_lesson(id):
    """Удаление занятия"""
    lesson = Lesson.query.get_or_404(id)
    return_date = lesson.lesson_date.strftime('%Y-%m-%d')
    
    try:
        db.session.delete(lesson)
        db.session.commit()
        flash('Занятие успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    
    return redirect(url_for('schedule', date=return_date))


# Поиск свободных аудиторий
@app.route('/search')
def search():
    """Страница поиска свободных аудиторий"""
    return render_template('search.html')


@app.route('/api/search-free-classrooms', methods=['POST'])
def search_free_classrooms():
    """API для поиска свободных аудиторий"""
    data = request.json
    
    try:
        search_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        min_capacity = int(data.get('min_capacity', 0))
        building = data.get('building', '')
        has_projector = data.get('has_projector', False)
        has_computers = data.get('has_computers', False)
        
        if start_time >= end_time:
            return jsonify({'error': 'Время начала должно быть меньше времени окончания'}), 400
        
        # Базовый запрос
        query = Classroom.query
        
        if min_capacity > 0:
            query = query.filter(Classroom.capacity >= min_capacity)
        
        if building:
            query = query.filter(Classroom.building == building)
        
        if has_projector:
            query = query.filter(Classroom.has_projector == True)
        
        if has_computers:
            query = query.filter(Classroom.has_computers == True)
        
        all_classrooms = query.all()
        
        # Находим занятые аудитории
        busy_classroom_ids = db.session.query(Lesson.classroom_id).filter(
            Lesson.lesson_date == search_date,
            Lesson.start_time < end_time,
            Lesson.end_time > start_time
        ).all()
        
        busy_ids = [c[0] for c in busy_classroom_ids]
        
        # Свободные аудитории
        free_classrooms = [c for c in all_classrooms if c.id not in busy_ids]
        result = [c.to_dict() for c in free_classrooms]
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Отчёты
@app.route('/reports')
def reports():
    """Страница с отчётами"""
    return render_template('reports.html')


@app.route('/api/generate-report')
def generate_report():
    """Генерация отчёта в CSV"""
    report_type = request.args.get('type', 'occupancy')
    
    try:
        # Создаем CSV файл в памяти
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        
        if report_type == 'occupancy':
            # Отчёт по загруженности
            writer.writerow(['Аудитория', 'Корпус', 'Этаж', 'Вместимость', 'Кол-во занятий', 'Загруженность (%)'])
            
            classrooms = Classroom.query.all()
            for c in classrooms:
                lessons_count = Lesson.query.filter_by(classroom_id=c.id).count()
                occupancy_rate = min(round((lessons_count / 40) * 100, 1), 100)
                
                writer.writerow([
                    c.number, c.building, c.floor, c.capacity, 
                    lessons_count, f"{occupancy_rate}%"
                ])
            
            filename = f'occupancy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif report_type == 'equipment':
            # Отчёт по оборудованию
            writer.writerow(['Аудитория', 'Корпус', 'Проектор', 'Компьютеры', 'Доска', 'Кондиционер'])
            
            classrooms = Classroom.query.all()
            for c in classrooms:
                writer.writerow([
                    c.number, c.building,
                    'Да' if c.has_projector else 'Нет',
                    f'{c.computers_count} шт.' if c.has_computers else 'Нет',
                    'Да' if c.has_board else 'Нет',
                    'Да' if c.has_air_conditioner else 'Нет'
                ])
            
            filename = f'equipment_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        else:
            return jsonify({'error': 'Неверный тип отчёта'}), 400
        
        # Подготавливаем файл для отправки
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            download_name=filename,
            as_attachment=True,
            mimetype='text/csv'
        )
        
    except Exception as e:
        flash(f'Ошибка при генерации отчёта: {str(e)}', 'danger')
        return redirect(url_for('reports'))


# API для предпросмотра
@app.route('/api/classrooms/occupancy-preview')
def occupancy_preview():
    """API для предпросмотра отчёта по загруженности"""
    try:
        classrooms = Classroom.query.all()
        result = []
        
        for c in classrooms:
            lessons_count = Lesson.query.filter_by(classroom_id=c.id).count()
            occupancy_rate = min(round((lessons_count / 40) * 100, 1), 100)
            
            result.append({
                'number': c.number,
                'building': c.building,
                'capacity': c.capacity,
                'lessons_count': lessons_count,
                'occupancy_rate': occupancy_rate
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classrooms/equipment-preview')
def equipment_preview():
    """API для предпросмотра отчёта по оборудованию"""
    try:
        classrooms = Classroom.query.all()
        result = []
        
        for c in classrooms:
            result.append({
                'number': c.number,
                'building': c.building,
                'has_projector': '✅' if c.has_projector else '❌',
                'computers_count': c.computers_count if c.has_computers else 0,
                'has_board': '✅' if c.has_board else '❌',
                'has_air_conditioner': '✅' if c.has_air_conditioner else '❌'
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Функция проверки конфликта (для тестов)
def check_conflict(classroom_id, lesson_date, start_time, end_time):
    """Проверка наличия конфликтов в расписании"""
    with app.app_context():
        conflicting = Lesson.query.filter(
            Lesson.classroom_id == classroom_id,
            Lesson.lesson_date == lesson_date,
            Lesson.start_time < end_time,
            Lesson.end_time > start_time
        ).first()
        return conflicting is not None


# Инициализация базы данных
def init_db():
    """Создание таблиц и добавление тестовых данных"""
    with app.app_context():
        try:
            # Проверяем подключение
            db.create_all()
            print("✅ Таблицы созданы")
            
            # Проверяем, есть ли данные
            if Classroom.query.count() == 0:
                print("Добавление тестовых данных...")
                
                # Тестовые аудитории
                test_classrooms = [
                    Classroom(number="101", floor=1, building="A", capacity=30, area=45.5,
                             has_projector=True, has_computers=False, has_board=True,
                             has_air_conditioner=False, computers_count=0),
                    Classroom(number="102", floor=1, building="A", capacity=25, area=40.0,
                             has_projector=False, has_computers=True, has_board=True,
                             has_air_conditioner=False, computers_count=10),
                    Classroom(number="103", floor=1, building="A", capacity=20, area=35.0,
                             has_projector=True, has_computers=True, has_board=True,
                             has_air_conditioner=False, computers_count=8),
                    Classroom(number="201", floor=2, building="A", capacity=40, area=60.0,
                             has_projector=True, has_computers=True, has_board=True,
                             has_air_conditioner=True, computers_count=15),
                    Classroom(number="202", floor=2, building="A", capacity=35, area=55.0,
                             has_projector=True, has_computers=False, has_board=True,
                             has_air_conditioner=False, computers_count=0),
                    Classroom(number="301", floor=3, building="B", capacity=50, area=70.0,
                             has_projector=True, has_computers=True, has_board=True,
                             has_air_conditioner=True, computers_count=20),
                ]
                
                db.session.add_all(test_classrooms)
                db.session.commit()
                
                # Добавляем тестовые занятия
                classrooms = Classroom.query.all()
                today = date.today()
                
                test_lessons = [
                    Lesson(classroom_id=classrooms[0].id, lesson_date=today,
                          start_time=time(9, 0), end_time=time(10, 30),
                          group_name="ИС-21", teacher_name="Иванов И.И.", subject_name="Математика"),
                    Lesson(classroom_id=classrooms[1].id, lesson_date=today,
                          start_time=time(9, 0), end_time=time(10, 30),
                          group_name="П-31", teacher_name="Петрова А.С.", subject_name="Физика"),
                    Lesson(classroom_id=classrooms[2].id, lesson_date=today,
                          start_time=time(10, 45), end_time=time(12, 15),
                          group_name="БД-22", teacher_name="Сидоров М.П.", subject_name="Базы данных"),
                    Lesson(classroom_id=classrooms[3].id, lesson_date=today + timedelta(days=1),
                          start_time=time(9, 0), end_time=time(10, 30),
                          group_name="ИС-21", teacher_name="Иванов И.И.", subject_name="Математика"),
                ]
                
                db.session.add_all(test_lessons)
                db.session.commit()
                
                print(f"✅ Добавлено {len(test_classrooms)} аудиторий и {len(test_lessons)} занятий")
            else:
                print("✅ База данных уже содержит данные")
                
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {str(e)}")
            return False
        
        return True


if __name__ == '__main__':
    print("=" * 60)
    print("ЗАПУСК ПРИЛОЖЕНИЯ")
    print("=" * 60)
    
    # Инициализация базы данных
    if init_db():
        print("\n" + "=" * 60)
        print("🚀 Сервер запущен на http://127.0.0.1:5000")
        print("=" * 60)
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        print("\n❌ Не удалось запустить приложение из-за ошибки инициализации БД")