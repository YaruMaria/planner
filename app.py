from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# Палитра оттенков зелёного
palette = {
    "Pale Jade": "#e8efe2",
    "Soft Matcha": "#c6d3a0",
    "Olive Matcha": "#94ad6e",
    "Roasted Green": "#5f7f3d",
    "Dark Tea Leaf": "#3d5526",
    "Forest Shadow": "#25391a",
}

# Файлы для хранения данных
STUDENTS_FILE = 'students.json'
SCHEDULE_FILE = 'schedule.json'
TASKS_FILE = 'tasks.json'

# Список учеников: [{"name": "Имя", "subject": "Предмет", "size": "small|medium|large", "color": "#hex"}, ...]
students = []

# Расписание в формате: { "Monday": [события], ... }
# Событие: {student, subject, color, start, end, size}
schedule = {
    "Monday": [],
    "Tuesday": [],
    "Wednesday": [],
    "Thursday": [],
    "Friday": [],
    "Saturday": [],
    "Sunday": [],
}

# Список задач: [{"id": 1, "text": "Текст задачи", "completed": false, "date": "2024-01-01"}, ...]
tasks = []

weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekdays_ru = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

# Временной диапазон (с 7:00 до 23:00)
START_HOUR = 7
END_HOUR = 23
TOTAL_HOURS = END_HOUR - START_HOUR

# Коэффициенты размера для высоты событий
size_factors = {"small": 1.3, "medium": 1.6, "large": 1.9}


# Функции для сохранения и загрузки
def save_students():
    with open(STUDENTS_FILE, 'w') as f:
        json.dump(students, f)


def load_students():
    global students
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, 'r') as f:
            students = json.load(f)


def save_schedule():
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f)


def load_schedule():
    global schedule
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            schedule = json.load(f)


def save_tasks():
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f)


def load_tasks():
    global tasks
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r') as f:
            tasks = json.load(f)


# Функция для получения дат недели
def get_week_dates(week_offset=0):
    """Возвращает даты недели относительно текущей недели"""
    today = datetime.now().date()
    # Находим понедельник текущей недели
    start_of_week = today - timedelta(days=today.weekday())
    # Добавляем смещение недели
    start_of_week += timedelta(weeks=week_offset)

    week_dates = {}
    for i, day in enumerate(weekdays):
        current_date = start_of_week + timedelta(days=i)
        week_dates[day] = {
            "formatted": current_date.strftime("%d.%m.%Y"),
            "iso": current_date.strftime("%Y-%m-%d")
        }

    return week_dates


def get_today_tasks(selected_date):
    """Получаем задачи на выбранную дату"""
    return [task for task in tasks if task['date'] == selected_date]


# Загружаем данные при запуске
load_students()
load_schedule()
load_tasks()


@app.route("/load_data", methods=["POST"])
def load_data():
    try:
        data = request.get_json()
        global students, schedule

        # Обновляем данные
        students = data.get('students', [])
        schedule = data.get('schedule', {
            "Monday": [], "Tuesday": [], "Wednesday": [],
            "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []
        })

        # Сохраняем после загрузки
        save_students()
        save_schedule()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/")
def index():
    # Получаем номер недели из параметра (по умолчанию 0 - текущая неделя)
    week_offset = int(request.args.get('week', 0))
    week_dates = get_week_dates(week_offset)

    # Получаем задачи на сегодня (первый день выбранной недели)
    selected_date = week_dates["Monday"]["iso"]  # Можно изменить на текущий день
    today_tasks = get_today_tasks(selected_date)

    return render_template("schedule.html",
                           schedule=schedule,
                           weekdays=weekdays,
                           weekdays_ru=weekdays_ru,
                           palette=palette,
                           students=students,
                           size_factors=size_factors,
                           start_hour=START_HOUR,
                           end_hour=END_HOUR,
                           total_hours=TOTAL_HOURS,
                           week_offset=week_offset,
                           week_dates=week_dates,
                           today_tasks=today_tasks,
                           selected_date=selected_date)


@app.route("/add_task", methods=["POST"])
def add_task():
    task_text = request.form.get("task_text")
    task_date = request.form.get("task_date")
    week_offset = request.form.get("week_offset", 0)

    if task_text and task_date:
        new_task = {
            "id": len(tasks) + 1,
            "text": task_text,
            "completed": False,
            "date": task_date
        }
        tasks.append(new_task)
        save_tasks()

    return redirect(url_for("index", week=week_offset))


@app.route("/toggle_task/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    week_offset = request.form.get("week_offset", 0)

    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]
            break

    save_tasks()
    return redirect(url_for("index", week=week_offset))


@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    week_offset = request.form.get("week_offset", 0)

    global tasks
    tasks = [task for task in tasks if task["id"] != task_id]
    save_tasks()

    return redirect(url_for("index", week=week_offset))


@app.route("/students", methods=["GET", "POST"])
def manage_students():
    if request.method == "POST":
        name = request.form.get("name")
        subject = request.form.get("subject")
        size = request.form.get("size")
        color = request.form.get("color")
        if name and subject and size and color:
            # Проверяем, есть ли уже такой ученик
            existing = next((s for s in students if s["name"] == name), None)
            if existing:
                existing.update({"subject": subject, "size": size, "color": color})
            else:
                students.append({"name": name, "subject": subject, "size": size, "color": color})
            # Сохраняем после изменения
            save_students()
        return redirect(url_for("manage_students"))
    return render_template("students.html", students=students, palette=palette)


@app.route("/add_event", methods=["POST"])
def add_event():
    day = request.form.get("day")
    student_name = request.form.get("student")

    if day not in schedule:
        return "Неверный день", 400

    # Находим ученика по имени
    student = next((s for s in students if s["name"] == student_name), None)
    if not student:
        return "Ученик не найден", 400

    start = request.form.get("start")
    end = request.form.get("end")

    # Добавляем событие с данными из ученика
    schedule[day].append({
        "student": student["name"],
        "subject": student["subject"],
        "color": student["color"],
        "start": start,
        "end": end,
        "size": student["size"],
    })

    # Сохраняем после изменения
    save_schedule()

    # Получаем текущее смещение недели для возврата на ту же неделю
    week_offset = request.form.get('week_offset', 0)
    return redirect(url_for("index", week=week_offset))


@app.route("/update_event", methods=["POST"])
def update_event():
    day = request.form.get("day")
    index = int(request.form.get("index"))
    new_start = request.form.get("start")
    new_end = request.form.get("end")

    if day not in schedule or index < 0 or index >= len(schedule[day]):
        return "Неверные данные", 400

    # Обновляем время урока
    schedule[day][index]["start"] = new_start
    schedule[day][index]["end"] = new_end

    # Сохраняем после изменения
    save_schedule()

    # Получаем текущее смещение недели для возврата на ту же неделю
    week_offset = request.form.get('week_offset', 0)
    return redirect(url_for("index", week=week_offset))


@app.route("/delete_event", methods=["POST"])
def delete_event():
    day = request.form.get("day")
    index = int(request.form.get("index"))

    if day not in schedule or index < 0 or index >= len(schedule[day]):
        return "Неверные данные", 400

    # Удаляем урок
    del schedule[day][index]

    # Сохраняем после изменения
    save_schedule()

    # Получаем текущее смещение недели для возврата на ту же неделю
    week_offset = request.form.get('week_offset', 0)
    return redirect(url_for("index", week=week_offset))


@app.route("/remove_student/<name>", methods=["POST"])
def remove_student(name):
    global students
    students = [s for s in students if s["name"] != name]
    # Сохраняем после изменения
    save_students()
    return redirect(url_for("manage_students"))


if __name__ == "__main__":
    app.run(debug=True)