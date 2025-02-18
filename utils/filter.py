import re

def is_valid_name(name):
    """Проверка валидности имени."""
    if not name or name.strip() == "":
        return False
    return bool(re.search(r'[a-zA-Zа-яА-Я0-9]', name))

def is_valid_teacher_name(name):
    """Проверка валидности имени преподавателя."""
    pattern = r'^(доц\.|проф\.|ст\.преп\.|асс\.|дек\.)?\s?[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$'
    return bool(re.match(pattern, name))

def is_valid_group_name(name):
    """Проверка валидности имени группы."""
    pattern = r'^[A-ZА-ЯЁ]+-\d+$'
    return bool(re.match(pattern, name))

def filter_groups(data):
    """Фильтрация групп с валидными именами."""
    unique_groups = {}
    for item in data:
        if item.get("name") and is_valid_group_name(item["name"]):
            unique_groups[item["id"]] = item  # Используем id как ключ для удаления дубликатов
    return list(unique_groups.values())

def filter_teachers(data):
    """Фильтрация преподавателей с валидными именами."""
    unique_teachers = {}
    for item in data:
        if item.get("name") and is_valid_teacher_name(item["name"]):
            unique_teachers[item["id"]] = item  # Используем id как ключ для удаления дубликатов
    return list(unique_teachers.values())