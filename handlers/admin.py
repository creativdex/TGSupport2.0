from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentTypes
from bot_bx import bx_list_smart
import handlers, pandas as pd
from bot_create import fsm_admin, bot
#from bot_bx import upload_file_bx, attach_file_bx, to_base_bx

async def admin_handlers_start(message: types.Message):
    await fsm_admin.menu.set()
    mark_menu_admin = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["ЧС", "Отчет", "Тест", "Обращение"]
    mark_menu_admin.add(*buttons)
    await message.answer(f"Панель управления", reply_markup=mark_menu_admin)

async def admin_handlers_alert(message: types.Message):
    await handlers.contacting_start(message)

async def admin_handlers_blacklist(message: types.Message, state: FSMContext):
    await fsm_admin.blacklist_cb.set()
    blacklist_markup = types.InlineKeyboardMarkup(row_width=2)
    btn_block = types.InlineKeyboardButton('Заблокировать', callback_data='block')
    btn_unblock = types.InlineKeyboardButton('Разблокировать', callback_data='unblock')
    blacklist_markup.add(btn_unblock, btn_block)  
    await message.answer(f"Черный список", reply_markup=blacklist_markup)

async def admin_callback_blacklist(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    #await bot.send_message(callback_query.from_user.id, f"Заблокировать")
    await bot.edit_message_text('Белый список', callback_query.message.chat.id, callback_query.message.message_id)

async def admin_handlers_report(message: types.Message, state: FSMContext):
    columns1 = {'id':'ID', 'title':'Заголовок', 'ufCrm10_1644911192216':'Тип проблемы', 'ufCrm10_1644926802':'Дата', 
                'ufCrm10_1651723524':'ФИО', 'ufCrm10_1644926433':'Описание', 'assignedById':'Ответственный', 'ufCrm10_1644927739266':'Инцидент касается'}

    assignedById = {'520':'Анастасия Юдина', '270':'Анастасия Индюкова', '566':'Светлана Куклева', 
                    '568':'Елена Пантелеева', '166':'Сергей Варенков', '466':'Проект Менеджер', '50':'Александр Мамаев', '66':'Роман Филиповский'}

    ufCrm10_1644911192216 = {170:'Не провелся/создался ОРП', 178:'Консультация', 
                            160:'Прочие проблемы', 132:'Проблемы с чеком ККМ', 
                            134:'Проблема с закрытием смены', 136:'Проблема с открытием смены',
                            144:'Операции с документами', 146:'Проблемы технического характера',
                            148:'Проблемы со скидкой', 150:'Проблемы с остатками',
                            152:'Проблемы с предоплатой и/или заказом покупателя',
                            154:'Проблемы с пробитием товара', 156:'Не производится оплата',
                            158:'Проблема с Бонусной картой/Бонусами', 172:'Проблема с правами доступа в БД',
                            174:'Проблема с печатью ценников', 176:'Проблема ДС/Кассовый разрыв',
                            180:'Не заархивировались чеки ККМ', 202: 'Проблема с возвратом товаров/возвратом оплаты',
                            194:'Заявка на расходование ДС', 196: 'Проблемы с Интернет-заказами УТ11',
                            198:'Проблемы с QR кодом', 200: 'Распроведение/Пометка на удаление ',
                            }
    report = await bx_list_smart(184, 30)
    df = pd.DataFrame(report)
    df['assignedById'] = df['assignedById'].map(assignedById)
    df['ufCrm10_1644911192216'] = df['ufCrm10_1644911192216'].map(ufCrm10_1644911192216)
    df = df.rename(columns=columns1)
    df.to_excel('report.xlsx')
    await message.reply_document(open('report.xlsx', 'rb'))


def admin_hendlers_registration(dp: Dispatcher):
    dp.register_callback_query_handler(admin_callback_blacklist, state=fsm_admin.blacklist_cb)
    dp.register_message_handler(admin_handlers_blacklist, lambda message: message.text == "ЧС", state=fsm_admin.menu)
    dp.register_message_handler(admin_handlers_alert, lambda message: message.text == "Обращение", state=fsm_admin.menu)
    dp.register_message_handler(admin_handlers_report, lambda message: message.text == "Отчет", state=fsm_admin.menu)
