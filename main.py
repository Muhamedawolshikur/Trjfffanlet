import telebot
from telebot import types, apihelper
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- [ RENDER KEEP-ALIVE SERVER ] ---
app = Flask('')

@app.route('/')
def home():
    return "Translator Pro is Online!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [ CONFIG (SECURED WITH ENV VARIABLES) ] ---
# ኮድህ በGitHub ላይ በግልጽ እንዳይታይ በEnvironment Variables ተተክቷል
API_TOKEN = os.environ.get('API_TOKEN')
ADMIN_ID_ENV = os.environ.get('ADMIN_ID', '8700421304')

ADMIN_ID = int(ADMIN_ID_ENV)
bot = telebot.TeleBot(API_TOKEN)

apihelper.CONNECT_TIMEOUT = 100
apihelper.READ_TIMEOUT = 100

all_users = set()
user_langs = {}
LINE = "━━━━━━━━━━━━━━━━━━━━"

# የተሟላ የቋንቋ ዝርዝር
LANGUAGES = {
    "Amharic 🇪🇹": "am",
    "Oromo 🇪🇹": "om",
    "Tigrinya 🇪🇹": "ti",
    "Afar 🇪🇹": "aa",
    "English 🇺🇸": "en",
    "Arabic 🇸🇦": "ar",
    "French 🇫🇷": "fr",
    "Spanish 🇪🇸": "es",
    "German 🇩🇪": "de",
    "Italian 🇮🇹": "it",
    "Portuguese 🇵🇹": "pt",
    "Russian 🇷🇺": "ru",
    "Turkish 🇹🇷": "tr",
    "Hindi 🇮🇳": "hi",
    "Chinese 🇨🇳": "zh-CN",
    "Japanese 🇯🇵": "ja",
    "Korean 🇰🇷": "ko",
    "Dutch 🇳🇱": "nl"
}

def omni_translate(text, target_lang):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return "".join([s[0] for s in result[0]])
        return "❌ Engine Error."
    except: 
        return "❌ Translation Timeout."

def get_lang_keyboard(exclude_code=None):
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for name, code in LANGUAGES.items():
        if code != exclude_code:
            buttons.append(types.InlineKeyboardButton(text=name, callback_data=f"setlang_{code}"))
    markup.add(*buttons)
    return markup

# --- [ ADMIN BROADCAST ] ---
@bot.message_handler(commands=['bc'])
def broadcast(message):
    if message.chat.id == ADMIN_ID:
        if message.reply_to_message:
            success, failed = 0, 0
            for user in list(all_users):
                try:
                    bot.copy_message(user, message.chat.id, message.reply_to_message.message_id)
                    success += 1
                except: failed += 1
            bot.reply_to(message, f"📢 <b>Broadcast Status:</b>\n{LINE}\n✅ Success: <code>{success}</code>\n❌ Failed: <code>{failed}</code>", parse_mode="HTML")
        else:
            bot.reply_to(message, "⚠️ Please reply to a message with <code>/bc</code>", parse_mode="HTML")

# --- [ MAIN HANDLERS ] ---
@bot.message_handler(commands=['start', 'setting'])
def start_cmd(message):
    all_users.add(message.chat.id)
    text = (
        f"⚡ <b>TRANSLATOR PRO 亗</b>\n"
        f"{LINE}\n"
        f"👋 Welcome <b>{message.from_user.first_name}</b>!\n\n"
        f"🤖 Just send me any text or message you want to translate, "
        f"and I will process it instantly with dynamic language options."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang_"))
def callback_set_lang(call):
    lang_code = call.data.split("_")[1]
    chat_id = call.message.chat.id
    user_langs[chat_id] = lang_code
    lang_name = next(name for name, code in LANGUAGES.items() if code == lang_code)
    
    try:
        if call.message.reply_to_message:
            original_text = call.message.reply_to_message.text
            bot.answer_callback_query(call.id, f"Translating to {lang_name}...")
            
            translated = omni_translate(original_text, lang_code)
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"🌐 <b>TRANSLATOR PRO 亗</b>\n"
                     f"{LINE}\n"
                     f"📝 <b>Translation ({lang_name}):</b>\n"
                     f"<code>{translated}</code>\n"
                     f"{LINE}\n"
                     f"👤 <b>By: @Officialcoders</b>",
                parse_mode="HTML",
                reply_markup=get_lang_keyboard(exclude_code=lang_code)
            )
        else:
            bot.answer_callback_query(call.id, f"Language set to {lang_name}")
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ Preference Updated: <b>{lang_name}</b>\n\n📥 Send me a message to start translating!",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Update skipped: {e}")

@bot.message_handler(func=lambda m: True)
def handle_translation(message):
    chat_id = message.chat.id
    all_users.add(chat_id)
    
    if chat_id not in user_langs:
        user_langs[chat_id] = "am" 

    bot.send_chat_action(chat_id, 'typing')
    target = user_langs[chat_id]
    lang_name = next(name for name, code in LANGUAGES.items() if code == target)
    translated = omni_translate(message.text, target)
    
    bot.reply_to(
        message, 
        f"🌐 <b>TRANSLATOR PRO 亗</b>\n"
        f"{LINE}\n"
        f"📝 <b>Translation ({lang_name}):</b>\n"
        f"<code>{translated}</code>\n"
        f"{LINE}\n"
        f"👑 <b>@Officialcoders & @Codex_Habesha</b>",
        parse_mode="HTML",
        reply_markup=get_lang_keyboard(exclude_code=target)
    )

# --- [ RUNNER ] ---
if __name__ == "__main__":
    print("🚀 Translator Bot is starting...")
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, timeout=90, long_polling_timeout=20)
        except Exception as e:
            print(f"Connection Error: {e}")
            time.sleep(5)
