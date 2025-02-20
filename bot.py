import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from config import TOKEN, BITRIX_WEBHOOK_URL, manager_username, bot_username, BITRIX_FIELDS, courses, tariffs

bot = telebot.TeleBot(TOKEN)

user_states = {}
bloggers = {
    "habibulo": 0,
    "mirzo": 0,
    "muboriz": 0,
    "bobo": 0,
    "jamol": 0
}

def generate_referral_link(username):
    return f"https://t.me/{bot_username}?start=ref{username.lower()}"

@bot.message_handler(commands=["referral_links"])
def show_referral_links(message):
    text = "Реферальные ссылки для блогеров:\n"
    for blogger in bloggers:
        text += f"{blogger}: {generate_referral_link(blogger)}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["referral_stats"])
def show_referral_count(message):
    text = "Статистика по блогерам:\n"
    for blogger, count in bloggers.items():
        text += f"{blogger}: {count} приглашенных\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_name = None
    if len(args) > 1 and args[1].startswith("ref"): 
        referrer_username = args[1][3:].lower()
        if referrer_username in bloggers:
            bloggers[referrer_username] += 1
            referrer_name = referrer_username
        else:
            bot.send_message(message.chat.id, "Реферал не найден, продолжаем без него.")
    user_states[user_id] = {"referrer": referrer_name}
    bot.send_message(
        message.chat.id,
        "Привет! Пожалуйста, отправьте свой номер телефона:",
        reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            telebot.types.KeyboardButton("Отправьте свой номер телефона", request_contact=True)
        )
    )

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number.replace(" ", "")
    if not phone.startswith("+"):
        phone = f"+{phone}"
    user_states[user_id]["phone"] = phone
    bot.send_message(
        message.chat.id,
        "Пожалуйста, выберите курс:",
        reply_markup=InlineKeyboardMarkup().add(
            *[InlineKeyboardButton(name, callback_data=f"course_{cid}") for cid, name in courses.items()]
        )
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def course_callback(call): 
    user_id = call.from_user.id
    course_id = call.data.split("_")[1]
    user_states[user_id]["selected_course"] = course_id
    bot.edit_message_text(
        "Выберите метод оплаты:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=InlineKeyboardMarkup().row(
            InlineKeyboardButton("Онлайн", callback_data="payment_online"),
            InlineKeyboardButton("Менеджер", callback_data="payment_manager")
        )
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("payment_"))
def payment_method_callback(call):
    user_id = call.from_user.id
    if call.data.split("_")[1] == "manager":
        bot.edit_message_text(f"Свяжитесь с менеджером: {manager_username}", call.message.chat.id, call.message.message_id)
    else:
        course_id = user_states[user_id]["selected_course"]
        bot.edit_message_text(
            "Пожалуйста, выберите тариф:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(
                *[InlineKeyboardButton(f"{t['name']} - {t['price']} рубл", callback_data=f"tariff_{course_id}_{tid}") for tid, t in tariffs.items()]
            )
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tariff_"))
def tariff_callback(call):
    user_id = call.from_user.id
    _, course_id, tariff_id = call.data.split("_")
    if "phone" not in user_states[user_id]:
        bot.send_message(user_id, "Пожалуйста, введите номер телефона!")
        return
    referrer_name = user_states[user_id].get("referrer", "Без реферала")
    try:
        contact_response = requests.get(f"{BITRIX_WEBHOOK_URL}/crm.contact.list", params={"FILTER[PHONE]": user_states[user_id]["phone"]}, timeout=10)
        contact_response.raise_for_status()
        contact_data = contact_response.json()
        contact_id = contact_data["result"][0]["ID"] if contact_data.get("result") else None
        if not contact_id:
            contact_create = requests.post(f"{BITRIX_WEBHOOK_URL}/crm.contact.add", json={
                "fields": {"NAME": f"User {user_id}", "PHONE": [{"VALUE": user_states[user_id]["phone"], "VALUE_TYPE": "WORK"}]}
            }, timeout=10)
            contact_create.raise_for_status()
            contact_id = contact_create.json().get("result")
        response = requests.post(f"{BITRIX_WEBHOOK_URL}/crm.deal.add", json={
            "fields": {
                BITRIX_FIELDS["title"]: f"Покупка курса - {courses[course_id]}",
                BITRIX_FIELDS["type"]: "GOODS",
                BITRIX_FIELDS["stage"]: "NEW",
                BITRIX_FIELDS["price"]: int(tariffs[tariff_id]["price"]),
                "CONTACT_ID": contact_id,
                BITRIX_FIELDS["course"]: courses[course_id],
                BITRIX_FIELDS["tariff_name"]: tariffs[tariff_id]["name"],
                "UF_CRM_1740017868": referrer_name
            }
        }, timeout=10)
        response.raise_for_status()
        bot.send_message(user_id, "Спасибо за покупку, ждите подтверждения платежа.")
    except requests.RequestException as e:
        bot.send_message(user_id, f"Ошибка связи с CRM: {str(e)}. Попробуйте позже.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
