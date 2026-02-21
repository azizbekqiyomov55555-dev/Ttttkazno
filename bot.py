import telebot
from telebot import types
import sqlite3
import random
import string

# Bot tokenini o'rnating (https://t.me/BotFather dan oling)
TOKEN = "8390342230:AAFIAyiSJj6sxsZzePaO-srY2qy8vBC7bCU"
bot = telebot.TeleBot(TOKEN)

# Ma'lumotlar bazasini sozlash
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, 
                  referals INTEGER DEFAULT 0, referal_link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, service TEXT, link TEXT, quantity INTEGER,
                  status TEXT DEFAULT "pending", price INTEGER)''')
    conn.commit()
    conn.close()

# Referal link yaratish
def generate_referal():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# /start komandasi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Foydalanuvchini bazaga qo'shish (agar mavjud bo'lmasa)
    c.execute("INSERT OR IGNORE INTO users (user_id, referal_link) VALUES (?, ?)",
              (user_id, generate_referal()))
    conn.commit()
    
    # Referal tizimi (agar startda ? start param bo'lsa)
    args = message.text.split()
    if len(args) > 1:
        referer_id = args[1]
        if referer_id != str(user_id):
            c.execute("UPDATE users SET referals = referals + 1, balance = balance + 10 WHERE user_id = ?",
                      (referer_id,))
            c.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (user_id,))
            conn.commit()
            bot.send_message(int(referer_id), "🎉 Sizning referalingiz orqali yangi foydalanuvchi qo'shildi! +10 so'm bonus!") 
    
    conn.close()
    
    # Asosiy menyu
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Telegram")
    btn2 = types.KeyboardButton("📷 Instagram")
    btn3 = types.KeyboardButton("🎵 TikTok")
    btn4 = types.KeyboardButton("▶️ YouTube")
    btn5 = types.KeyboardButton("🔍 Qidirish")
    btn6 = types.KeyboardButton("📚 2-Bo'lim")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    # Pastki menyu
    markup2 = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn7 = types.KeyboardButton("📊 Hisobim")
    btn8 = types.KeyboardButton("💰 Hisob To'ldirish")
    btn9 = types.KeyboardButton("📞 Murojaat")
    btn10 = types.KeyboardButton("📋 Buyurtmalarim")
    btn11 = types.KeyboardButton("🤝 Hamkorlik")
    btn12 = types.KeyboardButton("📖 Qo'llanma")
    markup2.add(btn7, btn8, btn9, btn10, btn11, btn12)
    
    bot.send_message(message.chat.id, 
                     f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\n"
                     f"🔥 Botimizga xush kelibsiz! Bu yerda siz ijtimoiy tarmoqlar uchun "
                     f"obuna, like, ko'rish va boshqa xizmatlarni buyurtma qilishingiz mumkin.\n\n"
                     f"📊 Balansingiz: 0 so'm\n"
                     f"🔗 Referal linkingiz: https://t.me/{bot.get_me().username}?start={user_id}",
                     reply_markup=markup)
    bot.send_message(message.chat.id, "👇 Quyidagi menyudan xizmatni tanlang:", reply_markup=markup2)

# Xizmatlarni ko'rsatish
@bot.message_handler(func=lambda message: message.text in ["📱 Telegram", "📷 Instagram", "🎵 TikTok", "▶️ YouTube"])
def show_services(message):
    service = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if service == "📱 Telegram":
        btn1 = types.InlineKeyboardButton("👥 Obunachilar", callback_data="tg_subs")
        btn2 = types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="tg_views")
        btn3 = types.InlineKeyboardButton("❤️ Like", callback_data="tg_likes")
        markup.add(btn1, btn2, btn3)
    elif service == "📷 Instagram":
        btn1 = types.InlineKeyboardButton("👥 Obunachilar", callback_data="inst_subs")
        btn2 = types.InlineKeyboardButton("❤️ Like", callback_data="inst_likes")
        btn3 = types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="inst_views")
        btn4 = types.InlineKeyboardButton("💬 Comment", callback_data="inst_comments")
        markup.add(btn1, btn2, btn3, btn4)
    elif service == "🎵 TikTok":
        btn1 = types.InlineKeyboardButton("👥 Obunachilar", callback_data="tt_subs")
        btn2 = types.InlineKeyboardButton("❤️ Like", callback_data="tt_likes")
        btn3 = types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="tt_views")
        markup.add(btn1, btn2, btn3)
    elif service == "▶️ YouTube":
        btn1 = types.InlineKeyboardButton("👥 Obunachilar", callback_data="yt_subs")
        btn2 = types.InlineKeyboardButton("👍 Like", callback_data="yt_likes")
        btn3 = types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="yt_views")
        btn4 = types.InlineKeyboardButton("💬 Comment", callback_data="yt_comments")
        markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(message.chat.id, f"{service} xizmatlaridan birini tanlang:", reply_markup=markup)

# Callback query larni boshqarish
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    service_map = {
        'tg_subs': 'Telegram obunachilar', 'tg_views': 'Telegram ko\'rishlar', 'tg_likes': 'Telegram like',
        'inst_subs': 'Instagram obunachilar', 'inst_likes': 'Instagram like', 'inst_views': 'Instagram ko\'rishlar',
        'inst_comments': 'Instagram comment', 'tt_subs': 'TikTok obunachilar', 'tt_likes': 'TikTok like',
        'tt_views': 'TikTok ko\'rishlar', 'yt_subs': 'YouTube obunachilar', 'yt_likes': 'YouTube like',
        'yt_views': 'YouTube ko\'rishlar', 'yt_comments': 'YouTube comment'
    }
    
    if call.data in service_map:
        service_name = service_map[call.data]
        msg = bot.send_message(call.message.chat.id, 
                              f"📌 {service_name} buyurtma qilish\n\n"
                              f"Iltimos, havolani (link) yuboring:")
        bot.register_next_step_handler(msg, process_link, service_name)

# Havolani qabul qilish
def process_link(message, service_name):
    link = message.text
    msg = bot.send_message(message.chat.id, 
                          f"🔗 Link qabul qilindi!\n\n"
                          f"Endi {service_name} uchun miqdorni kiriting (masalan: 1000):")
    bot.register_next_step_handler(msg, process_quantity, service_name, link)

# Miqdorni qabul qilish va buyurtmani tasdiqlash
def process_quantity(message, service_name, link):
    try:
        quantity = int(message.text)
        
        # Narxni hisoblash (misol uchun)
        prices = {
            'obunachilar': 10,  # 10 so'm / dona
            'ko\'rishlar': 5,    # 5 so'm / dona
            'like': 7,           # 7 so'm / dona
            'comment': 15        # 15 so'm / dona
        }
        
        # Xizmat turiga qarab narxni aniqlash
        if 'obunachilar' in service_name.lower():
            price_per_unit = prices['obunachilar']
        elif 'ko\'rishlar' in service_name.lower():
            price_per_unit = prices['ko\'rishlar']
        elif 'like' in service_name.lower():
            price_per_unit = prices['like']
        elif 'comment' in service_name.lower():
            price_per_unit = prices['comment']
        else:
            price_per_unit = 5
        
        total_price = quantity * price_per_unit
        
        # Foydalanuvchi balansini tekshirish
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (message.from_user.id,))
        balance = c.fetchone()[0]
        conn.close()
        
        if balance >= total_price:
            # Buyurtmani saqlash
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("INSERT INTO orders (user_id, service, link, quantity, price) VALUES (?, ?, ?, ?, ?)",
                     (message.from_user.id, service_name, link, quantity, total_price))
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (total_price, message.from_user.id))
            conn.commit()
            conn.close()
            
            bot.send_message(message.chat.id, 
                           f"✅ Buyurtma qabul qilindi!\n\n"
                           f"📌 Xizmat: {service_name}\n"
                           f"🔗 Link: {link}\n"
                           f"📊 Miqdor: {quantity}\n"
                           f"💰 Narx: {total_price} so'm\n"
                           f"⏳ Holat: Jarayonda")
        else:
            bot.send_message(message.chat.id, 
                           f"❌ Balansingiz yetarli emas!\n"
                           f"💰 Sizning balansingiz: {balance} so'm\n"
                           f"💳 Buyurtma narxi: {total_price} so'm\n\n"
                           f"Iltimos, avval hisobingizni to'ldiring.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Noto'g'ri format! Iltimos, faqat son kiriting.")

# Hisobim
@bot.message_handler(func=lambda message: message.text == "📊 Hisobim")
def my_account(message):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT balance, referals FROM users WHERE user_id = ?", (message.from_user.id,))
    data = c.fetchone()
    conn.close()
    
    if data:
        balance, referals = data
        bot.send_message(message.chat.id,
                        f"📊 Hisobim ma'lumotlari:\n\n"
                        f"🆔 ID: {message.from_user.id}\n"
                        f"👤 Ism: {message.from_user.first_name}\n"
                        f"💰 Balans: {balance} so'm\n"
                        f"👥 Referallar: {referals}\n"
                        f"🔗 Referal link: https://t.me/{bot.get_me().username}?start={message.from_user.id}")

# Hisob to'ldirish
@bot.message_handler(func=lambda message: message.text == "💰 Hisob To'ldirish")
def top_up(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("💳 Click", callback_data="pay_click")
    btn2 = types.InlineKeyboardButton("📱 Payme", callback_data="pay_payme")
    btn3 = types.InlineKeyboardButton("🏦 Bank karta", callback_data="pay_card")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(message.chat.id,
                    "💰 Hisobni to'ldirish usulini tanlang:",
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment(call):
    method = call.data.replace('pay_', '')
    if method == 'click':
        bot.send_message(call.message.chat.id,
                        "💳 Click to'lov tizimi\n\n"
                        "📞 Telefon: +998901234567\n"
                        "💰 To'lov summasini kiriting:")
    elif method == 'payme':
        bot.send_message(call.message.chat.id,
                        "📱 Payme to'lov tizimi\n\n"
                        "📞 Telefon: +998901234567\n"
                        "💰 To'lov summasini kiriting:")
    elif method == 'card':
        bot.send_message(call.message.chat.id,
                        "🏦 Bank karta ma'lumotlari:\n\n"
                        "💳 Karta: 8600 1234 5678 9012\n"
                        "👤 Ismi: BEKZOD KARIMOV\n"
                        "💰 To'lov summasini kiriting:")

# Buyurtmalarim
@bot.message_handler(func=lambda message: message.text == "📋 Buyurtmalarim")
def my_orders(message):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT order_id, service, quantity, price, status FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT 10", 
              (message.from_user.id,))
    orders = c.fetchall()
    conn.close()
    
    if orders:
        text = "📋 So'nggi 10 ta buyurtmangiz:\n\n"
        for order in orders:
            status_emoji = "✅" if order[4] == "completed" else "⏳" if order[4] == "pending" else "❌"
            text += f"{status_emoji} #{order[0]}: {order[1]} - {order[2]} dona ({order[3]} so'm)\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "📭 Hali buyurtmalar mavjud emas.")

# Murojaat
@bot.message_handler(func=lambda message: message.text == "📞 Murojaat")
def contact(message):
    bot.send_message(message.chat.id,
                    "📞 Murojaat uchun:\n\n"
                    "👨‍💻 Admin: @adminusername\n"
                    "📧 Email: support@example.com\n"
                    "💬 Xabaringizni yozib qoldirishingiz mumkin:")

# Hamkorlik
@bot.message_handler(func=lambda message: message.text == "🤝 Hamkorlik")
def partnership(message):
    bot.send_message(message.chat.id,
                    "🤝 Hamkorlik shartlari:\n\n"
                    "• Har bir referal uchun 10 so'm\n"
                    "• Referal orqali buyurtma berilganda 5% chegirma\n"
                    "• Minimal to'lov: 50 000 so'm\n\n"
                    "🔗 Referal linkingiz: https://t.me/{bot.get_me().username}?start={}")

# Qo'llanma
@bot.message_handler(func=lambda message: message.text == "📖 Qo'llanma" or message.text == "/qollanma")
def guide(message):
    bot.send_message(message.chat.id,
                    "📖 Bot qo'llanmasi:\n\n"
                    "1️⃣ Xizmatni tanlang (Telegram, Instagram, TikTok, YouTube)\n"
                    "2️⃣ Xizmat turini tanlang (obunachilar, like, ko'rishlar)\n"
                    "3️⃣ Havolani yuboring\n"
                    "4️⃣ Miqdorni kiriting\n"
                    "5️⃣ Buyurtmani tasdiqlang\n\n"
                    "💰 To'lov usullari: Click, Payme, Bank karta\n"
                    "🤝 Hamkorlik: Do'stlaringizni taklif qiling va pul ishlang\n\n"
                    "❓ Savollar bo'lsa, admin bilan bog'lanishingiz mumkin.")

# Qidirish va 2-Bo'lim
@bot.message_handler(func=lambda message: message.text in ["🔍 Qidirish", "📚 2-Bo'lim"])
def other_sections(message):
    bot.send_message(message.chat.id, "⚠️ Bu bo'lim hozircha ishga tushirilmagan. Tez orada ishga tushadi!")

# Botni ishga tushirish
if __name__ == "__main__":
    init_db()
    print("Bot ishga tushdi...")
    bot.infinity_polling()
