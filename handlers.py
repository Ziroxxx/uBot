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

router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    try:
        user = Users.get(id=msg.from_user.id)
        if user.role == 'admin':
            await msg.answer("Вы админ бота!", reply_markup=kb.admin_start_kb)
        elif user.role == 'sScout':
            await msg.answer("Вы администрация города!", reply_markup=kb.coord_start_kb)
        elif user.role == 'scout':
            await msg.answer("Вы скаут!", reply_markup=kb.start_finish_kb)
        else:
            await msg.answer("⚠️ Вы пока ещё не получили роль.")
    except:
        await msg.answer("Привет! Я зарегистрировал тебя. Дождись, пока руководство выдаст тебе роль внутри бота!\nДля проверки своей роли снова воспользуйся /start")
        Users.create(id=msg.from_user.id, tg_username=msg.from_user.username, role='non-role')

@router.message(lambda msg: msg.text == '🔑 Назначить')
async def register_handler(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'admin':
        await msg.answer("Введите @тег пользователя, права которого вы хотите изменить.", reply_markup=kb.admin_back_kb)
        await state.set_state(RegisterState.waiting_for_telegram_tag)
    else:
        await msg.answer("🚫 Вы не имеете прав на это действие!")

@router.message(RegisterState.waiting_for_telegram_tag)
async def get_telegram_tag_handler(msg: Message, state: FSMContext):
    if msg.text == '🔙 Назад':
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    tag = msg.text.strip()
    if not tag.startswith("@"):
        await msg.answer("⚠️ Тег должен начинаться с '@'. Попробуйте снова.")
        return

    try:
        # Пытаемся получить информацию о пользователе по тегу
        user = Users.get(tg_username=tag[1:])
        await state.update_data(tg_id=user.id)  # Сохраняем ID в состоянии
        await msg.answer(f"ID пользователя {tag} найден: {user.id}. Теперь укажите его роль ('администратор', 'координатор', 'скаут', 'non-role').", reply_markup=kb.role_kb)
        await state.set_state(RegisterState.waiting_for_role)  # Переходим к следующему состоянию
    except:
        await msg.answer(f"⚠️ Не удалось найти пользователя с таким тегом. Убедитесь, что тег указан верно")

@router.message(RegisterState.waiting_for_role)
async def get_role_handler(msg: Message, state: FSMContext):
    role = msg.text.strip()  # Получаем текст сообщения от пользователя

    # Проверяем корректность введенной роли
    valid_roles = ["администратор", "координатор", "скаут", "non-role"]
    if msg.text == "🔙 Назад":
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    if role.lower() not in valid_roles:
        await msg.answer("⚠️ Неверная роль. Укажите одну из: администратор, координатор, скаут или non-role.")
        return

    user_data = await state.get_data()
    user = Users.get(id=user_data.get('tg_id'))
    reply_kb = kb.start_kb
    if role == 'Скаут':
        role = 'scout'
        reply_kb = kb.start_finish_kb
    elif role == 'Координатор':
        role = 'sScout'
        reply_kb = kb.coord_start_kb
    elif role == 'Администратор':
        role = 'admin'
        reply_kb = kb.admin_start_kb
    else:
        role = 'non-role'
    user.role = role
    user.save()

    await msg.answer(f"Пользователь обновлен с ролью: {role}.", reply_markup=kb.admin_start_kb)
    await msg.bot.send_message(chat_id=user.id, text=f"🎉 Вам обновили роль, ваша роль {role}", reply_markup=reply_kb)
    await state.clear()  # Сбрасываем состояние

@router.message(lambda msg: msg.text == '⚙️ Новая карта зон')
async def set_map_info(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'admin':
        await msg.answer('Отправьте JSON файл зон, сгенерированный с Яндекс карт\nСсылка: https://yandex.ru/map-constructor', reply_markup=kb.admin_back_kb)
        await state.set_state(LoadMapState.waiting_for_file)
    else:
        await msg.answer("🚫 Вы не имеете прав на это действие!")

@router.message(LoadMapState.waiting_for_file)
async def handle_json_file(msg: Message, state: FSMContext):
    if msg.text == "🔙 Назад":
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.admin_start_kb)
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
                        await msg.answer("⚠️ Не удалось декодировать файл как JSON. Пожалуйста, убедитесь, что файл имеет корректный формат GeoJSON.")
                else:
                    await msg.answer("⚠️ Не удалось загрузить файл.")
    else:
        await msg.answer("⚠️ Пожалуйста, отправьте файл в формате GeoJSON.")

async def process_zones(json_data, msg: Message, state: FSMContext):
    # Очищаем старые данные
    scouts = Users.select()
    for s in scouts:
        if s.zonefk != None:
            await msg.bot.send_message(chat_id=s.id, text="⚠️ Было сделано обновление зон, войдите на слот еще раз!", reply_markup=kb.start_finish_kb)
        s.zonefk = None
        s.save()
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
                await msg.answer("⚠️ Есть зона без описания, перепроверьте файл!", reply_markup=kb.admin_start_kb)
                await state.clear()
                return
            
            if ',' not in zone_name_data:
                await msg.answer("⚠️ Есть зона без деления на АО (должна быть запятая), перепроверьте файл!", reply_markup=kb.admin_start_kb)
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
        
        await msg.answer("Новые данные успешно загружены в базу данных.", reply_markup=kb.admin_start_kb)

    except Exception as e:
        await msg.answer(f"⚠️ Произошла ошибка при обработке данных: {str(e)}")

@router.message(lambda msg: msg.text == '✉️ Отправить задание')
async def handler_create_task(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) in ['sScout', 'admin']:
        await state.set_state(TaskState.waiting_for_task)
        await msg.answer("Отправьте сообщение с заданием, ОБЯЗАТЕЛЬНО в нем должны фигурировать координаты через запятую!", reply_markup=kb.admin_back_kb)
    else:
        await msg.answer("🚫 Вы не имеете прав на это действие!")

@router.message(TaskState.waiting_for_task)
async def handler_send_task(msg: Message, state: FSMContext):
    if msg.text == '🔙 Назад':
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.coord_start_kb)
        await state.clear()
        return
    
    if not msg.text and not msg.caption:
        await msg.answer("⚠️ Это сообщение не содержит текста. Пожалуйста, отправьте текстовое сообщение с координатами.")
        return
    text_of_task = (msg.text or msg.caption).strip()
    point = find_coords(text_of_task)
    if not point:
        await msg.answer("⚠️ Это сообщение не содержит координат. Пожалуйста, отправьте текстовое сообщение с координатами.")
        return

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
        scouts_on_zone = Users.select().where(Users.zonefk == found_zone.id)
        if len(scouts_on_zone) == 0:
            await msg.answer(f"⚠️ На зоне {found_zone.name} нет ни одного активного скаута в данный момент времени.", reply_markup=kb.coord_start_kb)
            await state.clear()
            return
        
        hash_of_task = create_hash_for_task()
        new_task = Task.create(id=hash_of_task, admin_chat=msg.from_user.id, msg_text=text_of_task)
        string_coords = str(point[0]) + ', ' + str(point[1])
        sent_message = await msg.answer(
                f"Ваше сообщение\n{'-'*30}\n<i>{text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')}</i>\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                f"<b>Номер задания: #{new_task.id}\n</b>"
                f"<b>Статус принято:       ❌❌❌</b>\n<b>Статус выполнено:\t❌❌❌</b>",
                parse_mode="HTML"
            )

        # Сохраняем message_id в уже созданной записи
        new_task.msg_status = sent_message.message_id
        new_task.msg_orig = msg.message_id
        new_task.save()

        for s in scouts_on_zone:
            if msg.photo:
                await msg.bot.send_photo(chat_id=s.id, photo=msg.photo[-1].file_id, caption=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')+f"\n#{new_task.id}", reply_markup=kb.reply_markup)
            else:
                await msg.bot.send_message(chat_id=s.id, text=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')+f"\n#{new_task.id}", reply_markup=kb.reply_markup)
    else:
        await msg.answer("⚠️ Точка не принадлежит ни одной зоне!", reply_markup=kb.coord_start_kb)
    await state.clear()

class IsForwardedFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.forward_from or message.forward_from_chat)

@router.message(IsForwardedFilter())
async def handle_forwarded_message(msg: Message):
    if check_permission(msg.from_user.id) in ['sScout', 'admin']:

        if not (msg.text or msg.caption):
            await msg.answer("⚠️ Нет текста или фото.")
            return
        
        text_of_task = msg.text or msg.caption
        point = find_coords(text_of_task)
        if not point:
            await msg.answer("⚠️ Это сообщение не содержит координат. Пожалуйста, отправьте текстовое сообщение с координатами.\n"
                            "координаты должны быть записаны через запятую")
            return
        
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
            scouts_on_zone = Users.select().where(Users.zonefk == found_zone.id)
            if len(scouts_on_zone) == 0:
                await msg.answer(f"⚠️ На зоне {found_zone.name} нет ни одного активного скаута в данный момент времени.", reply_markup=kb.coord_start_kb)
                return

            hash_of_task = create_hash_for_task()
            new_task = Task.create(id=hash_of_task, admin_chat=msg.from_user.id, msg_text=text_of_task)
            string_coords = str(point[0]) + ', ' + str(point[1])
            sent_message = await msg.answer(
                f"Ваше сообщение\n{'-'*30}\n<i>{text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')}</i>\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                f"<b>Номер задания: #{new_task.id}\n</b>"
                f"<b>Статус принято:       ❌❌❌</b>\n<b>Статус выполнено:\t❌❌❌</b>",
                parse_mode="HTML"
            )

            # Сохраняем message_id в уже созданной записи
            new_task.msg_status = sent_message.message_id
            new_task.msg_orig = msg.message_id
            new_task.save()

            for s in scouts_on_zone:
                if msg.photo:
                    await msg.bot.send_photo(chat_id=s.id, photo=msg.photo[-1].file_id, caption=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')+f"\n#{new_task.id}", reply_markup=kb.reply_markup)
                else:
                    await msg.bot.send_message(chat_id=s.id, text=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')+f"#{new_task.id}", reply_markup=kb.reply_markup)
        else:
            await msg.answer("⚠️ Точка не принадлежит ни одной зоне!", reply_markup=kb.coord_start_kb)
    else:
        await msg.answer("🚫 Вы не имеете прав на это действие!")

@router.callback_query()
async def hadle_callback(callback_query: types.CallbackQuery, state: FSMContext):
    id_task = find_task_id(callback_query.message.text or callback_query.message.caption)
    task_object = Task.get(id=id_task)
    cords = find_coords(task_object.msg_text)
    cords_str = str(cords[0]) + ', ' + str(cords[1])

    if callback_query.data == "handler_accept":
        if task_object.scoutfk == None:
            #await callback_query.message.answer(f"Вы приняли задание! #{id_task}")
            task_object.scoutfk = callback_query.from_user.id
            task_object.msg_id_scout = callback_query.message.message_id
            task_object.save()

            if callback_query.message.text:
                await callback_query.message.bot.edit_message_text(
                    chat_id = task_object.scoutfk.id,
                    message_id = task_object.msg_id_scout,
                    text = task_object.msg_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n<b>Вы приняли задание! #{id_task}📌</b>",
                    parse_mode="HTML",
                    reply_markup = kb.reply_markup_done
                )
            else:
                await callback_query.message.bot.edit_message_caption(
                    chat_id = task_object.scoutfk.id,
                    message_id = task_object.msg_id_scout,
                    caption = task_object.msg_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n<b>Вы приняли задание! #{id_task}📌</b>",
                    parse_mode="HTML",
                    reply_markup = kb.reply_markup_done
                )

            try:
                text_of_task = task_object.msg_text
                coords = find_coords(text_of_task)
                string_coords = str(coords[0]) + ', ' + str(coords[1])
                await callback_query.message.bot.edit_message_text(
                chat_id=task_object.admin_chat,
                message_id=task_object.msg_status,
                text=(
                        f"Ваше сообщение\n{'-'*30}\n<i>{text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')}</i>\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                        f"<b>Номер задания: #{task_object.id}\n</b>"
                        f"<b>Статус принято:       ✅✅✅</b>\n<b>Статус выполнено:\t❌❌❌</b>"
                    ),
                parse_mode="HTML"
                )
            except Exception as e:
                print(e)
                return

            await callback_query.bot.send_message(chat_id=task_object.admin_chat, text=f"Ваше задание #{id_task} принято в работу.", reply_to_message_id=task_object.msg_orig, reply_markup=kb.coord_start_kb)
        else:
            await callback_query.message.answer("⚠️ Это задание уже было взято в работу другим скаутом (или вами).")
            return

    if callback_query.data == 'handler_done_task':
        if callback_query.message.text:
            await callback_query.message.bot.edit_message_text(
                chat_id = task_object.scoutfk.id,
                message_id = task_object.msg_id_scout,
                text = task_object.msg_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n#{id_task}\n\n<b>Отправьте фото-подтверждение (можно добавить и текст)📋</b>",
                parse_mode="HTML",
                reply_markup = kb.reply_markup_back
            )
        else:
            await callback_query.message.bot.edit_message_caption(
                chat_id = task_object.scoutfk.id,
                message_id = task_object.msg_id_scout,
                caption = task_object.msg_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n#{id_task}\n\n<b>Отправьте фото-подтверждение (можно добавить и текст)📋</b>",
                parse_mode="HTML",
                reply_markup = kb.reply_markup_back
            )
        await state.update_data(task_object=task_object)
        await state.set_state(DoneTaskState.waiting_for_photo)
    
    if callback_query.data == 'handler_done_back':
        if callback_query.message.text:
            await callback_query.message.bot.edit_message_text(
                chat_id = task_object.scoutfk.id,
                message_id = task_object.msg_id_scout,
                text = task_object.msg_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n<b>Вы приняли задание! #{id_task}📌</b>",
                parse_mode="HTML",
                reply_markup = kb.reply_markup_done
            )
        else:
            await callback_query.message.bot.edit_message_caption(
                chat_id = task_object.scoutfk.id,
                message_id = task_object.msg_id_scout,
                caption = task_object.msg_text.replace(cords_str, '<code>'+cords_str+'</code>') + f"\n<b>Вы приняли задание! #{id_task}📌</b>",
                parse_mode="HTML",
                reply_markup = kb.reply_markup_done
            )
        
        await state.clear()
        return

@router.message(lambda msg: msg.text == '🚀 Выйти на слот')
async def handler_enter_slot(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'scout':
        zones = Zone.select()
        if len(zones) == 0:
            await msg.answer("⚠️ В данный момент в базе данных нет зон", reply_markup=kb.start_finish_kb)
            await state.clear()
            return
        zones_ao = [z.ao for z in zones]
        zones_kb = kb.create_dynamic_keyboard(list(set(zones_ao)))
        zones_kb.keyboard.append([kb.btnBack])
        await msg.answer(f"Выбирете административную область (АО) для выхода на слот.", reply_markup=zones_kb)
        await state.set_state(SlotState.waiting_for_ao)
    else:
        await msg.answer("Вы не скаут.")

@router.message(SlotState.waiting_for_ao)
async def handler_choose_ao(msg: Message, state: FSMContext):
    ao = msg.text.strip()
    if ao == '🔙 Назад':
        await msg.answer("Выберите опцию по кнопкам ниже.", reply_markup=kb.start_finish_kb)
        await state.clear()
        return
    ao_bd = [z.ao for z in Zone.select()]
    if ao not in ao_bd:
        await msg.answer("⚠️ Вы выбрали несуществующую АО! Пользуйтесь клавиатурой", reply_markup=kb.start_finish_kb)
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
        zone_object.status = 'active'
        user_scout = Users.get(id=msg.from_user.id)
        user_scout.zonefk = zone_object.id
        zone_object.save()
        user_scout.save()
        await msg.answer(f"Вы вышли на слот {zone_msg}", reply_markup=kb.start_finish_kb)
        await state.clear()
    except:
        await msg.answer(f"⚠️ Вы выбрали зону не из списка, попробуйте еще раз.")

@router.message(lambda msg: msg.text == "🏠 Уйти со слота")
async def handler_exit_slot(msg: Message, state: FSMContext):
    await state.clear()
    if check_permission(msg.from_user.id) == 'scout':
        user = Users.get(id=msg.from_user.id)
        if not user.zonefk:
            await msg.answer("⚠️ Вы еще не вышли на слот.")
            return
        user.zonefk = None
        user.save()
        await msg.answer("Вы вышли со слота.", reply_markup=kb.start_finish_kb)

@router.message(DoneTaskState.waiting_for_photo)
async def handler_get_task(msg: Message, state: FSMContext):
    data = await state.get_data()
    task_object = data.get("task_object")
    text_of_task = task_object.msg_text
    coords = find_coords(text_of_task)
    string_coords = str(coords[0]) + ', ' + str(coords[1])

    if not msg.photo:
        await msg.answer("⚠️ Вы не прикрепили фото, пожалуйста прикрепите фото.")
        return
    else:
        await msg.answer(f"Ваши результаты по заданию #{task_object.id} отправлены координатору ✅", reply_markup=kb.start_finish_kb, reply_to_message_id=task_object.msg_id_scout)
        await msg.bot.copy_message(chat_id=task_object.admin_chat, from_chat_id=msg.chat.id, message_id=msg.message_id, reply_to_message_id=task_object.msg_orig)
        await msg.bot.edit_message_text(
            chat_id=task_object.admin_chat,
            message_id=task_object.msg_status,
            text=(
                f"Ваше сообщение\n{'-'*30}\n`{text_of_task.replace(string_coords, '<code>'+string_coords+'</code>')}`\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                f"<b>Номер задания: #{task_object.id}</b>\n"
                f"<b>Статус принято:       ✅✅✅</b>\n<b>Статус выполнено:\t✅✅✅</b>"
                ),
            parse_mode="HTML"
            )
        try:
            await msg.bot.edit_message_text(
                chat_id=task_object.scoutfk.id,
                message_id=task_object.msg_id_scout,
                text=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>') + f'\n\n<b>Задание #{task_object.id} выполнено🎖️</b>',
                parse_mode="HTML",
                reply_markup=None
            )
        except:
            await msg.bot.edit_message_caption(
                chat_id=task_object.scoutfk.id,
                message_id=task_object.msg_id_scout,
                caption=text_of_task.replace(string_coords, '<code>'+string_coords+'</code>') + f'\n\n<b>Задание #{task_object.id} выполнено🎖️</b>',
                parse_mode="HTML",
                reply_markup=None
            )
        await msg.bot.send_message(chat_id=task_object.admin_chat, text=f"Задание #{task_object.id} выполнено скаутом.")

        Task.delete().where(Task.id == task_object.id).execute()
        await state.clear()
    
    