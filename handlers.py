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
            await msg.answer("Вы пока ещё не получили роль.")
    except:
        await msg.answer("Привет! Я зарегистрировал тебя. Дождись, пока руководство выдаст тебе роль внутри бота!\nДля проверки своей роли снова воспользуйся /start")
        Users.create(id=msg.from_user.id, tg_username=msg.from_user.username, role='non-role')

@router.message(lambda msg: msg.text == 'Назначить')
async def register_handler(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'admin':
        await msg.answer("Введите @тег пользователя, права которого вы хотите изменить.", reply_markup=kb.admin_back_kb)
        await state.set_state(RegisterState.waiting_for_telegram_tag)
    else:
        await msg.answer("Вы не имеете прав на это действие!")

@router.message(RegisterState.waiting_for_telegram_tag)
async def get_telegram_tag_handler(msg: Message, state: FSMContext):
    if msg.text == 'Назад':
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    tag = msg.text.strip()
    if not tag.startswith("@"):
        await msg.answer("Тег должен начинаться с '@'. Попробуйте снова.")
        return

    try:
        # Пытаемся получить информацию о пользователе по тегу
        user = Users.get(tg_username=tag[1:])
        await state.update_data(tg_id=user.id)  # Сохраняем ID в состоянии
        await msg.answer(f"ID пользователя {tag} найден: {user.id}. Теперь укажите его роль ('администратор', 'координатор', 'скаут', 'non-role').", reply_markup=kb.role_kb)
        await state.set_state(RegisterState.waiting_for_role)  # Переходим к следующему состоянию
    except:
        await msg.answer(f"Не удалось найти пользователя с таким тегом. Убедитесь, что тег указан верно")

@router.message(RegisterState.waiting_for_role)
async def get_role_handler(msg: Message, state: FSMContext):
    role = msg.text.strip()  # Получаем текст сообщения от пользователя

    # Проверяем корректность введенной роли
    valid_roles = ["администратор", "координатор", "скаут", "non-role"]
    if msg.text == "Назад":
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.admin_start_kb)
        await state.clear()
        return
    if role.lower() not in valid_roles:
        await msg.answer("Неверная роль. Укажите одну из: администратор, координатор, скаут или non-role.")
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
    await msg.bot.send_message(chat_id=user.id, text=f"Вам обновили роль, ваша роль {role}", reply_markup=reply_kb)
    await state.clear()  # Сбрасываем состояние

@router.message(lambda msg: msg.text == 'Новая карта зон')
async def set_map_info(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'admin':
        await msg.answer('Отправьте JSON файл зон, сгенерированный с Яндекс карт\nСсылка: https://yandex.ru/map-constructor', reply_markup=kb.admin_back_kb)
        await state.set_state(LoadMapState.waiting_for_file)
    else:
        await msg.answer("Вы не имеете прав на это действие!")

@router.message(LoadMapState.waiting_for_file)
async def handle_json_file(msg: Message, state: FSMContext):
    if msg.text == "Назад":
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
                        await process_zones(json_data, msg)
                    except json.JSONDecodeError:
                        await msg.answer("Не удалось декодировать файл как JSON. Пожалуйста, убедитесь, что файл имеет корректный формат GeoJSON.")
                else:
                    await msg.answer("Не удалось загрузить файл.")
    else:
        await msg.answer("Пожалуйста, отправьте файл в формате GeoJSON.")

async def process_zones(json_data, msg: Message):
    # Очищаем старые данные
    scouts = Users.select()
    for s in scouts:
        if s.zonefk != None:
            await msg.bot.send_message(chat_id=s.id, text="Было сделано обновление зон, войдите на слот еще раз!", reply_markup=kb.start_finish_kb)
        s.zonefk = None
        s.save()
    Coordinate.delete().execute()  # Удаляем все старые координаты
    Zone.delete().execute()  # Удаляем все старые зоны

    try:
        # Извлекаем данные зон из JSON
        features = json_data.get('features', [])
        
        for feature in features:
            # Получаем имя зоны и координаты
            zone_name = feature['properties']['description']
            coordinates = feature['geometry']['coordinates'][0]  # Получаем список координат

            # Создаём запись для зоны в базе данных
            zone, created = Zone.get_or_create(name=zone_name, status='non-active')

            if created:
                await msg.answer(f"Зона {zone_name} добавлена.")
            
            # Добавляем координаты в таблицу Coordinate
            for coord in coordinates:
                longitude, latitude = coord
                Coordinate.create(longitude=longitude, latitude=latitude, zonefk=zone.id)
        
        await msg.answer("Новые данные успешно загружены в базу данных.")

    except Exception as e:
        await msg.answer(f"Произошла ошибка при обработке данных: {str(e)}")

@router.message(lambda msg: msg.text == 'Отправить задание')
async def handler_create_task(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) in ['sScout', 'admin']:
        await state.set_state(TaskState.waiting_for_task)
        await msg.answer("Отправьте сообщение с заданием, ОБЯЗАТЕЛЬНО в нем должны фигурировать координаты через запятую!", reply_markup=kb.admin_back_kb)
    else:
        await msg.answer("Вы не имеете прав на это действие!")

@router.message(TaskState.waiting_for_task)
async def handler_send_task(msg: Message, state: FSMContext):
    if msg.text == 'Назад':
        await msg.answer("Выберите опцию по кнопкам ниже", reply_markup=kb.coord_start_kb)
        await state.clear()
        return
    
    if not msg.text:
        await msg.answer("Это сообщение не содержит текста. Пожалуйста, отправьте текстовое сообщение с координатами.")
        return
    text_of_task = msg.text.strip()
    point = find_coords(text_of_task)
    if not point:
        await msg.answer("Это сообщение не содержит координат. Пожалуйста, отправьте текстовое сообщение с координатами.")
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
            await msg.answer(f"На зоне {found_zone.name} нет ни одного активного скаута в данный момент времени.", reply_markup=kb.coord_start_kb)
            await state.clear()
            return
        
        new_task = Task.create(id=create_hash_for_task(), admin_chat=msg.from_user.id)
        for s in scouts_on_zone:
            if msg.photo:
                await msg.bot.send_photo(chat_id=s.id, photo=msg.photo[-1].file_id, caption=(msg.caption or msg.text)+f"\n#{new_task.id}", reply_markup=kb.reply_markup)
            else:
                await msg.bot.send_message(chat_id=s.id, text=msg.text+f"#{new_task.id}", reply_markup=kb.reply_markup)

        await msg.answer(f"Ваше сообщение `{text_of_task}` отправлено скаутам на зоне!\n#{new_task.id}", reply_markup=kb.coord_start_kb)
    else:
        await msg.answer("Точка не принадлежит ни одной зоне!", reply_markup=kb.coord_start_kb)
    await state.clear()

class IsForwardedFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.forward_from or message.forward_from_chat)

@router.message(IsForwardedFilter())
async def handle_forwarded_message(msg: Message):
    if not (msg.text or msg.caption):
        await msg.answer("Нет текста или фото.")
        return
    if check_permission(msg.from_user.id) in ['sScout', 'admin']:
        text_of_task = msg.text or msg.caption
        point = find_coords(text_of_task)
        if not point:
            await msg.answer("Это сообщение не содержит координат. Пожалуйста, отправьте текстовое сообщение с координатами.\n"
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
                await msg.answer(f"На зоне {found_zone.name} нет ни одного активного скаута в данный момент времени.", reply_markup=kb.coord_start_kb)
                return

            hash_of_task = create_hash_for_task()
            new_task = Task.create(id=hash_of_task, admin_chat=msg.from_user.id)
            await msg.answer(f"Ваше сообщение `{text_of_task}` отправлено скаутам на зоне!\n#{new_task.id}", reply_markup=kb.coord_start_kb)

            for s in scouts_on_zone:
                if msg.photo:
                    await msg.bot.send_photo(chat_id=s.id, photo=msg.photo[-1].file_id, caption=(msg.caption or msg.text)+f"\n#{new_task.id}", reply_markup=kb.reply_markup)
                else:
                    await msg.bot.send_message(chat_id=s.id, text=msg.text+f"#{new_task.id}", reply_markup=kb.reply_markup)
        else:
            await msg.answer("Точка не принадлежит ни одной зоне!", reply_markup=kb.coord_start_kb)
    else:
        await msg.answer("Вы не имеете прав на это действие!")

@router.callback_query()
async def hadle_callback(callback_query: types.CallbackQuery):
    if callback_query.data == "handler_accept":
        id_task = find_task_id(callback_query.message.text or callback_query.message.caption)
        task_object = Task.get(id=id_task)
        if task_object.scoutfk == None:
            await callback_query.message.answer(f"Вы приняли задание! #{id_task}")
            task_object.scoutfk = callback_query.from_user.id
            task_object.msg_id_scout = callback_query.message.message_id
            task_object.save()

            await callback_query.bot.send_message(chat_id=task_object.admin_chat, text=f"Ваше задание #{id_task} принято в работу.")
        else:
            await callback_query.message.answer("Это задание уже было взято в работу другим скаутом (или вами).")

@router.message(lambda msg: msg.text == 'Выйти на слот')
async def handler_enter_slot(msg: Message, state: FSMContext):
    if check_permission(msg.from_user.id) == 'scout':
        zones = Zone.select()
        zones_list = []
        kb.zones_kb.keyboard.clear()
        zones_list.append(kb.btnBack)
        for z in zones:
            zone_i = KeyboardButton(text=z.name)
            zones_list.append(zone_i)
        kb.zones_kb.keyboard.append(zones_list)
        await msg.answer(f"Выбирете зону для выхода на слот.", reply_markup=kb.zones_kb)
        await state.set_state(SlotState.waiting_for_zone)
    else:
        await msg.answer("Вы не скаут.")

@router.message(SlotState.waiting_for_zone)
async def hadler_start_slot(msg: Message, state: FSMContext):
    if msg.text == "Назад":
        await msg.answer("Добро пожаловать в бота Urent. Выберите опцию, по кнопкам ниже.", reply_markup=kb.start_finish_kb)
        await state.clear()
        return
    try:
        zone_msg = msg.text.strip()
        zone_object = Zone.get(Zone.name == zone_msg)
        zone_object.status = 'active'
        user_scout = Users.get(id=msg.from_user.id)
        user_scout.zonefk = zone_object.id
        zone_object.save()
        user_scout.save()
        await msg.answer(f"Вы вышли на слот {zone_msg}", reply_markup=kb.start_finish_kb)
        await state.clear()
    except:
        await msg.answer("Вы выбрали зону не из списка, попробуйте еще раз используя /enter")

@router.message(lambda msg: msg.text == "Уйти со слота")
async def handler_exit_slot(msg: Message, state: FSMContext):
    await state.clear()
    if check_permission(msg.from_user.id) == 'scout':
        user = Users.get(id=msg.from_user.id)
        if not user.zonefk:
            await msg.answer("Вы еще не вышли на слот.")
            return
        user.zonefk = None
        user.save()
        await msg.answer("Вы вышли со слота.", reply_markup=kb.start_finish_kb)

@router.message(lambda msg: msg.text == "Мои задания")
async def handler_show_tasks(msg: Message, state: FSMContext):
    await state.clear()
    scout_tasks = Task.select().where(Task.scoutfk == msg.from_user.id)
    if scout_tasks:
        task_list = []
        kb.task_list_kb.keyboard.clear()
        task_list.append(kb.btnBack)
        for task in scout_tasks:
            task_i = KeyboardButton(text="#"+str(task.id))
            task_list.append(task_i)
        kb.task_list_kb.keyboard.append(task_list)
        await msg.answer("Выберете выполненую задачу:", reply_markup=kb.task_list_kb)
        await state.set_state(DoneTaskState.waiting_for_task)
    else:
        await msg.answer("У вас нет активных задач!")

@router.message(DoneTaskState.waiting_for_task)
async def handler_get_task(msg: Message, state: FSMContext):
    if msg.text == "Назад":
        await msg.answer("Выберите нужное действие.", reply_markup=kb.start_finish_kb)
        await state.clear()
        return
    try:
        task_object = Task.get(id=msg.text[1:])
        await msg.answer("Прикрепите фото-подтверждение (можно добавить и текст).", reply_markup=kb.only_back_kb)
        await state.update_data(task_object=task_object)
        await state.set_state(DoneTaskState.waiting_for_photo)
    except:
        await msg.answer("Вы выбрали неверное задание! Пользуйтесь клавиатурой")
        return

@router.message(DoneTaskState.waiting_for_photo)
async def handler_get_task(msg: Message, state: FSMContext):
    if msg.text == "Назад":
        await state.set_state(DoneTaskState.waiting_for_task)
        await msg.answer("Выберете выполненую задачу:", reply_markup=kb.task_list_kb)
        return

    data = await state.get_data()
    task_object = data.get("task_object")

    if not msg.photo:
        await msg.answer("Вы не прикрепили фото, пожалуйста прикрепите фото.")
        return
    else:
        await msg.answer("Ваши результаты отправлены координатору", reply_markup=kb.start_finish_kb)
        await msg.bot.forward_message(chat_id=task_object.admin_chat, from_chat_id=msg.chat.id, message_id=msg.message_id)
        await msg.bot.send_message(chat_id=task_object.admin_chat, text=f"Задание #{task_object.id} выполнено скаутом.")

        Task.delete().where(Task.id == task_object.id).execute()
        await state.clear()
    
    