from aiogram.fsm.state import State, StatesGroup

class RegisterState(StatesGroup):
    waiting_for_role = State()
    waiting_for_telegram_tag = State()

class LoadMapState(StatesGroup):
    waiting_for_file = State()

class TaskState(StatesGroup):
    waiting_for_task = State()

class SlotState(StatesGroup):
    waiting_for_ao = State()
    waiting_for_zone = State()
    waiting_for_submit = State()

class DoneTaskState(StatesGroup):
    waiting_for_photo = State()

class CoordinatorState(StatesGroup):
    waiting_for_tag = State()
    waiting_for_caption = State()
    waiting_for_reason = State()