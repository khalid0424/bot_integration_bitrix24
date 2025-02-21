import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from config import TOKEN, BITRIX_WEBHOOK_URL, manager_username, BITRIX_FIELDS, courses, tariffs 

bot = telebot.TeleBot(TOKEN)

user_states = {}

# Проверка конфигурации перед запуском
required_configs = [TOKEN, BITRIX_WEBHOOK_URL, manager_username, BITRIX_FIELDS, courses, tariffs ]
if not all(required_configs):
    raise ValueError("Не все необходимые параметры конфигурации определены в config!")

def create_courses_keyboard():
    keyboard = InlineKeyboardMarkup()
    for course_id, course_name in courses.items():
        keyboard.add(InlineKeyboardButton(course_name, callback_data=f"course_{course_id}"))
    return keyboard

def create_payment_method_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("💳 Онлайн", callback_data="payment_online"),
        InlineKeyboardButton("👨‍💼 Менеджер", callback_data="payment_manager")
    )
    return keyboard

def create_tariffs_keyboard(course_id):
    keyboard = InlineKeyboardMarkup()
    for tariff_id, tariff_info in tariffs.items():
        button_text = f"{tariff_info['name']} - {tariff_info['price']} руб 💰"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=f"tariff_{course_id}_{tariff_id}"))
    return keyboard

@bot.message_handler(commands=["start"])
def start_handler(message):
    referrer = message.text.split(" ")[-1] if " " in message.text else None
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = telebot.types.KeyboardButton(text="📱 Отправьте свой номер телефона", request_contact=True)
    keyboard.add(button_phone)

    user_states[message.from_user.id] = {"referrer": referrer}
    bot.send_message(
        message.chat.id,
        "👋 Привет! Пожалуйста, отправьте свой номер телефона:",
        reply_markup=keyboard
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
        "📚 Пожалуйста, выберите курс:",
        reply_markup=create_courses_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def course_callback(call): 
    user_id = call.from_user.id
    course_id = call.data.split("_")[1]
    user_states[user_id]["selected_course"] = course_id

    bot.edit_message_text(
        "💵 Выберите метод оплаты:",
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
            f"📞 Свяжитесь с менеджером: {manager_username}",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        course_id = user_states[user_id]["selected_course"]
        bot.edit_message_text(
            "🎟 Пожалуйста, выберите тариф:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_tariffs_keyboard(course_id)
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("tariff_"))
def tariff_callback(call):
    user_id = call.from_user.id
    _, course_id, tariff_id = call.data.split("_")

    if "phone" not in user_states[user_id]:
        bot.send_message(user_id, "⚠️ Пожалуйста, введите номер телефона!")
        return
    
    try:
        referrer = user_states[user_id].get("referrer")
        contact_response = requests.get(f"{BITRIX_WEBHOOK_URL}/crm.contact.list", params={"FILTER[PHONE]": user_states[user_id]["phone"]}, timeout=10)
        contact_response.raise_for_status()
        contact_data = contact_response.json()

        contact_id = None
        if "result" in contact_data and len(contact_data["result"]) > 0:
            contact_id = contact_data["result"][0]["ID"]
        else:
            contact_create = requests.post(f"{BITRIX_WEBHOOK_URL}/crm.contact.add", json={
                "fields": {
                    "NAME": f"User {user_id}",
                    "PHONE": [{"VALUE": user_states[user_id]["phone"], "VALUE_TYPE": "WORK"}],
                    
                }
            }, timeout=10)
            contact_create.raise_for_status()
            contact_id = contact_create.json().get("result")

        deal_data = {
            "fields": {
                BITRIX_FIELDS["title"]: f"🛒 Покупка курса - {courses[course_id]}",
                BITRIX_FIELDS["type"]: "GOODS",
                BITRIX_FIELDS["stage"]: "NEW",
                BITRIX_FIELDS["price"]: int(tariffs[tariff_id]["price"]),
                "CONTACT_ID": contact_id,
                BITRIX_FIELDS["course"]: courses[course_id],
                BITRIX_FIELDS["tariff_name"]: tariffs[tariff_id]["name"],
                BITRIX_FIELDS["referral"]: referrer if referrer else "Нет реферера"
            }
        }

        response = requests.post(f"{BITRIX_WEBHOOK_URL}/crm.deal.add", json=deal_data, timeout=10)
        response.raise_for_status()

        bot.send_message(user_id, "✅ Спасибо за покупку, ждите подтверждения платежа. 🚀")
    except requests.RequestException:
        bot.send_message(user_id, "❌ Ошибка связи с CRM. Попробуйте позже.")
    except Exception:
        bot.send_message(user_id, "⚠️ Произошла ошибка. Обратитесь к поддержке.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
