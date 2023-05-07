from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentTypes
import aiogram.utils.markdown as fmt
from bot_create import fsm_alert, bot
from bot_bx import bx_create_smart
from bot_sql import sql_get_division, sql_get_user, sql_get_cashbox, sql_create_smart
from handlers.other import other_user_check, other_images_to_base64, other_images_packing
from config import settings


async def contacting_start(message: types.Message):
    """ Начало обращения инцидент, запрашиваем подразделение """
    await fsm_alert.start.set()
    mark_menu_main = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["Инцидент", "ОРП", "Консультация", "Заявка на расходование ДС"]
    mark_menu_main.add(*buttons)
    await message.answer(f"Выберите тип обращения", reply_markup=mark_menu_main)


async def contacting_get_type(message: types.Message, state: FSMContext):
    """ Начало обращения инцидент, запрашиваем подразделение """
    await state.update_data(images={})
    if message.text == "Инцидент" or message.text == "Консультация" or \
    message.text == "ОРП" or message.text == "Заявка на расходование ДС":
        await fsm_alert.division.set()
        await state.update_data(type=message.text)
        if message.text == "Инцидент":
            await state.update_data(id_type='160')
        elif message.text == "Консультация":
            await state.update_data(id_type='178')
        elif message.text == "ОРП":
            await state.update_data(id_type='170')
        elif message.text == "Заявка на расходование ДС":
            await state.update_data(id_type='194')
        division = sql_get_division(message.from_user.id)
        await state.update_data(division_select=division)
        mark_division = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        mark_division.add(*division)
        await message.answer("Выберите подразделение", reply_markup=mark_division)
    else:
        await message.answer("Выберите из предложеного списка")


async def contacting_get_division(message: types.Message, state: FSMContext):
    """ Запрашиваем краткое описание инцидент"""
    fsm_data_user = await state.get_data()
    if message.text in fsm_data_user['division_select']:
        await fsm_alert.description.set()
        await state.update_data(division=message.text)
        if fsm_data_user['type'] == 'ОРП':        
            await fsm_alert.cashbox.set()
            cashbox = sql_get_cashbox(message.text)
            await state.update_data(cashbox_select=cashbox)
            mark_cashbox = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            mark_cashbox.add(*cashbox)
            await message.answer("Выберите кассу", reply_markup=mark_cashbox)
        elif fsm_data_user['type'] == 'Заявка на расходование ДС':
            await fsm_alert.defective.set()
            await message.answer("Номер заявки на расходование ДC", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("Кратко опишите суть проблемы", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите из предложеного списка")
        

async def contacting_get_cashbox(message: types.Message, state: FSMContext):
    fsm_data_user = await state.get_data()
    if message.text in fsm_data_user['cashbox_select']:
        await state.update_data(description=message.text)
        await fsm_alert.confirm.set()
        await contacting_confirm(message, state)
    else:
        await message.answer("Выберите из предложеного списка")
        

async def contacting_get_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await fsm_alert.confirm.set()  
    if message.content_type == 'photo' or message.content_type == 'document':    
        fsm_data_user = await state.get_data()
        fsm_data_user['images'].update(await other_images_to_base64(message))
        fsm_data_user.update({'count_images': f"{len(fsm_data_user['images'])}"})
        await state.set_data(fsm_data_user)
        await state.update_data(description=message.caption)
        await contacting_confirm(message, state)
    else:
        await contacting_confirm(message, state)


async def contacting_defective(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await fsm_alert.question.set()
    mark_defective = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*["Да", "Нет"])
    await message.answer("Брак или нет", reply_markup=mark_defective)  


async def contacting_question(message: types.Message, state: FSMContext):
    if message.text == "Да":
        await fsm_alert.images.set()
        mark_confirm = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*["Завершить", "Сбросить"])
        await message.answer("Приложите фото, после нажмите кнопку Завершить, или Сбросить", reply_markup=mark_confirm)
    elif message.text == "Нет":
        await fsm_alert.confirm.set()
        await contacting_confirm(message, state)
    else:
        await message.answer("Выберите из предложеного списка")
        

async def contacting_images(message: types.Message, state: FSMContext):
    if message.content_type == 'photo' or message.content_type == 'document':    
        fsm_data_user = await state.get_data()
        fsm_data_user['images'].update(await other_images_to_base64(message))
        fsm_data_user.update({'count_images': f"{len(fsm_data_user['images'])}"})
        await state.set_data(fsm_data_user)
        mark_confirm = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*["Завершить", "Сбросить"])
        # await state.update_data(count_images=len(fsm_data_user['images']))
        await message.answer(f"Приложенно {fsm_data_user['count_images']} фото", reply_markup=mark_confirm)
    elif message.text == 'Завершить':
        await fsm_alert.confirm.set()
        await contacting_confirm(message, state)
    elif message.text == 'Сбросить':
        await state.finish()
        await contacting_start(message)
    else:
        await message.answer("Приложите фото, после нажмите кнопку Завершить, или Сбросить")


async def contacting_confirm(message: types.Message, state: FSMContext):
    """ Проверяем введенные данные """
    fsm_data_user = await state.get_data()
    mark_confirm = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["Подтвердить", "Отменить"]
    mark_confirm.add(*buttons)
    
    if fsm_data_user['images'] == {}:
        await fsm_alert.create.set()
        confirm_without_sh = fmt.text(fmt.bold("Тип обращения: "), fmt.escape_md(f"{fsm_data_user['type']}\n"),
                            fmt.bold("Подразделение: "), fmt.escape_md(f"{fsm_data_user['division']}\n"),
                            fmt.bold("Описание: "), fmt.escape_md(f"{fsm_data_user['description']}"), sep='')
        await message.answer(confirm_without_sh, reply_markup=mark_confirm)

    elif fsm_data_user['images'] != {}:
        await fsm_alert.create.set()
        confirm_with_sh = fmt.text(fmt.bold("Тип обращения: "), fmt.escape_md(f"{fsm_data_user['type']}\n"),
                            fmt.bold("Подразделение: "), fmt.escape_md(f"{fsm_data_user['division']}\n"),
                            fmt.bold("Описание: "), fmt.escape_md(f"{fsm_data_user['description']}\n"),
                            fmt.bold("Изображения: "), fmt.escape_md(f"{fsm_data_user['count_images']}"), sep='')
        await message.answer(confirm_with_sh, reply_markup=mark_confirm)


""" Регистрируем обрашение инцидент в BX и отпраляем сообшение об успехе в чат """
async def contacting_create(message: types.Message, state: FSMContext):    
    if message.text == "Подтвердить":    
        fsm_data_user = await state.get_data()
        sql_data_user = sql_get_user(message.from_user.id)
        bx_param = f"{fsm_data_user['division']}\n{sql_data_user[0]}\n\
                     {sql_data_user[1]}\n{fsm_data_user['type']}\n\
                     {fsm_data_user['description']}"
        images = await other_images_packing(fsm_data_user['images'])
        result = await bx_create_smart(fsm_data_user['division'], bx_param, sql_data_user[0], fsm_data_user['id_type'], images)
        bx_markup = types.InlineKeyboardMarkup(row_width=2)
        bx_url = types.InlineKeyboardButton('Обращение в битриксе', f"{settings.BX_URL_PROCESS}{result['item']['id']}/")
        bx_markup.add(bx_url)  
        if fsm_data_user['type'] == 'ОРП':
            await message.answer(fmt.escape_md(f"Зарегистрировано обращение от\n{fsm_data_user['division']}, проблема с ОРП\n{fsm_data_user['description']}\nОжидайте, техническая поддержка с вами свяжется"), reply_markup=bx_markup)
            msg = await bot.send_message(settings.BOT_CHATSEND, fmt.escape_md(f"Зарегистрировано обращение от\n{fsm_data_user['division']}, проблема с ОРП\n{fsm_data_user['description']}\nОжидайте, техническая поддержка с вами свяжется"), reply_markup=bx_markup)
            sql_create_smart(result['item']['id'], msg.message_id)
        else:
            await message.answer(fmt.escape_md(f"Зарегистрировано обращение от\n{fsm_data_user['division']}\nОжидайте, техническая поддержка с вами свяжется"), reply_markup=bx_markup)
            msg = await bot.send_message(settings.BOT_CHATSEND,fmt.escape_md(f"Зарегистрировано обращение от\n{fsm_data_user['division']}\nОжидайте, техническая поддержка с вами свяжется"), reply_markup=bx_markup)
            sql_create_smart(result['item']['id'], msg.message_id)
        await state.finish()
        await other_user_check(message, state)
    elif message.text == "Отменить":
        await state.finish()
        await other_user_check(message, state)
    
    
async def get_chat_id(message: types.Message):
    await bot.send_message('-', f"Чат ID группы ", fmt.bold(f"{message.chat.id}"))

    
def alert_handlers_registration(dp: Dispatcher):
    dp.register_message_handler(contacting_get_type, state=fsm_alert.start)
    dp.register_message_handler(contacting_get_division, state=fsm_alert.division)
    dp.register_message_handler(contacting_get_cashbox, state=fsm_alert.cashbox)
    dp.register_message_handler(contacting_get_description, content_types=ContentTypes.PHOTO | ContentTypes.DOCUMENT | ContentTypes.TEXT, state=fsm_alert.description)
    dp.register_message_handler(contacting_defective, state=fsm_alert.defective)
    dp.register_message_handler(contacting_question, state=fsm_alert.question)    
    dp.register_message_handler(contacting_images, content_types=ContentTypes.PHOTO | ContentTypes.DOCUMENT | ContentTypes.TEXT, state=fsm_alert.images)    
    dp.register_message_handler(contacting_confirm, state=fsm_alert.confirm)
    dp.register_message_handler(contacting_create, state=fsm_alert.create)
    # dp.register_message_handler(get_chat_id, commands="chat")
    
    