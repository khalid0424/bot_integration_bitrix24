import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from refral import TOKEN ,BITRIX_WEBHOOK_URL


bot = telebot.TeleBot(TOKEN)

user_states = {}
referrals = {}

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

def generate_referral_link(user_id):
    return f"https://t.me/your_bot?start=ref{user_id}"

def create_courses_keyboard():
    keyboard = InlineKeyboardMarkup()
    for course_id, course_name in courses.items():
        keyboard.add(InlineKeyboardButton(course_name, callback_data=f"course_{course_id}"))
    return keyboard

def create_payment_method_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Онлайн", callback_data="payment_online"),
        InlineKeyboardButton("Менеджер", callback_data="payment_manager")
    )
    return keyboard

def create_tariffs_keyboard(course_id):
    keyboard = InlineKeyboardMarkup()
    for tariff_id, tariff_info in tariffs.items():
        button_text = f"{tariff_info['name']} - {tariff_info['price']} рубл"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"tariff_{course_id}_{tariff_id}"))
    return keyboard

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("ref"): 
        referrer_id = args[1][3:]
        if referrer_id.isdigit():
            referrer_id = int(referrer_id)
            if referrer_id != user_id: 
                referrals.setdefault(referrer_id, 0)
                referrals[referrer_id] += 1 

    referral_link = generate_referral_link(user_id)
    user_states[user_id] = {"referral_link": referral_link}

    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = telebot.types.KeyboardButton(text="Отправьте свой номер телефона", request_contact=True)
    keyboard.add(button_phone)

    bot.send_message(
        message.chat.id,
        "Привет! Пожалуйста, отправьте свой номер телефона:",
        reply_markup=keyboard
    )

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        user_states[user_id] = {}
    
    user_states[user_id]["phone"] = message.contact.phone_number

    bot.send_message(
        message.chat.id,
        "Пожалуйста, выберите курс:",
        reply_markup=create_courses_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def course_callback(call):
    user_id = call.from_user.id
    course_id = call.data.split("_")[1]
    user_states[user_id]["selected_course"] = course_id

    bot.edit_message_text(
        " Выберите метод оплаты:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=create_payment_method_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
def payment_method_callback(call):
    user_id = call.from_user.id
    payment_method = call.data.split("_")[1]

    if payment_method == "manager":
        bot.edit_message_text(
            " Свяжитесь с менеджером: @unknownnnsu",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        course_id = user_states[user_id]["selected_course"]
        bot.edit_message_text(
            "Пожалуйста, выберите тариф:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_tariffs_keyboard(course_id)
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tariff_"))
def tariff_callback(call):
    user_id = call.from_user.id
    _, course_id, tariff_id = call.data.split("_")

    if "phone" not in user_states[user_id]:
        bot.send_message(user_id, " Пожалуйста, введите номер телефона!")
        return


    deal_data = {
    "fields": {
        "TITLE": f"Покупка курса - {courses[course_id]}",
        "TYPE_ID": "GOODS",
        "STAGE_ID": "NEW",
        "OPPORTUNITY": int(tariffs[tariff_id]["price"]),
        "UF_CRM_1739701799": user_states[user_id]["phone"],  
        "UF_CRM_1739701903": courses[course_id],  
        "UF_CRM_1739701953": tariffs[tariff_id]["name"],  
        "UF_CRM_1739702082": user_states[user_id]["referral_link"]  
    }
}



    response = requests.post(f"{BITRIX_WEBHOOK_URL}/crm.deal.add", json=deal_data)


    if response.status_code == 200:
        bot.send_message(user_id, "Спасибо за покупку, ждите подтверждения платежа.")
    else:
        bot.send_message(user_id, f" Ошибка! Код:")

@bot.message_handler(commands=["refraliman"])
def show_referral_link(message):
    user_id = message.from_user.id
    referral_link = user_states.get(user_id, {}).get("referral_link", " У вас нет реферала!")

    bot.send_message(user_id, f" Ваша реферальная ссылка:\n{referral_link}")

@bot.message_handler(commands=["ovardam"])
def show_referral_count(message):
    user_id = message.from_user.id
    count = referrals.get(user_id, 0)

    bot.send_message(user_id, f" Вы пригласили {count} человек!")

bot.polling(none_stop=True)
