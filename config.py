import requests   #токен бота и вебхука битрикса
TOKEN = 
BITRIX_WEBHOOK_URL = 
#юзернейм менеджера и бота, чтобы можно было отправлять им сообщения
manager_username ="@Bobo_76"
bot_username = "calculator_tecnotoj_bot"

# dict для сопоставления полей из бота и битрикса
BITRIX_FIELDS = {
    "title": "TITLE",
    "type": "TYPE_ID",
    "stage": "STAGE_ID",
    "price": "OPPORTUNITY",
    "phone": "UF_CRM_1739701799",
    "course": "UF_CRM_1739701903",
    "tariff_name": "UF_CRM_1739701953"
    #"referral": "UF_CRM_1740017868"
}

# dict для  courses и tariffs
"""courses = {
    "course1": "Wileberiser",
    "course2": "OZON",
    "course3": "AVITO",
    "course4": "YANDEX MARKAT"
}
"""




def get_products():
    response = requests.get(BITRIX_WEBHOOK_URL + "crm.product.list")
    
    if response.status_code == 200:
        data = response.json()
        
        if "result" in data:
            return {f"product{i+1}": product["NAME"] for i, product in enumerate(data["result"])}
    
    return {}  

# courses az bitriz ба bot мегузорем
courses = get_products()

# dict для  tariffs
tariffs = {
    "tariff1": {"name": "Основной", "price": 500},
    "tariff2": {"name": "Стандарт", "price": 1000},
    "tariff3": {"name": "Премиум", "price": 1500},
    "tariff4": {"name": "VIP", "price": 2000}
}
#dict for bloger  бот создаёт рефирални силка толко для блогер 
bloggers = {
    "habibulo": 0,
    "mirzo": 0,
    "muboriz": 0,
    "bobo": 0,
    "jamol": 0
}
"""def get_products_with_prices():
    response = requests.get(BITRIX_WEBHOOK_URL + "crm.product.list")
    
    if response.status_code == 200:
        data = response.json()
        
        if "result" in data:
            return {f"product{i+1}": product["PRICE"] for i, product in enumerate(data["result"])}
    
    return {}  

# narkh az bitrix ба tariffs ба bot мегузорем
tariffs = get_products_with_prices()"""


