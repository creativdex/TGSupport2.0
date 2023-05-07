from typing import List
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from bot_bx import to_base_bx
from bot_create import fsm_other, bot
from bot_sql import sql_get_message, sql_complete_smart, sql_check_user
import handlers, time
from config import settings


async def other_user_check(message: types.Message, state: FSMContext):  
    """ Проверка пользователя на уровень доступа"""
    await state.finish()
    user: List = sql_check_user(message.from_user.id)
    if user == []:
        await handlers.reg_start(message)
    else:
        if user[1] == '0':
            await fsm_other.blocked.set()
            await other_user_blocked(message, state)
        elif user[1] == '1':
            await handlers.contacting_start(message)
        elif user[1] == '2':
            await handlers.admin_handlers_start(message)


async def other_user_blocked(message: types.Message, state: FSMContext):
    """ Оповещение о блокировке """
    user = sql_check_user(message.from_user.id) 
    if user[1] == '0':
        await message.answer(f"Вы заблокированы, обратитесь к Администратору", reply_markup=types.ReplyKeyboardRemove())
    else:
        await state.finish()
        await other_user_check(message, state)


async def other_echo(message: types.Message, state: FSMContext):
    """ Инструкция для старта """
    await state.update_data(msg=message)
    echo_markup = types.InlineKeyboardMarkup(row_width=2)
    echo_markup.add(types.InlineKeyboardButton('Старт', callback_data='start'))  
    await message.answer(f"Для оформления обращения в службу поддержки нажмите на кнопку", reply_markup=echo_markup)
    

async def other_echo_click(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    fsm_data_user = await state.get_data()
    await other_user_check(fsm_data_user['msg'], state)


async def other_image_convert(message: types.Message):
    """ Принимает сообщение с фото или документом и конвертирует его в base64
        Параметры: :obj:`types.Message`
        Возврат: :obj:`base64`
     """
    if message.content_type == 'photo':
        photo = message.photo.pop()
        await photo.download(destination_file=f'{photo.file_unique_id}.png')
        time.sleep(1)
        image = [f'{photo.file_unique_id}.png'], [to_base_bx(f'{photo.file_unique_id}.png')]
        return image
    elif message.content_type == 'document':
        await message.document.download(destination_file=f'{message.document.file_unique_id}.{message.document.mime_subtype}')
        time.sleep(1)
        image = [f'{message.document.file_unique_id}.{message.document.mime_subtype}'], [to_base_bx(f'{message.document.file_unique_id}.{message.document.mime_subtype}')]
        return image
        #await message.answer(f"{message.caption}")


async def other_images_to_base64(message: types.Message):
    """ Принимает сообщение с фото или документом и конвертирует его в base64
        Параметры: :obj:`types.Message`
        Возврат: :obj:`base64`
     """
    if message.content_type == 'photo':
        photo = message.photo.pop()
        await photo.download(destination_file=f'{photo.file_unique_id}.png')
        time.sleep(1)
        return {f'{photo.file_unique_id}.png': to_base_bx(f'{photo.file_unique_id}.png')}
    elif message.content_type == 'document':
        await message.document.download(destination_file=f'{message.document.file_unique_id}.{message.document.mime_subtype}')
        time.sleep(1)
        return {f'{message.document.file_unique_id}.{message.document.mime_subtype}': to_base_bx(f'{message.document.file_unique_id}.{message.document.mime_subtype}')}


async def other_images_packing(*args):
    diction = {}
    for n, img in enumerate(args):
        for n, key in enumerate(img):
            diction.update({str(n): {'file_name': key, 'base64image': img[key]}})
    return diction


async def status_send(id, status):
    """ Отправка статуса обращения в КД """
    msg = sql_get_message(id)
    if msg[1] != 'True':
        if status == 'start':
            await bot.send_message(settings.BOT_CHATSEND, f"Принято в работу 👩🏼‍💻", reply_to_message_id=msg[0])
        elif status == 'complete':
            await bot.send_message(settings.BOT_CHATSEND, f"Решено ✅", reply_to_message_id=msg[0])
            sql_complete_smart(id)


def other_handlers_registration(dp: Dispatcher):
    dp.register_message_handler(other_user_check, chat_type=types.ChatType.PRIVATE, commands="start")
    dp.register_message_handler(other_user_blocked, state=fsm_other.blocked)
    dp.register_message_handler(other_echo, chat_type=types.ChatType.PRIVATE)
    dp.register_callback_query_handler(other_echo_click, lambda callback: callback.data == "start")
