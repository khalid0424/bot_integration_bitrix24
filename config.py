# токен бота и вебхука битрикса
TOKEN = 
BITRIX_WEBHOOK_URL = 
#юзернейм менеджера и бота, чтобы можно было отправлять им сообщения
manager_username ="@Bobo_76"
bot_username = "@calculator_tecnotoj_bot"

# dict для сопоставления полей из бота и битрикса
BITRIX_FIELDS = {
    "title": "TITLE",
    "type": "TYPE_ID",
    "stage": "STAGE_ID",
    "price": "OPPORTUNITY",
    "phone": "UF_CRM_1739701799",
    "course": "UF_CRM_1739701903",
    "tariff_name": "UF_CRM_1739701953",
    "referral": "UF_CRM_1739702082"
}

# dict для  courses и tariffs
courses = {
    "course1": "Wileberiser",
    "course2": "OZON",
    "course3": "AVITO",
    "course4": "YANDEX MARKAT"
}

tariffs = {
    "tariff1": {"name": "Основной", "price": 500},
    "tariff2": {"name": "Стандарт", "price": 1000},
    "tariff3": {"name": "Премиум", "price": 1500},
    "tariff4": {"name": "VIP", "price": 2000}
}
