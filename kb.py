from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

btnBack = KeyboardButton(text="🔙 Назад")

only_back_kb = ReplyKeyboardMarkup(
    keyboard=[[btnBack]],
    resize_keyboard=True
)

btnStart = KeyboardButton(text="Старт")

button1 = KeyboardButton(text="🚀 Выйти на слот")
button2 = KeyboardButton(text="🏠 Уйти со слота")

btnScout = KeyboardButton(text="Скаут")
btnsScout = KeyboardButton(text="Координатор")
btnAdmin = KeyboardButton(text="Администратор")
btnNoRole = KeyboardButton(text="non-role")

btnAdmin1 = KeyboardButton(text="🔑 Назначить")
btnAdmin2 = KeyboardButton(text="⚙️ Новая карта зон")

btnCoordinator = KeyboardButton(text="✉️ Отправить задание")

def create_dynamic_keyboard(button_texts, max_row_width=20):
    if not button_texts:  # Проверяем, чтобы список кнопок не был пустым
        raise ValueError("Список кнопок пуст. Невозможно создать клавиатуру.")
    
    keyboard_rows = []  # Список строк кнопок
    current_row = []  # Текущая строка кнопок

    for text in button_texts:
        if sum(len(btn.text) for btn in current_row) + len(current_row) + len(text) > max_row_width:
            keyboard_rows.append(current_row)
            current_row = []

        current_row.append(KeyboardButton(text=text))
    
    # Добавляем оставшиеся кнопки
    if current_row:
        keyboard_rows.append(current_row)

    return ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)

start_kb = ReplyKeyboardMarkup(
    keyboard=[[btnStart]],
    resize_keyboard=True
)

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
    keyboard=[[btnScout, btnsScout], [btnAdmin, btnNoRole], [btnBack]],
    resize_keyboard=True
)

start_finish_kb = ReplyKeyboardMarkup(
    keyboard=[[button1, button2]],
    resize_keyboard=True,
)

task_list_kb = ReplyKeyboardMarkup(
    keyboard=[[]],
    resize_keyboard=True,
)

reply_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Принять задание", callback_data="handler_accept")]
])

reply_markup_done = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Выполнил", callback_data="handler_done_task")]
])

reply_markup_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="handler_done_back")]
])