import telebot
from telebot import types
import sqlite3
import random
import string
import logging
import time
from datetime import datetime
import threading
import os

# ------------------- SOZLAMALAR -------------------
BOT_TOKEN = "8490088431:AAH-5kbO11C7TH9Q6IRYByQ45xoyb0fr7QY"  # BotFather dan olingan token
ADMIN_IDS = [8537782289, 987654321]  # Adminlar Telegram ID si (o'zingiznikini qo'ying)

# Narxlar (so'm / dona) – admin panel orqali o'zgartirish mumkin
DEFAULT_PRICES = {
    'telegram_followers': 10,
    'telegram_views': 5,
    'telegram_likes': 7,
    'instagram_followers': 15,
    'instagram_likes': 8,
    'instagram_views': 6,
    'instagram_comments': 20,
    'tiktok_followers': 12,
    'tiktok_likes': 7,
    'tiktok_views': 5,
    'youtube_followers': 20,
    'youtube_likes': 10,
    'youtube_views': 8,
    'youtube_comments': 25
}

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------------- MA'LUMOTLAR BAZASI -------------------
def init_db():
    """Barcha jadvallarni yaratish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # Foydalanuvchilar
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  balance INTEGER DEFAULT 0,
                  referals INTEGER DEFAULT 0,
                  referal_link TEXT UNIQUE,
                  joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_activity TIMESTAMP)''')
    
    # Buyurtmalar
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  service_code TEXT,
                  service_name TEXT,
                  link TEXT,
                  quantity INTEGER,
                  price INTEGER,
                  status TEXT DEFAULT 'pending',  -- pending, processing, completed, cancelled
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  completed_at TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    # Tranzaksiyalar (hisob to'ldirish)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  amount INTEGER,
                  method TEXT,  -- click, payme, card, referal
                  status TEXT DEFAULT 'pending',  -- pending, completed, failed
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  completed_at TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(user_id))''')
    
    # Sozlamalar (narxlar va boshqalar)
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')
    
    # Default narxlarni sozlamalarga qo'shish
    for k, v in DEFAULT_PRICES.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    
    conn.commit()
    conn.close()

def get_setting(key):
    """Sozlamadan qiymat olish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    """Sozlamaga qiymat yozish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    """Foydalanuvchi ma'lumotlarini olish (agar yo'q bo'lsa yaratish)"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        # Yangi foydalanuvchi yaratish
        referal_link = generate_referal_link()
        c.execute('''INSERT INTO users (user_id, username, first_name, last_name, referal_link, last_activity)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, None, None, None, referal_link, datetime.now()))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
    else:
        # Oxirgi faollikni yangilash
        c.execute("UPDATE users SET last_activity = ? WHERE user_id = ?", (datetime.now(), user_id))
        conn.commit()
    conn.close()
    return user

def update_user_info(user_id, username, first_name, last_name):
    """Foydalanuvchi ma'lumotlarini yangilash"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''UPDATE users SET username = ?, first_name = ?, last_name = ?, last_activity = ?
                 WHERE user_id = ?''',
              (username, first_name, last_name, datetime.now(), user_id))
    conn.commit()
    conn.close()

def generate_referal_link():
    """Unikal referal link yaratish"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def add_referal_bonus(referrer_id, new_user_id):
    """Referal orqali kelgan foydalanuvchi uchun bonus berish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    # Refererga 10 so'm bonus
    c.execute("UPDATE users SET balance = balance + 10, referals = referals + 1 WHERE user_id = ?", (referrer_id,))
    # Yangi foydalanuvchiga 5 so'm bonus
    c.execute("UPDATE users SET balance = balance + 5 WHERE user_id = ?", (new_user_id,))
    conn.commit()
    conn.close()
    return True

def get_balance(user_id):
    """Foydalanuvchi balansini qaytarish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = c.fetchone()[0]
    conn.close()
    return balance

def update_balance(user_id, amount, add=True):
    """Balansni o'zgartirish (add=True qo'shish, False ayirish)"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    if add:
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    else:
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def create_order(user_id, service_code, service_name, link, quantity, price):
    """Yangi buyurtma yaratish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders (user_id, service_code, service_name, link, quantity, price, status)
                 VALUES (?, ?, ?, ?, ?, ?, 'pending')''',
              (user_id, service_code, service_name, link, quantity, price))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id, limit=10):
    """Foydalanuvchining oxirgi buyurtmalarini olish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''SELECT order_id, service_name, quantity, price, status, created_at
                 FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?''',
              (user_id, limit))
    orders = c.fetchall()
    conn.close()
    return orders

def get_all_orders(limit=50, status=None):
    """Barcha buyurtmalarni olish (admin uchun)"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    if status:
        c.execute('''SELECT o.order_id, o.user_id, u.username, o.service_name, o.link, o.quantity, o.price, o.status, o.created_at
                     FROM orders o LEFT JOIN users u ON o.user_id = u.user_id
                     WHERE o.status = ? ORDER BY o.created_at DESC LIMIT ?''', (status, limit))
    else:
        c.execute('''SELECT o.order_id, o.user_id, u.username, o.service_name, o.link, o.quantity, o.price, o.status, o.created_at
                     FROM orders o LEFT JOIN users u ON o.user_id = u.user_id
                     ORDER BY o.created_at DESC LIMIT ?''', (limit,))
    orders = c.fetchall()
    conn.close()
    return orders

def update_order_status(order_id, status):
    """Buyurtma holatini yangilash"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    if status == 'completed':
        c.execute("UPDATE orders SET status = ?, completed_at = ? WHERE order_id = ?",
                  (status, datetime.now(), order_id))
    else:
        c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

def create_transaction(user_id, amount, method):
    """Yangi tranzaksiya yaratish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''INSERT INTO transactions (user_id, amount, method, status)
                 VALUES (?, ?, ?, 'pending')''', (user_id, amount, method))
    txn_id = c.lastrowid
    conn.commit()
    conn.close()
    return txn_id

def complete_transaction(txn_id):
    """Tranzaksiyani yakunlash va balansga qo'shish"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_id, amount FROM transactions WHERE txn_id = ?", (txn_id,))
    txn = c.fetchone()
    if txn:
        user_id, amount = txn
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        c.execute("UPDATE transactions SET status = 'completed', completed_at = ? WHERE txn_id = ?",
                  (datetime.now(), txn_id))
        conn.commit()
        conn.close()
        return user_id, amount
    conn.close()
    return None, None

# ------------------- BOT OB'EKTI -------------------
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("Bot ishga tushdi...")

# ------------------- YORDAMCHI FUNKSIYALAR -------------------
def get_main_keyboard():
    """Asosiy menyu (xizmatlar)"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Telegram")
    btn2 = types.KeyboardButton("📷 Instagram")
    btn3 = types.KeyboardButton("🎵 TikTok")
    btn4 = types.KeyboardButton("▶️ YouTube")
    btn5 = types.KeyboardButton("🔍 Qidirish")
    btn6 = types.KeyboardButton("📚 2-Bo'lim")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def get_bottom_keyboard():
    """Pastki menyu (profil, to'ldirish, murojaat va h.k.)"""
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn1 = types.KeyboardButton("📊 Hisobim")
    btn2 = types.KeyboardButton("💰 Hisob To'ldirish")
    btn3 = types.KeyboardButton("📞 Murojaat")
    btn4 = types.KeyboardButton("📋 Buyurtmalarim")
    btn5 = types.KeyboardButton("🤝 Hamkorlik")
    btn6 = types.KeyboardButton("📖 Qo'llanma")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def get_service_inline(service):
    """Xizmat turiga mos inline tugmalar"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    if service == "telegram":
        markup.add(
            types.InlineKeyboardButton("👥 Obunachilar", callback_data="service_tg_followers"),
            types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="service_tg_views"),
            types.InlineKeyboardButton("❤️ Like", callback_data="service_tg_likes")
        )
    elif service == "instagram":
        markup.add(
            types.InlineKeyboardButton("👥 Obunachilar", callback_data="service_inst_followers"),
            types.InlineKeyboardButton("❤️ Like", callback_data="service_inst_likes"),
            types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="service_inst_views"),
            types.InlineKeyboardButton("💬 Comment", callback_data="service_inst_comments")
        )
    elif service == "tiktok":
        markup.add(
            types.InlineKeyboardButton("👥 Obunachilar", callback_data="service_tt_followers"),
            types.InlineKeyboardButton("❤️ Like", callback_data="service_tt_likes"),
            types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="service_tt_views")
        )
    elif service == "youtube":
        markup.add(
            types.InlineKeyboardButton("👥 Obunachilar", callback_data="service_yt_followers"),
            types.InlineKeyboardButton("👍 Like", callback_data="service_yt_likes"),
            types.InlineKeyboardButton("👁 Ko'rishlar", callback_data="service_yt_views"),
            types.InlineKeyboardButton("💬 Comment", callback_data="service_yt_comments")
        )
    return markup

def get_price(service_code):
    """Berilgan xizmat kodiga mos narxni qaytarish (sozlamadan)"""
    price_str = get_setting(service_code)
    return int(price_str) if price_str else 0

def format_order_status(status):
    """Holatni chiroyli qilib qaytarish"""
    if status == 'pending':
        return "⏳ Kutilmoqda"
    elif status == 'processing':
        return "⚙️ Jarayonda"
    elif status == 'completed':
        return "✅ Bajarildi"
    elif status == 'cancelled':
        return "❌ Bekor qilingan"
    return status

# ------------------- /start KOMANDASI -------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Foydalanuvchini bazaga qo'shish/yangilash
    get_user(user_id)
    update_user_info(user_id, username, first_name, last_name)
    
    # Referal tizimi
    args = message.text.split()
    if len(args) > 1:
        referal_code = args[1]
        # referal_code bu user_id emas, balki referal_link (masalan, "abc123")
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE referal_link = ?", (referal_code,))
        referrer = c.fetchone()
        conn.close()
        if referrer and referrer[0] != user_id:
            add_referal_bonus(referrer[0], user_id)
            try:
                bot.send_message(referrer[0], "🎉 Sizning referalingiz orqali yangi foydalanuvchi qo'shildi! +10 so'm bonus hisobingizga qo'shildi.")
            except:
                pass
    
    # Salomlashish va asosiy menyu
    bot.send_message(user_id, f"👋 Assalomu alaykum, {first_name}!\n\n"
                              f"🔥 Botimizga xush kelibsiz! Bu yerda siz ijtimoiy tarmoqlar uchun "
                              f"obuna, like, ko'rish va boshqa xizmatlarni buyurtma qilishingiz mumkin.",
                     reply_markup=get_main_keyboard())
    bot.send_message(user_id, "👇 Quyidagi menyudan xizmatni tanlang:", reply_markup=get_bottom_keyboard())

# ------------------- XIZMATLAR (TELEGRAM, INSTAGRAM, TikTok, YouTube) -------------------
@bot.message_handler(func=lambda m: m.text in ["📱 Telegram", "📷 Instagram", "🎵 TikTok", "▶️ YouTube"])
def choose_service(message):
    service_map = {
        "📱 Telegram": "telegram",
        "📷 Instagram": "instagram",
        "🎵 TikTok": "tiktok",
        "▶️ YouTube": "youtube"
    }
    service = service_map[message.text]
    bot.send_message(message.chat.id, f"{message.text} xizmatlaridan birini tanlang:",
                     reply_markup=get_service_inline(service))

# ------------------- SERVICE CALLBACKLAR -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def service_callback(call):
    service_code = call.data.replace('service_', '')
    # service_code masalan: tg_followers, inst_likes, ...
    user_id = call.from_user.id
    
    # Xizmat nomini chiroyli qilib olish
    service_names = {
        'tg_followers': 'Telegram obunachilar',
        'tg_views': 'Telegram ko\'rishlar',
        'tg_likes': 'Telegram like',
        'inst_followers': 'Instagram obunachilar',
        'inst_likes': 'Instagram like',
        'inst_views': 'Instagram ko\'rishlar',
        'inst_comments': 'Instagram comment',
        'tt_followers': 'TikTok obunachilar',
        'tt_likes': 'TikTok like',
        'tt_views': 'TikTok ko\'rishlar',
        'yt_followers': 'YouTube obunachilar',
        'yt_likes': 'YouTube like',
        'yt_views': 'YouTube ko\'rishlar',
        'yt_comments': 'YouTube comment'
    }
    service_name = service_names.get(service_code, service_code)
    
    # Narxni olish
    price_per_unit = get_price(service_code)
    if not price_per_unit:
        price_per_unit = 5  # default
    
    # Foydalanuvchidan link so'rash
    msg = bot.send_message(call.message.chat.id,
                          f"📌 {service_name} buyurtma qilish\n\n"
                          f"💰 Narx: {price_per_unit} so'm / dona\n\n"
                          f"Iltimos, havolani (link) yuboring:")
    bot.register_next_step_handler(msg, process_link, service_code, service_name, price_per_unit)
    bot.answer_callback_query(call.id)

def process_link(message, service_code, service_name, price_per_unit):
    link = message.text.strip()
    user_id = message.from_user.id
    
    # Miqdorni so'rash
    msg = bot.send_message(message.chat.id,
                          f"🔗 Link qabul qilindi!\n\n"
                          f"Endi {service_name} uchun miqdorni kiriting (masalan: 1000):")
    bot.register_next_step_handler(msg, process_quantity, service_code, service_name, price_per_unit, link)

def process_quantity(message, service_code, service_name, price_per_unit, link):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ Noto'g'ri format! Iltimos, musbat butun son kiriting.")
        return
    
    user_id = message.from_user.id
    total_price = quantity * price_per_unit
    balance = get_balance(user_id)
    
    if balance < total_price:
        bot.send_message(message.chat.id,
                        f"❌ Balansingiz yetarli emas!\n"
                        f"💰 Sizning balansingiz: {balance} so'm\n"
                        f"💳 Buyurtma narxi: {total_price} so'm\n\n"
                        f"Iltimos, avval hisobingizni to'ldiring.",
                        reply_markup=get_bottom_keyboard())
        return
    
    # Balansdan ayirish
    update_balance(user_id, total_price, add=False)
    
    # Buyurtma yaratish
    order_id = create_order(user_id, service_code, service_name, link, quantity, total_price)
    
    # Tasdiqlash xabari
    bot.send_message(user_id,
                    f"✅ Buyurtma qabul qilindi!\n\n"
                    f"📌 Buyurtma raqami: #{order_id}\n"
                    f"📌 Xizmat: {service_name}\n"
                    f"🔗 Link: {link}\n"
                    f"📊 Miqdor: {quantity}\n"
                    f"💰 Narx: {total_price} so'm\n"
                    f"⏳ Holat: ⏳ Kutilmoqda\n\n"
                    f"Buyurtmangiz tez orada bajariladi.",
                    reply_markup=get_bottom_keyboard())
    
    # Adminlarga xabar (ixtiyoriy)
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id,
                            f"🆕 Yangi buyurtma!\n"
                            f"👤 Foydalanuvchi: {user_id}\n"
                            f"📌 Xizmat: {service_name}\n"
                            f"🔗 Link: {link}\n"
                            f"📊 Miqdor: {quantity}\n"
                            f"💰 Narx: {total_price} so'm")
        except:
            pass
    
    # Bu yerda buyurtmani bajarish jarayonini simulyatsiya qilish uchun alohida thread ishga tushirish mumkin
    # Masalan, 30 soniyadan keyin "processing", 2 daqiqadan keyin "completed" qilish
    def process_order(order_id):
        time.sleep(30)  # 30 soniya kutilmoqda
        update_order_status(order_id, 'processing')
        # Foydalanuvchiga xabar (ixtiyoriy)
        # bot.send_message(user_id, f"⚙️ #{order_id} - buyurtma ishga tushdi.")
        time.sleep(90)  # 1.5 daqiqa
        update_order_status(order_id, 'completed')
        bot.send_message(user_id, "Salom")
