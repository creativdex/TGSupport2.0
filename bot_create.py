from aiogram import Bot, Dispatcher
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from config import settings


tokenTG = settings.BOT_TOKEN
bot = Bot(tokenTG, parse_mode=ParseMode.MARKDOWN_V2)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class fsm_registration(StatesGroup):
    name_first = State()
    name_last = State()
    tel = State()
    city = State()
    confirm = State()

class fsm_alert(StatesGroup):
    start = State()
    division = State()
    cashbox = State()
    description = State()
    defective = State()
    question = State()
    images = State()
    confirm = State()
    create = State()

class fsm_admin(StatesGroup):
    menu = State()
    blacklist_cb = State()
    load_file = State()

class fsm_other(StatesGroup):
    blocked = State()
