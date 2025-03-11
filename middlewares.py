from db import *
from text import *
from collections import deque
import kb
import random
import re
import datetime

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

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
    except:
        user = Users.get(id=cid)
        if user.role in ["boss", "sScout", "admin"]:
            print(f"user: {user.tg_username} was deleted from db!")
            Users.delete().where(Users.id == cid).execute()
        elif user.role == 'coordinator':
            await banned_from_coordinator(bot, user.id)
        else:
            pass
    
async def send_msg(bot, cid, text, markup, photo, problem_task=None, coordinator_id=None, message_orig_id=None):
    try:
        try:
            #можно попробовать copy_message, аналогично send2Coordinator
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
    except:
        user = Users.get(id=cid)
        if user.role in ["boss", "sScout", "admin"]:
            print(f"user: {user.tg_username} was deleted from db!")
            Users.delete().where(Users.id == cid).execute()
        elif user.role == 'coordinator':
            await banned_from_coordinator(bot, user.id)
        else:
            await banned_from_scout(bot, user, problem_task, coordinator_id, message_orig_id)
    
async def send2Coordinator(msg, coordinators, coordinator_sequence, text_of_task, error_text, cid, mid, kb, task, coordinator_list=None):
    if coordinator_list is None:
        coordinator_list = []
    try:
        try:
            sent = await msg.bot.copy_message(chat_id=coordinators[coordinator_sequence].id, 
                                        from_chat_id = cid, message_id=mid, 
                                        caption=text_of_task + '\n\n' + error_text,
                                        reply_markup = kb.reply_markup_problem,
                                        parse_mode = "HTML"
            )
            task.err_id = list(errorText.coordinator_errors.values()).index(error_text)
            task.coord_id = coordinators[coordinator_sequence].id
            task.coord_msg = sent.message_id
            task.save()
            return sent
        except:
            sent = await msg.bot.send_message(chat_id=coordinators[coordinator_sequence].id, 
                                        text=text_of_task + '\n\n' + error_text,
                                        reply_markup = kb.reply_markup_problem,
                                        parse_mode = "HTML"
            )
            task.err_id = list(errorText.coordinator_errors.values()).index(error_text)
            task.coord_id = coordinators[coordinator_sequence].id
            task.coord_msg = sent.message_id
            task.save()
            return sent
    except TelegramForbiddenError:
        coordinator_list = filter(lambda x: x != coordinators[coordinator_sequence], coordinator_list)
        await banned_from_coordinator(msg.bot, coordinators[coordinator_sequence].id, task, msg.message_id)

async def send2Coordinator_bot2(bot, coordinator_id, text_of_task, error_text, cid, mid, task):
    try:
        try:
            sent = await bot.copy_message(chat_id=coordinator_id, 
                                        from_chat_id = cid, message_id=mid, 
                                        caption=text_of_task + '\n\n' + error_text,
                                        reply_markup = kb.reply_markup_problem,
                                        parse_mode = "HTML"
            )
            task.err_id = list(errorText.coordinator_errors.values()).index(error_text)
            task.coord_id = coordinator_id
            task.coord_msg = sent.message_id
            task.datetimestamp_sent = None
            task.scouts = None
            task.save()
            return sent
        except:
            sent = await bot.send_message(chat_id=coordinator_id, 
                                        text=text_of_task + '\n\n' + error_text,
                                        reply_markup = kb.reply_markup_problem,
                                        parse_mode = "HTML"
            )
            task.err_id = list(errorText.coordinator_errors.values()).index(error_text)
            task.coord_id = coordinator_id
            task.coord_msg = sent.message_id
            task.datetimestamp_sent = None
            task.scouts = None
            task.save()
            return sent
    except TelegramForbiddenError:
        await banned_from_coordinator(bot, coordinator_id, task)
    
async def send2Coordinator_bot(bot, coordinators, coordinator_sequence, text_of_task, errorText, cid, mid):
    try:
        return await bot.copy_message(chat_id=coordinators[coordinator_sequence].id, 
                                    from_chat_id = cid, message_id=mid, 
                                    caption=text_of_task + '\n\n' + errorText,
                                    reply_markup = kb.reply_markup_problem,
                                    parse_mode = "HTML"
        )
    except:
        return await bot.send_message(chat_id=coordinators[coordinator_sequence].id, 
                                    text=text_of_task + '\n\n' + errorText,
                                    reply_markup = kb.reply_markup_problem,
                                    parse_mode = "HTML"
        )

async def copyTaskTo(bot, from_chat, from_msg, to_chat, own_text=None, markup=None):
    if own_text != None:
        return await bot.copy_message(chat_id=to_chat, 
                                    from_chat_id=from_chat, 
                                    message_id=from_msg,
                                    caption=own_text,
                                    reply_markup=markup,
                                    parse_mode="HTML")
    else:
        return await bot.copy_message(chat_id=to_chat, 
                                    from_chat_id=from_chat, 
                                    message_id=from_msg,
                                    reply_markup=markup,
                                    parse_mode="HTML")


#---------------------ОБРАБОТКА_БАНОВ_И_ДЕЛЕГИРОВАНИЙ---------------------#
async def banned_from_coordinator(bot, user_id, problem_task=None, problem_task_orig=None):
    processed_users = set()
    queue = deque([user_id])  # Очередь пользователей для обработки

    while queue:
        user_id = queue.popleft()  # Берем следующего пользователя
        if user_id in processed_users:
            continue  # Пропускаем, если уже обработан

        processed_users.add(user_id)

        # Получаем пользователя из БД
        user = Users.get(id=user_id)
        danger_tasks = get_tasks_one_coordinator(user_id)
        print(f'coordinator {user.tg_username} was deleted from db!')

        # Находим других активных координаторов
        other_active_coordinators = Users.select().where(
            (Users.role == 'coordinator') & (Users.working_status == True) & Users.id.not_in(list(queue))
        )

        if len(other_active_coordinators) == 0:
            for task in danger_tasks:
                await auto_cancel_task(bot, task)

            if problem_task is not None:
                await auto_cancel_task(bot, problem_task)
                problem_task = None

            Users.delete().where(Users.id == user_id).execute()
            continue  # Переходим к следующему пользователю

        delegated_danger = False

        for i in range(len(other_active_coordinators)):
            for task in danger_tasks:
                try:
                    sent = await send2Coordinator_bot(
                        bot, other_active_coordinators, i, 
                        task.msg_text, errorText.coordinator_errors['banned'], 
                        task.admin_chat, task.msg_status
                    )
                    task.datetimestamp_sent = None
                    task.scouts = None
                    task.coord_id = other_active_coordinators[i].id
                    task.coord_msg = sent.message_id
                    task.err_id = 6
                    task.save()
                    delegated_danger = True
                except TelegramForbiddenError:  # Другой координатор забанил бота
                    queue.append(other_active_coordinators[i].id)  # Добавляем в очередь
                    delegated_danger = False
                    break
                except TelegramBadRequest:  # Забанил СИТ
                    Users.delete().where(Users.id == task.admin_chat).execute()
                    await auto_cancel_task(bot, task)
                    danger_tasks.remove(task)
            
            if delegated_danger:
                break

        if not delegated_danger and len(danger_tasks) > 0:
            for task in danger_tasks:
                await auto_cancel_task(bot, task)

            if problem_task is not None:
                await auto_cancel_task(bot, problem_task)
                problem_task = None

        Users.delete().where(Users.id == user_id).execute()
        print('process deleting coordinator finished')

    if problem_task is not None:
        true_active_coordinator = Users.select().where((Users.role == 'coordinator') & (Users.working_status == True)).first()
        if true_active_coordinator:
            sent = await send2Coordinator_bot(
                        bot, [true_active_coordinator], 0, 
                        problem_task.msg_text, errorText.coordinator_errors['banned'], 
                        problem_task.admin_chat, problem_task.msg_status if problem_task.msg_status else problem_task_orig
                    )
            problem_task.datetimestamp_sent = None
            problem_task.scouts = None
            problem_task.coord_id = true_active_coordinator.id
            problem_task.coord_msg = sent.message_id
            problem_task.err_id = 6
            problem_task.save()
        else:
            await auto_cancel_task(bot, problem_task)

async def auto_cancel_task(bot, task):
    if task.coord_id != None:
        try:
            await bot.delete_message(chat_id=task.coord_id, message_id=task.coord_msg)
        except:
            print('sScout banned bot')
    
    if task.scouts != None:
        splited = task.scouts.split()
        for i in range(0, len(splited), 2):
            if i+1 < len(splited):
                try:
                    await bot.delete_message(chat_id=splited[i], message_id=splited[i+1])
                except:
                    print('scout banned bot')

    if task.msg_status != None:
        coords = find_coords(task.msg_text)
        if coords:
            coords_str = str(coords[0]) + ', ' + str(coords[1])
        else:
            coords_str = ''
        new_text = msgStatusText.first_stage(task.msg_text, coords_str, task.id) + f"\n\n<b>ЗАДАНИЕ ОТМЕНЕНО ПО ПРИЧИНЕ: {errorText.coordinator_errors['cancel_task']}</b>"
        bosses = boss_task.select().where(boss_task.id_task == task.id)
        for boss in bosses:
            await edit_msg(bot, boss.id_boss, boss.id_msg, new_text, None)
        await edit_msg(bot, task.admin_chat, task.msg_status, new_text, None)
    else:
        await send_msg(bot, task.admin_chat, errorText.no_coordinator, None, None)

    task.delete_instance()

def get_tasks_one_scout(scout_id):
    tasks = Task.select()
    result = []

    for task in tasks:
        if task.scouts:
            scouts_messages_for_task = task.scouts.split()
        else:
            continue

        if len(scouts_messages_for_task) < 2:
            continue

        if task.scoutfk and task.scoutfk.id == scout_id:
            result.append(task)
            continue

        if str(scout_id) in scouts_messages_for_task and len(scouts_messages_for_task) == 2:
            result.append(task)
        
    return result

def get_tasks_one_coordinator(coordinator_id):
    return Task.select().where((Task.coord_id == coordinator_id) & (Task.scoutfk == None))

def remove_scout_from_list(task, scout_id):
    scouts_messages = task.scouts
    list_scout_messages = scouts_messages.split()
    i = 0
    while i < len(list_scout_messages):
        if list_scout_messages[i] == str(scout_id):
            list_scout_messages.pop(i)
            if i < len(list_scout_messages):
                list_scout_messages.pop(i)
        else:
            i += 1

    scouts_messages = ' '.join(list_scout_messages)
    task.scouts = scouts_messages
    task.save()

async def deleteCordTask(bot, task):
    if task.coord_id != None:
       await bot.delete_message(chat_id = task.coord_id, message_id = task.coord_msg)

async def send2OtherScouts(bot, task, scouts, scouts_queue, dict_zone_scouts):
    flag_sent = False
    scouts_sent = ''
    for scout in scouts:
        try:    
            err_text = list(errorText.coordinator_errors.values())[task.err_id] if task.err_id != None else ''
            text_of_task = task.msg_text
            new_text = text_of_task + '\n\n' + err_text + f"\n#{task.id}"
            sent = await copyTaskTo(bot, task.admin_chat, task.msg_status, scout.id, new_text, kb.reply_markup)
            scouts_sent += f' {scout.id} {sent.message_id}'
            flag_sent = True
        except TelegramForbiddenError:
            scouts_queue.append(scout)
            for key in dict_zone_scouts:
                if scout in dict_zone_scouts[key]:
                    dict_zone_scouts[key].remove(scout)

    if flag_sent:
        task.scouts = scouts_sent
        task.datetimestamp_sent = datetime.datetime.now()
        task.save()

def get_dict_zone_scouts(problem_scout):
    dict_zone_scouts = {}
    all_scouts_mm = Mm.select()

    for mm in all_scouts_mm:
        zone = mm.zonefk.id
        scout = mm.scoutfk

        if zone not in dict_zone_scouts and scout != problem_scout:
            dict_zone_scouts[zone] = [scout]
        elif scout != problem_scout:
            dict_zone_scouts[zone].append(scout)
    
    return dict_zone_scouts

async def banned_from_scout(bot, problem_scout, problem_task, coordinator_id=None, message_orig_id=None):
    dict_zone_scouts = get_dict_zone_scouts(problem_scout)
    print(dict_zone_scouts, problem_scout)
    tasks_to_coordinator = []

    scouts_queue = deque([problem_scout])

    while scouts_queue:
        scout_to_processing = scouts_queue.popleft()
        danger_tasks = get_tasks_one_scout(scout_to_processing.id)

        for task in danger_tasks:
            remove_scout_from_list(task, scout_to_processing.id)
            await deleteCordTask(bot, task)

            if task.zone_id is not None:
                other_scouts_on_zone = dict_zone_scouts.get(task.zone_id)
                if other_scouts_on_zone:
                    await send2OtherScouts(bot, task, other_scouts_on_zone, scouts_queue, dict_zone_scouts)
                    dict_zone_scouts = {key: val for key, val in dict_zone_scouts.items() if val}
                else:
                    tasks_to_coordinator.append(task)
            else:
                tasks_to_coordinator.append(task)
        
        print(f'scout {problem_scout.tg_username} was deleted from db!')
        Mm.delete().where(Mm.scoutfk == scout_to_processing).execute()
        scout_to_processing.delete_instance()

    if len(tasks_to_coordinator) > 0:
        if coordinator_id is not None:
            for task in tasks_to_coordinator:
                await send2Coordinator_bot2(bot, coordinator_id, task.msg_text, errorText.coordinator_errors['banned'], task.admin_chat, task.msg_status, task)
            if problem_task.msg_status is not None:
                await send2Coordinator_bot2(bot, coordinator_id, problem_task.msg_text, errorText.coordinator_errors['banned'], problem_task.admin_chat, problem_task.msg_status, problem_task)
            else:
                await send2Coordinator_bot2(bot, coordinator_id, problem_task.msg_text, errorText.coordinator_errors['banned'], problem_task.admin_chat, message_orig_id, problem_task)
        else:
            for task in tasks_to_coordinator:
                first_coordinator = Users.select().where((Users.role == 'coordinator') & (Users.working_status == True)).first()
                if first_coordinator:
                    await send2Coordinator_bot2(bot, first_coordinator.id, task.msg_text, errorText.coordinator_errors['banned'], task.admin_chat, task.msg_status, task)
                else:
                    await auto_cancel_task(bot, task)
            
            if problem_task.zone_id is None or (problem_task.zone_id is not None and problem_task.zone_id not in dict_zone_scouts):
                if problem_task.msg_status is not None:
                    first_coordinator = Users.select().where((Users.role == 'coordinator') & (Users.working_status == True)).first()
                    if first_coordinator:
                        await send2Coordinator_bot2(bot, first_coordinator.id, problem_task.msg_text, errorText.coordinator_errors['banned'], problem_task.admin_chat, problem_task.msg_status, problem_task)
                    else:
                        await auto_cancel_task(bot, problem_task)
                else:
                    first_coordinator = Users.select().where((Users.role == 'coordinator') & (Users.working_status == True)).first()
                    if first_coordinator:
                        await send2Coordinator_bot2(bot, first_coordinator.id, problem_task.msg_text, errorText.coordinator_errors['banned'], problem_task.admin_chat, message_orig_id, problem_task)
                    else:
                        await auto_cancel_task(bot, problem_task)

    print('process deleting scout finished')





