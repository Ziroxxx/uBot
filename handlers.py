from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import BaseFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import KeyboardButton

import aiohttp
import json
import random

from db import *
from states import *
from middlewares import *
import config
import kb
from text import *

router = Router()
coordinator_sequence = -1

@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    await state.clear()
    try:
        user = Users.get(id=msg.from_user.id)
        if user.role == 'admin':
            await msg.answer(infoText.admin, reply_markup=kb.admin_start_kb)
        elif user.role == 'sScout':
            await msg.answer(infoText.sScout, reply_markup=kb.ReplyKeyboardRemove())
        elif user.role == 'scout':
            await msg.answer(infoText.scout, reply_markup=kb.start_finish_kb)
        elif user.role == 'boss':
            await msg.answer(infoText.boss, reply_markup=kb.ReplyKeyboardRemove())
        elif user.role == 'coordinator':
            await msg.answer(infoText.coordinator, reply_markup=kb.coordinator_kb)
        else:
            await msg.answer(errorText.non_role, reply_markup=kb.ReplyKeyboardRemove())
    except:
        await msg.answer(infoText.hello)
        Users.create(id=msg.from_user.id, tg_username=msg.from_user.username, role='non-role')

@router.message(lambda msg: msg.text == '🔑 Назначить')
async def register_handler(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'admin':
        await msg.answer(infoText.admin_tag_change, reply_markup=kb.admin_back_kb)
        await state.set_state(RegisterState.waiting_for_telegram_tag)
    else:
        await msg.answer(errorText.no_rights)

@router.message(RegisterState.waiting_for_telegram_tag)
async def get_telegram_tag_handler(msg: Message, state: FSMContext):
    if msg.text == '🔙 Назад':
        await msg.answer(infoText.option, reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    tag = msg.text.strip()
    if not tag.startswith("@"):
        await msg.answer(errorText.tag_err)
        return

    try:
        # Пытаемся получить информацию о пользователе по тегу
        user = Users.get(tg_username=tag[1:])
        await state.update_data(tg_id=user.id)  # Сохраняем ID в состоянии
        await msg.answer(infoText.found_tag_answer(tag, user.id), reply_markup=kb.role_kb)
        await state.set_state(RegisterState.waiting_for_role)  # Переходим к следующему состоянию
    except:
        await msg.answer(errorText.no_user_by_tag)

@router.message(RegisterState.waiting_for_role)
async def get_role_handler(msg: Message, state: FSMContext):
    role = msg.text.strip()  # Получаем текст сообщения от пользователя

    # Проверяем корректность введенной роли
    valid_roles = ["Администратор", "Координатор", "Скаут", "СИТ", "Босс", "non-role"]
    if msg.text == "🔙 Назад":
        await msg.answer(infoText.option, reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    if role not in valid_roles:
        await msg.answer(errorText.invalid_role)
        return

    user_data = await state.get_data()
    user = Users.get(id=user_data.get('tg_id'))
    reply_kb = kb.start_kb
    if role == 'Скаут':
        role = 'scout'
        reply_kb = kb.start_finish_kb
    elif role == 'Координатор':
        role = 'coordinator'
        reply_kb = kb.coordinator_kb
    elif role == 'Администратор':
        role = 'admin'
        reply_kb = kb.admin_start_kb
    elif role == 'СИТ':
        role = 'sScout'
        reply_kb = kb.ReplyKeyboardRemove()
    elif role == 'Босс':
        role = 'boss'
        reply_kb = kb.ReplyKeyboardRemove()
    else:
        role = 'non-role'
        reply_kb = kb.ReplyKeyboardRemove()
    
    if role != 'coordinator':
        user.working_status = None

    user.role = role
    user.save()

    await msg.answer(infoText.updated_role_admin(role), reply_markup=kb.admin_start_kb)
    await msg.bot.send_message(chat_id=user.id, text=infoText.updated_role_user(role), reply_markup=reply_kb)
    await state.clear()  # Сбрасываем состояние

@router.message(lambda msg: msg.text == '⚙️ Новая карта зон')
async def set_map_info(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'admin':
        await msg.answer(infoText.load_map, reply_markup=kb.admin_back_kb)
        await state.set_state(LoadMapState.waiting_for_file)
    else:
        await msg.answer(errorText.no_rights)

@router.message(LoadMapState.waiting_for_file)
async def handle_json_file(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer(infoText.option, reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    if msg.document and (msg.document.mime_type == 'application/json' or msg.document.mime_type == 'application/geo+json'):
        file_id = msg.document.file_id
        file = await msg.bot.get_file(file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"

        # Загружаем файл как бинарный
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    file_content = await resp.read()  # Скачиваем файл как бинарный
                    try:
                        # Пытаемся загрузить содержимое как JSON
                        json_data = json.loads(file_content)  # Декодируем бинарные данные в JSON
                        # Парсим данные и добавляем в базу
                        await process_zones(json_data, msg, state)
                    except json.JSONDecodeError:
                        await msg.answer(errorText.failed_json)
                else:
                    await msg.answer(errorText.failed_load)
    else:
        await msg.answer(errorText.no_geoJSON)

async def process_zones(json_data, msg: Message, state: FSMContext):
    # Очищаем старые данные
    scouts = Mm.select()
    for s in scouts:
        await msg.bot.send_message(chat_id=s.scoutfk.id, text=errorText.update_db_warning, reply_markup=kb.start_finish_kb)
    Mm.delete().execute()
    Coordinate.delete().execute()  # Удаляем все старые координаты
    Zone.delete().execute()  # Удаляем все старые зоны

    try:
        # Извлекаем данные зон из JSON
        features = json_data.get('features', [])
        id_coord = 0
        
        for feature in features:
            # Получаем имя зоны и координаты
            try:
                zone_name_data = feature['properties']['description'].strip()
            except:
                await msg.answer(errorText.no_description, reply_markup=kb.admin_start_kb)
                await state.clear()
                return
            
            if ',' not in zone_name_data:
                await msg.answer(errorText.no_ao, reply_markup=kb.admin_start_kb)
                await state.clear()
                return

            zone_ao, zone_name = map(str.strip, zone_name_data.split(',', 1))
            coordinates = feature['geometry']['coordinates'][0]  # Получаем список координат
            id_zone = feature['id']

            # Создаём запись для зоны в базе данных
            zone, created = Zone.get_or_create(id=id_zone, name=zone_name, ao=zone_ao, status='non-active')

            if created:
                await msg.answer(f"Зона {zone_name} добавлена.")
            
            # Добавляем координаты в таблицу Coordinate
            for coord in coordinates:
                longitude, latitude = coord
                Coordinate.create(id=id_coord, longitude=longitude, latitude=latitude, zonefk=zone.id)
                id_coord += 1
        
        await msg.answer(infoText.success_load, reply_markup=kb.admin_start_kb)

    except Exception as e:
        await msg.answer(errorText.fatal_load(e))

class IsForwardedFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.forward_from or message.forward_from_chat)

@router.message(IsForwardedFilter())
async def handle_forwarded_message(msg: Message):
    if check_permission(msg.from_user.id) in ['sScout', 'admin']:
        global coordinator_sequence
        coordinator_sequence += 1
        coordinators = Users.select().where(Users.working_status == True)
        if len(coordinators) > 1:
            coordinator_sequence %= len(coordinators)
        else:
            coordinator_sequence = 0

        text_of_task = msg.text or msg.caption
        point = find_coords(text_of_task)
        hash_of_task = create_hash_for_task()
        new_task = Task.create(id=hash_of_task, admin_chat=msg.from_user.id, msg_text=text_of_task)

        if not (msg.text or msg.caption):
            await msg.answer(errorText.no_photo_or_text)
            return
        
        if not point:
            string_coords = ''
            sent_coordinator =await send2Coordinator(
                msg=msg,
                coordinators=coordinators,
                coordinator_sequence=coordinator_sequence,
                text_of_task=text_of_task,
                errorText=errorText.no_coordinates,
                mid=msg.message_id,
                kb=kb
            )
            new_task.coord_id = coordinators[coordinator_sequence].id
            new_task.coord_msg = sent_coordinator.message_id
            new_task.save()
        else:
            string_coords = str(point[0]) + ', ' + str(point[1])
            found = False
            found_zone = ''
            zones = Zone.select()
            for p in zones:
                coordinate_query = Coordinate.select().where(Coordinate.zonefk == p.id)
                coordinate_list = []
                for coord in coordinate_query:
                    x = coord.latitude
                    y = coord.longitude
                    coordinate_list.append((x, y))
                sorted_list = sort_vertices(coordinate_list)
                if is_point_in_polygon(point[0], point[1], sorted_list):
                    found = True
                    found_zone = p
                    break
            if found:
                scouts_on_zone = Users.select().join(Mm, on=(Users.id == Mm.scoutfk)).where(Mm.zonefk == found_zone.id)
                if len(scouts_on_zone) == 0:
                    sent_coordinator =await send2Coordinator(
                        msg=msg,
                        coordinators=coordinators,
                        coordinator_sequence=coordinator_sequence,
                        text_of_task=text_of_task.replace(string_coords, '<code>' + string_coords + '</code>'),
                        errorText=errorText.no_active_scout(found_zone.name),
                        mid=msg.message_id,
                        kb=kb
                    )
                    new_task.coord_id = coordinators[coordinator_sequence].id
                    new_task.coord_msg = sent_coordinator.message_id
                    new_task.save()
                for s in scouts_on_zone:
                    if msg.photo:
                        await msg.bot.send_photo(chat_id=s.id, photo=msg.photo[-1].file_id, caption=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')+f"\n#{new_task.id}", reply_markup=kb.reply_markup)
                    else:
                        await msg.bot.send_message(chat_id=s.id, text=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')+f"#{new_task.id}", reply_markup=kb.reply_markup)
            else:
                sent_coordinator =await send2Coordinator(
                    msg=msg,
                    coordinators=coordinators,
                    coordinator_sequence=coordinator_sequence,
                    text_of_task=text_of_task.replace(string_coords, '<code>' + string_coords + '</code>'),
                    errorText=errorText.unknown_point,
                    mid=msg.message_id,
                    kb=kb
                )
                new_task.coord_id = coordinators[coordinator_sequence].id
                new_task.coord_msg = sent_coordinator.message_id
                new_task.save()
            
        sent_message = await send_msg(msg.bot, msg.chat.id, msgStatusText.first_stage(text_of_task, string_coords, new_task.id), None, msg.photo[-1].file_id)
        await msg.bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)

        # Сохраняем message_id в уже созданной записи
        new_task.msg_status = sent_message.message_id
        new_task.save()
    else:
        await msg.answer(errorText.no_rights)

@router.callback_query()
async def hadle_callback(callback_query: types.CallbackQuery, state: FSMContext):
    id_task = find_task_id(callback_query.message.text or callback_query.message.caption)
    if not id_task:
        id_task = Task.get_or_none((Task.coord_msg == callback_query.message.message_id) & (Task.coord_id == callback_query.message.chat.id)) 
    task_object = Task.get(id=id_task)
    text_of_task_CS = callback_query.message.text or callback_query.message.caption
    text_of_task_A = task_object.msg_text
    cords = find_coords(task_object.msg_text)
    if cords:
        cords_str = str(cords[0]) + ', ' + str(cords[1])
    else:
        cords_str = ''

    if callback_query.data == "handler_accept":
        if task_object.scoutfk == None:
            task_object.scoutfk = callback_query.from_user.id
            task_object.msg_id_scout = callback_query.message.message_id
            task_object.save()

            
            new_text = text_of_task_CS.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n<b>Вы приняли задание! #{id_task}📌</b>"
            await edit_msg(callback_query.bot, task_object.scoutfk.id, task_object.msg_id_scout, new_text, kb.reply_markup_done)
            try:
                await edit_msg(callback_query.bot, task_object.admin_chat, task_object.msg_status, msgStatusText.second_stage(text_of_task_A, cords_str, id_task), None)
                await callback_query.bot.send_message(chat_id=task_object.admin_chat, text=infoText.scout_accepted(id_task), reply_to_message_id=task_object.msg_status)
            except:
                pass

            if task_object.coord_id:
                await edit_msg(callback_query.bot, task_object.coord_id, task_object.coord_msg, msgStatusText.second_stage(text_of_task_CS, cords_str, id_task), None)
                await state.update_data(full_text = text_of_task_CS)
        else:
            await callback_query.message.answer(errorText.already_in_use)
            return

    if callback_query.data == 'handler_done_task':
        data = await state.get_data()
        full_text = data.get('full_text') or text_of_task_A
        new_text = full_text.replace(cords_str, '<code>'+cords_str+'</code>') + infoText.photo_prove(id_task)
        await edit_msg(callback_query.bot, task_object.scoutfk.id, task_object.msg_id_scout, new_text, kb.reply_markup_back)
        await state.update_data(task_object=task_object, full_text = full_text)
        await state.set_state(DoneTaskState.waiting_for_photo)
    
    if callback_query.data == 'handler_done_back':
        data = await state.get_data() 
        full_text = data.get('full_text') or text_of_task_A

        new_text = full_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n<b>Вы приняли задание! #{id_task}📌</b>"
        await edit_msg(callback_query.bot, task_object.scoutfk.id, task_object.msg_id_scout, new_text, kb.reply_markup_done)
        return
    
    if callback_query.data == 'handler_delegate':
        new_text = text_of_task_CS.replace(cords_str, '<code>'+ cords_str +'</code>') + infoText.coordinator_tag_deligate
        await edit_msg(callback_query.bot, task_object.coord_id, task_object.coord_msg, new_text, kb.reply_markup_problem_back)
        await state.update_data(text=callback_query.message.text or callback_query.message.caption, id_task=id_task, photo_id = callback_query.message.photo[-1].file_id)
        await state.set_state(CoordinatorState.waiting_for_tag)

    if callback_query.data == 'handler_coord_back':
        data = await state.get_data()
        full_text = data.get('text').replace(cords_str, '<code>' + cords_str + '</code>')
        await edit_msg(callback_query.bot, task_object.coord_id, task_object.coord_msg, full_text, kb.reply_markup_problem)
        await state.clear()

    if callback_query.data == 'handler_deny':
        new_text = text_of_task_CS.replace(cords_str, '<code>' + cords_str + '</code>') + '\n\n<b>Введите причину отказа...</b>'
        await edit_msg(callback_query.bot, task_object.coord_id, callback_query.message.message_id, new_text, kb.reply_markup_deny_back)
        await state.update_data(text=text_of_task_CS.replace(cords_str, '<code>' + cords_str + '</code>'), id_task=id_task)
        await state.set_state(CoordinatorState.waiting_for_reason)
    
    if callback_query.data == 'handler_deny_back':
        data = await state.get_data()
        textCS = data.get("text")
        await edit_msg(callback_query.bot, task_object.coord_id, callback_query.message.message_id, textCS, kb.reply_markup_problem)
        await state.clear()

@router.message(CoordinatorState.waiting_for_reason)
async def handler_deny_task(msg: Message, state: FSMContext):
    try:
        data = await state.get_data()
        textCS = data.get("text")
        id_task = data.get("id_task")

        task_object = Task.get(id=id_task)
        reason = msg.text.strip()
        coords = find_coords(task_object.msg_text)
        if coords:
            coords_str = str(coords[0]) + ', ' + str(coords[1])
        else:
            coords_str = ''
        await edit_msg(msg.bot, task_object.admin_chat, 
                       task_object.msg_status, 
                       msgStatusText.first_stage(task_object.msg_text, coords_str, task_object.id) + f'\n<b>ЗАДАНИЕ ОТМЕНЕНО ПО ПРИЧИНЕ: {reason}</b>', None)
        new_text = textCS + f'\n<b>ЗАДАНИЕ ОТМЕНЕНО ПО ПРИЧИНЕ: {reason}</b>'
        await edit_msg(msg.bot, msg.chat.id, task_object.coord_msg, new_text, None)
        Task.delete().where(Task.id == task_object.id).execute()
    except Exception as e:
        print(str(e))
        await msg.answer("⚠️ Произошла ошибка при отмене задания!")

@router.message(CoordinatorState.waiting_for_tag)
async def handler_waiting_stag(msg: Message, state: FSMContext):
    tag = msg.text.strip()
    if not tag.startswith("@"):
        await msg.answer(errorText.tag_err)
        return

    try:
        # Пытаемся получить информацию о пользователе по тегу
        user = Users.get(tg_username=tag[1:])
        await state.update_data(tg_id=user.id)  # Сохраняем ID в состоянии
        await msg.answer(infoText.found_tag_answer(tag, user.id) + '\n\n' + infoText.optional_caption)
        await state.set_state(CoordinatorState.waiting_for_caption)  # Переходим к следующему состоянию
    except:
        await msg.answer(errorText.no_user_by_tag)

@router.message(CoordinatorState.waiting_for_caption)
async def handler_waiting_caption(msg: Message, state: FSMContext):
    data = await state.get_data()
    scout_tgid = data.get("tg_id")
    full_text = data.get("text")
    id_task = data.get("id_task")
    photo_id = data.get("photo_id")

    cords = find_coords(full_text)
    if cords:
        coords_str = str(cords[0]) + ', ' + str(cords[1])
        full_text = full_text.replace(coords_str, '<code>'+ coords_str +'</code>')

    task_object = Task.get(id=id_task)
    if msg.text == '.':
        text = full_text + f'\n\n<b>Это задание было отправлено координатором!\n#{id_task}</b>'
    else:
        text = full_text + f'\n\n<b>Это задание было отправлено координатором!</b>' + f'\n<b>Пояснение координатора:\n</b>{msg.text}\n#{id_task}'

    await send_msg(msg.bot, scout_tgid, text, kb.reply_markup, photo_id)
    coords = find_coords(text)
    coords_str = str(coords[0]) + ', ' + str(coords[1])
    if not coords_str:
        coords_str = ''
    await edit_msg(msg.bot, msg.chat.id, task_object.coord_msg, msgStatusText.first_stage(text, coords_str, id_task), None)
    
    


@router.message(lambda msg: msg.text == '🚀 Выйти на слот' or msg.text == '➕ Добавить слот')
async def handler_enter_slot(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'scout':
        zones = Zone.select()
        if len(zones) == 0:
            await msg.answer(errorText.no_zones, reply_markup=kb.start_finish_kb)
            await state.clear()
            return
        zones_ao = [z.ao for z in zones]
        zones_kb = kb.create_dynamic_keyboard(list(set(zones_ao)))
        zones_kb.keyboard.append([kb.btnBack])
        await msg.answer(infoText.choose_ao, reply_markup=zones_kb)
        await state.set_state(SlotState.waiting_for_ao)
    else:
        await msg.answer(errorText.not_scout)

@router.message(SlotState.waiting_for_ao)
async def handler_choose_ao(msg: Message, state: FSMContext):
    ao = msg.text.strip()
    if ao == '🔙 Назад':
        await msg.answer(infoText.option, reply_markup=kb.start_finish_kb)
        await state.clear()
        return
    ao_bd = [z.ao for z in Zone.select()]
    if ao not in ao_bd:
        await msg.answer(errorText.invalid_ao, reply_markup=kb.start_finish_kb)
        await state.clear()
        return
    zones_obj = Zone.select().where(Zone.ao == ao)
    zones_names = [z.name for z in zones_obj]
    zones_kb = kb.create_dynamic_keyboard(zones_names)
    zones_kb.keyboard.append([kb.btnBack])
    await msg.answer("Выберите зону...", reply_markup=zones_kb)
    await state.set_state(SlotState.waiting_for_zone)



@router.message(SlotState.waiting_for_zone)
async def hadler_start_slot(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await state.clear()
        await handler_enter_slot(msg, state)
        return
    try:
        zone_msg = msg.text.strip()
        zone_object = Zone.select().where(Zone.name == zone_msg).first()
        size_mm = Mm.select()
        scout_on_zone = Mm.create(id=len(size_mm)+1, zonefk=zone_object.id, scoutfk=msg.from_user.id)
        scout_on_zone.save()
        await msg.answer(infoText.entered_slot(zone_msg), reply_markup=kb.scout_work_kb)
        await state.clear()
    except Exception as e:
        await msg.answer(errorText.invalid_zone + '\n' + str(e))

@router.message(lambda msg: msg.text == "🏠 Уйти со слота")
async def handler_exit_slot(msg: Message, state: FSMContext):
    await state.clear()
    if check_permission(msg.from_user.id) == 'scout':
        scout_zones = Mm.select().where(Mm.scoutfk == msg.from_user.id)
        user = Users.get(id=msg.from_user.id)
        if not scout_zones:
            await msg.answer(errorText.not_entered)
            return
        
        tasks = Task.select().where(Task.scoutfk == user)
        if tasks:
            await msg.answer(errorText.scout_have_tasks, reply_markup=kb.submit_kb)
            await state.update_data(user=user, tasks=tasks)
            await state.set_state(SlotState.waiting_for_submit)
        else:
            Mm.delete().where(Mm.scoutfk == user.id).execute()
            await msg.answer(infoText.leaved, reply_markup=kb.start_finish_kb)

@router.message(SlotState.waiting_for_submit)
async def handler_submit_exit(msg: Message, state: FSMContext):
    if msg.text == 'Да':
        global coordinator_sequence
        coordinators = Users.select().where(Users.working_status == True)
        if not coordinators:
            await msg.answer(errorText.no_active_coordinator, reply_markup=kb.start_kb)
            await state.clear()
        data = await state.get_data()
        user = data.get("user")
        tasks = data.get("tasks")

        for task in tasks:
            cords = find_coords(task.msg_text)
            if cords:
                str_cords = str(cords[0]) + ', ' + str(cords[1])
            else:
                str_cords = ''
            coordinator_sequence += 1
            coordinator_sequence %= len(coordinators)
            sent_coordinator = await send2Coordinator(
                msg,
                coordinators,
                coordinator_sequence,
                task.msg_text.replace(str_cords, '<code>'+ str_cords +'</code>'),
                errorText.scout_leaved,
                task.msg_id_scout,
                kb
            )
            task.coord_id = coordinators[coordinator_sequence].id
            task.coord_msg = sent_coordinator.message_id
            task.msg_id_scout = None
            task.scoutfk = None
            task.save()
        Mm.delete().where(Mm.scoutfk == user.id).execute()
        await msg.answer(infoText.leaved, reply_markup=kb.start_finish_kb)
    else:
        await msg.answer("Вы остались на слоте!", reply_markup=kb.start_finish_kb)
        await state.clear()

@router.message(DoneTaskState.waiting_for_photo)
async def handler_get_task(msg: Message, state: FSMContext):
    data = await state.get_data()
    task_object = data.get("task_object")
    text_of_task_SC = data.get("full_text")
    text_of_task_A = task_object.msg_text
    coords = find_coords(text_of_task_SC)
    if coords:
        string_coords = str(coords[0]) + ', ' + str(coords[1])
    else:
        string_coords = ''

    if not msg.photo:
        await msg.answer(errorText.no_photo)
        return
    else:
        await msg.answer(infoText.task_scout_done(task_object.id), reply_markup=kb.start_finish_kb, reply_to_message_id=task_object.msg_id_scout)
        await msg.bot.copy_message(chat_id=task_object.admin_chat, from_chat_id=msg.chat.id, message_id=msg.message_id, reply_to_message_id=task_object.msg_status)
        await edit_msg(msg.bot, task_object.admin_chat, task_object.msg_status, msgStatusText.third_stage(text_of_task_A, string_coords, task_object.id), None)
        await edit_msg(msg.bot, task_object.scoutfk.id, task_object.msg_id_scout, 
                       text_of_task_SC.replace(string_coords, '<code>'+string_coords+'</code>') + f'\n\n<b>Задание #{task_object.id} выполнено🎖️</b>',
                        None)
        if task_object.coord_id:
            await edit_msg(msg.bot, task_object.coord_id, task_object.coord_msg, msgStatusText.third_stage(text_of_task_SC, string_coords, task_object.id), None)
            await msg.bot.copy_message(chat_id=task_object.coord_id, from_chat_id=msg.chat.id, message_id=msg.message_id, reply_to_message_id=task_object.coord_msg)
        await msg.bot.send_message(chat_id=task_object.admin_chat, text=f"Задание #{task_object.id} выполнено скаутом.")

        Task.delete().where(Task.id == task_object.id).execute()
        await state.clear()

@router.message(lambda msg: msg.text == '🚀 Выйти на смену')
async def handler_coord_start(msg: Message):
    if check_permission(msg.from_user.id) == 'coordinator':
        user = Users.get(id=msg.from_user.id)
        if user.working_status:
            await msg.answer('Вы уже на смене!')
            return
        
        user.working_status = True
        user.save()
        await msg.answer('Вы вышли на смену!')
    else:
        await msg.answer('🚫 Вы не СИТ!')

@router.message(lambda msg: msg.text == '🏠 Уйти со смены')
async def handler_coord_end(msg: Message):
    if check_permission(msg.from_user.id) == 'coordinator':
        user = Users.get(id=msg.from_user.id)
        if not user.working_status:
            await msg.answer('Вы не выходили на смену!')
            return
        
        user.working_status = False
        user.save()
        await msg.answer('Вы ушли со смены!')
    else:
        await msg.answer('🚫 Вы не СИТ!')

@router.message(lambda msg: msg.text == '🔎 Список')
async def handler_search_scouts(msg: Message):
    #@tag - zone_name[0], zone_name[1]....\n
    result = {}
    mm_zones_object = Mm.select()
    if not mm_zones_object:
        await msg.answer('Сейчас нет активных скаутов.')
        return
    for slot in mm_zones_object:
        scout = slot.scoutfk
        zone = slot.zonefk

        if scout.tg_username in result:
            result[scout.tg_username].append(zone.name)
        else:
            result[scout.tg_username] = [zone.name]

    text = ''
    for scout, zones in result.items():
        text += '@' + scout + ' - ' + str(zones) + '\n'

    await msg.answer('Активные скауты:\n' + text)
    

#created by Zirox with hate :)
    