from db import *
import random
import re

def check_permission(tg_id):
    try:
        user = Users.get(id=tg_id)
        return user.role
    except:
        return 'non-role'
    
import math

def sort_vertices(vertices):
    # Вычисляем центр многоугольника
    center_x = sum(v[0] for v in vertices) / len(vertices)
    center_y = sum(v[1] for v in vertices) / len(vertices)

    # Сортируем вершины по углу относительно центра
    def angle(vertex):
        return math.atan2(vertex[1] - center_y, vertex[0] - center_x)
    
    return sorted(vertices, key=angle)

def is_point_in_polygon(x, y, polygon):
    """
    Проверяет, находится ли точка внутри многоугольника.
    
    :param x: Координата X точки
    :param y: Координата Y точки
    :param polygon: Список вершин многоугольника [(x1, y1), (x2, y2), ...]
    :return: True, если точка внутри многоугольника, иначе False
    """
    n = len(polygon)
    inside = False
    
    px, py = x, y
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        
        # Проверяем пересечение ребра многоугольника с горизонтальным лучом
        if min(y1, y2) < py <= max(y1, y2) and px <= max(x1, x2):
            # Вычисляем точку пересечения
            xinters = (py - y1) * (x2 - x1) / (y2 - y1) + x1 if y1 != y2 else x1
            if px < xinters:
                inside = not inside
    
    return inside

def find_coords(text):
    # Регулярное выражение для поиска координат
    pattern = r"(-?\d+\.\d+),\s*(-?\d+\.\d+)"

    # Поиск координат в строке
    match = re.search(pattern, text)

    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        return (latitude, longitude)
    return None

def find_task_id(text):
    pattern = r"(#\d{5})"
    match = re.search(pattern, text)
    if match:
        id = int(match.group(0)[1:])
        return id
    return None

def create_hash_for_task():
    flag = False
    all_tasks = Task.select()
    while not flag:
        hash_of_task = random.randint(10000, 99999)
        if len(all_tasks) == 0:
            flag = True
            break
        for task in all_tasks:
            if task.id != hash_of_task:
                flag = True
            else:
                flag = False
                break
    return hash_of_task

async def edit_msg(bot, cid, mid, eText, markup):
    try:
        return await bot.edit_message_text(
            chat_id = cid,
            message_id = mid,
            text = eText,
            reply_markup = markup,
            parse_mode = "HTML"
        )
    except:
        return await bot.edit_message_caption(
            chat_id = cid,
            message_id = mid,
            caption = eText,
            reply_markup = markup,
            parse_mode = "HTML"
        )

async def send_msg(bot, cid, text, markup, photo):
    try:
       return await bot.send_photo(
            caption = text,
            photo = photo,
            chat_id= cid,
            parse_mode="HTML",
            reply_markup = markup
        )
    except:
        return await bot.send_message(
            text =  text,
            chat_id= cid,
            parse_mode="HTML",
            reply_markup = markup
        )
    
async def send2Coordinator(msg, coordinators, coordinator_sequence, text_of_task, errorText, mid, kb):
    try:
        return await msg.bot.copy_message(chat_id=coordinators[coordinator_sequence].id, 
                                    from_chat_id = msg.chat.id, message_id=mid, 
                                    caption=text_of_task + '\n\n' + errorText,
                                    reply_markup = kb.reply_markup_problem,
                                    parse_mode = "HTML"
        )
    except:
        return await msg.bot.send_message(chat_id=coordinators[coordinator_sequence].id, 
                                    text=text_of_task + '\n\n' + errorText,
                                    reply_markup = kb.reply_markup_problem,
                                    parse_mode = "HTML"
        )