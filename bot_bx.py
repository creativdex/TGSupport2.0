import base64
from datetime import date, timedelta
from fast_bitrix24 import BitrixAsync
from config import settings

whbitrix = settings.BX_WH_OUT
bx = BitrixAsync(whbitrix)


""" Создание процесса """
async def bx_create_smart(title, text, name, id_type, images = ''):
    method = 'crm.item.add'   
    params = {'entityTypeId' : '184', 'fields': {'title': f'{title}', 'createdBy': '466', 'ufCrm10_1644911192216' : id_type,
              'ufCrm10_1644926802': f'{date.today()}', 'ufCrm10_1644927739266' : '162', 'ufCrm10_1644926433' : text,
              'ufCrm10_1651723524' : name, 'ufCrm10_1644926079790': images }}
    res = await bx.call(method, params)
    return res


""" Получение элемента процесса """
async def bx_get_smart(smart_id, elem_id):
    res = await bx.call('crm.item.get', {'entityTypeId': smart_id, 'id' : elem_id})
    return res

async def bx_list_smart(smart_id, days):
    """ 
    Получение списка элементов процессов 

    Параметры:
    : ID смарт процесса 
    : Кол-во дней
    """
    result= []
    count = 0
    while True:
        res = await bx.call('crm.item.list', {'entityTypeId': smart_id, 'select' : ['ufCrm10_1644926802', 'id', 'assignedById', 'title', 
                      'ufCrm10_1644911192216', 'ufCrm10_1651723524'], 
                      'filter' : {'>createdTime' : date.today() - timedelta(days=days)}, 'start': count})
        if len(res['items']) == 0:
            break
        result.extend(res['items'])
        count += 50
    return result

""" Загрузка файла на диск """
async def upload_file_bx(file):
    res = await bx.call('disk.folder.uploadfile', {'id': settings.BX_FOLDERID,
                        'data' : {'NAME' : 'img_send_bot.png'}, 'fileContent': file, 'generateUniqueName': 'true'})
    return res

""" Прикрипления файла с диск к задаче """
async def attach_file_bx(task_id, file_id):
    await bx.call('tasks.task.files.attach', {'taskId': task_id, 'fileId' : file_id})

""" Кодирование изображения в base64 """    
def to_base_bx(file):
    with open(file, "rb") as b_file:
        b_file_data = b_file.read()
        b64_file_data = base64.b64encode(b_file_data)
        b64_mesage = b64_file_data.decode('utf-8')
        return b64_mesage
