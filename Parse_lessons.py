import requests
from bs4 import BeautifulSoup

# URL страницы с расписанием
url = 'https://mpt.ru/raspisanie/'
TARGET_GROUP = "БИ50-3-24"

def fetch_week_type():
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    week_type_tag = soup.find('span', class_='label label-danger')
    if week_type_tag:
        return week_type_tag.text.strip()  # "Числитель" или "Знаменатель"
    
    return None

def fetch_schedule():
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    current_week_type = fetch_week_type()
    if not current_week_type:
        return "Ошибка: не удалось определить тип недели."
    
    group_block = None
    for block in soup.find_all('div', {'role': 'tabpanel'}):
        if block.find('h3') and TARGET_GROUP in block.find('h3').text:
            group_block = block
            break
    
    if not group_block:
        return f"Ошибка: не найдено расписание для группы {TARGET_GROUP}."

    # Функция для парсинга одного дня
    def parse_day(day_table):
        h4_tag = day_table.find('h4')
        if not h4_tag:
            return None
        
        day_name = h4_tag.contents[0].strip()
        lessons = day_table.find_all('tr')[1:]
        lesson_info = []

        for lesson in lessons:
            cells = lesson.find_all('td')
            if len(cells) == 3:
                time = cells[0].text.strip()

                numerator_subject = cells[1].find('div', class_='label label-danger')
                denominator_subject = cells[1].find('div', class_='label label-info')

                numerator_teacher = cells[2].find('div', class_='label label-danger')
                denominator_teacher = cells[2].find('div', class_='label label-info')

                if numerator_subject and denominator_subject:
                    if current_week_type == "Числитель":
                        subject = numerator_subject.text.strip()
                        teacher = numerator_teacher.text.strip() if numerator_teacher else ""
                    else:
                        subject = denominator_subject.text.strip()
                        teacher = denominator_teacher.text.strip() if denominator_teacher else ""
                elif numerator_subject:
                    subject = numerator_subject.text.strip()
                    teacher = numerator_teacher.text.strip() if numerator_teacher else ""
                elif denominator_subject:
                    subject = denominator_subject.text.strip()
                    teacher = denominator_teacher.text.strip() if denominator_teacher else ""
                else:
                    subject = cells[1].text.strip() if cells[1].text.strip() else ""
                    teacher = cells[2].text.strip() if cells[2].text.strip() else ""

                # Добавляем только, если предмет существует
                if subject:
                    lesson_info.append(f"Пара {time}: {subject} | Преподаватель: {teacher if teacher else 'Не указан'}")

        if not lesson_info:
            return None

        return f"--- {day_name.upper()} ---\n" + "\n".join(lesson_info)

    tables = group_block.find_all('table')
    schedule = [parse_day(day) for day in tables if day.find('h4')]

    return "\n\n".join(filter(None, schedule))

# Получаем расписание
schedule = fetch_schedule()

# Выводим расписание
if schedule:
    print(schedule)
else:
    print("Нет доступных пар.")
