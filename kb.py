from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

btnBack = KeyboardButton(text="Назад")

only_back_kb = ReplyKeyboardMarkup(
    keyboard=[[btnBack]],
    resize_keyboard=True
)

button1 = KeyboardButton(text="Выйти на слот")
button2 = KeyboardButton(text="Уйти со слота")
button3 = KeyboardButton(text="Мои задания")

btnScout = KeyboardButton(text="Скаут")
btnsScout = KeyboardButton(text="Координатор")
btnAdmin = KeyboardButton(text="Администратор")
btnNoRole = KeyboardButton(text="non-role")

btnAdmin1 = KeyboardButton(text="Назначить")
btnAdmin2 = KeyboardButton(text="Новая карта зон")

btnCoordinator = KeyboardButton(text="Отправить задание")

coord_start_kb = ReplyKeyboardMarkup(
    keyboard=[[btnCoordinator]],
    resize_keyboard=True
)

admin_start_kb = ReplyKeyboardMarkup(
    keyboard=[[btnAdmin1, btnAdmin2]],
    resize_keyboard=True
)

admin_back_kb = ReplyKeyboardMarkup(
    keyboard=[[btnBack]],
    resize_keyboard=True
)

role_kb = ReplyKeyboardMarkup(
    keyboard=[[btnScout, btnsScout, btnAdmin, btnNoRole, btnBack]],
    resize_keyboard=True
)

start_finish_kb = ReplyKeyboardMarkup(
    keyboard=[[button1, button2, button3]],
    resize_keyboard=True,
)

zones_kb = ReplyKeyboardMarkup(
    keyboard=[[]],
    resize_keyboard=True,
)

task_list_kb = ReplyKeyboardMarkup(
    keyboard=[[]],
    resize_keyboard=True,
)

reply_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Принять задание", callback_data="handler_accept")]
])