import logging, ssl
from aiohttp import web
from aiogram import Bot, types, Dispatcher
from aiogram.dispatcher.webhook import get_new_configured_app
from bot_create import dp, bot
from handlers import other, alert, registration, admin
from config import settings

WH_TG = settings.SRV_WH_HOST + settings.BOT_WH_IN
logging.basicConfig(level=logging.INFO)
routes = web.RouteTableDef()


# Получаем обновления от телеграма
# @routes.post(settings.BOT_WH_IN)
# async def tg_update(req: web.Request):
#     upds = [types.Update(**(await req.json()))]
#     Bot.set_current(bot)
#     Dispatcher.set_current(dp)
#     await dp.process_updates(upds)
#     return web.Response(text="OK")
#
#
# # Проверка правильности вебхука телеграма
# @routes.post(settings.BOT_WH_IN)
# async def bx_update(req: web.Request):
#     await other.status_send(req.query["id"], req.query["status"])
#     return web.Response(text="OK")


# Проверка правильности вебхука телеграма
@routes.get("/webhook")
async def webhook(request):
    webhook_info = await bot.get_webhook_info()
    return web.Response(text=f"Webhook = {webhook_info.url}")


# Скрипт для получения сертификата SSL от центра сертификации
@routes.get("/.well-known/pki-validation/50C50CBD656BC59D77322FCD2AEE2632.txt")
async def sslcert(request):
    return web.FileResponse("./Web/50C50CBD656BC59D77322FCD2AEE2632.txt")


async def on_startup(app):
    logging.warning("Hi!")
    other.other_handlers_registration(dp)
    admin.admin_hendlers_registration(dp)
    alert.alert_handlers_registration(dp)
    registration.register_handlers_registration(dp)

    webhook = await bot.get_webhook_info()
    if webhook.url != WH_TG:
        if not webhook.url:
            await bot.delete_webhook()
        await bot.set_webhook(WH_TG)


async def on_shutdown(app):
    await bot.delete_webhook()
    logging.warning("Bye!")


print(settings.SRV_SSL_BUNDLE)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_verify_locations(settings.SRV_SSL_BUNDLE)
context.load_cert_chain(certfile=settings.SEV_SSL_CERT, keyfile=settings.SRV_SSL_KEY)


app = web.Application()
app = get_new_configured_app(dispatcher=dp, path=settings.BOT_WH_IN)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.add_routes(routes)

web.run_app(app, port=settings.SRV_PORT, ssl_context=context)
