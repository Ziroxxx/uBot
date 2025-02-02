from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

btnBack = KeyboardButton(text="🔙 Назад")

only_back_kb = ReplyKeyboardMarkup(
    keyboard=[[btnBack]],
    resize_keyboard=True
)

btnStart = KeyboardButton(text="Старт")

button1 = KeyboardButton(text="🚀 Выйти на слот")
button2 = KeyboardButton(text="🏠 Уйти со слота")
button3 = KeyboardButton(text="➕ Добавить слот")

btnCoordinatorStart = KeyboardButton(text="🚀 Выйти на смену")
btnCoordinatorEnd = KeyboardButton(text="🏠 Уйти со смены")
btnCoordinatorSearch = KeyboardButton(text="🔎 Список")

btnCoordinatorDelegate = InlineKeyboardButton(text="Делегировать", callback_data="handler_delegate")
btnCoordinatorDeny = InlineKeyboardButton(text="Отменить", callback_data="handler_deny")
btnCoordinatorBack = InlineKeyboardButton(text="Назад", callback_data="handler_coord_back")
btnCoordinatorDenyBack = InlineKeyboardButton(text="Назад", callback_data="handler_deny_back")

btnYes = KeyboardButton(text='Да')
btnNo = KeyboardButton(text='Нет')

btnScout = KeyboardButton(text="Скаут")
btnCoordinator = KeyboardButton(text="Координатор")
btnAdmin = KeyboardButton(text="Администратор")
btnBoss = KeyboardButton(text='Босс')
btnsScout = KeyboardButton(text='СИТ')
btnNoRole = KeyboardButton(text="non-role")

btnAdmin1 = KeyboardButton(text="🔑 Назначить")
btnAdmin2 = KeyboardButton(text="⚙️ Новая карта зон")

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

submit_kb = ReplyKeyboardMarkup(
    keyboard=[[btnYes, btnNo]],
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
    keyboard=[[btnScout, btnCoordinator], [btnAdmin, btnsScout], [btnBoss, btnNoRole], [btnBack]],
    resize_keyboard=True
)

start_finish_kb = ReplyKeyboardMarkup(
    keyboard=[[button1, button2]],
    resize_keyboard=True,
)

scout_work_kb = ReplyKeyboardMarkup(
    keyboard=[[button3, button2]],
    resize_keyboard=True
)

task_list_kb = ReplyKeyboardMarkup(
    keyboard=[[]],
    resize_keyboard=True,
)

coordinator_kb = ReplyKeyboardMarkup(
    keyboard=[[btnCoordinatorStart, btnCoordinatorEnd, btnCoordinatorSearch]],
    resize_keyboard=True
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

reply_markup_problem = InlineKeyboardMarkup(
    inline_keyboard = [[btnCoordinatorDelegate, btnCoordinatorDeny]]
)

reply_markup_problem_back = InlineKeyboardMarkup(
    inline_keyboard = [[btnCoordinatorBack]]
)

reply_markup_deny_back = InlineKeyboardMarkup(
    inline_keyboard = [[btnCoordinatorDenyBack]]
)