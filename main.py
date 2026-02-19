import random
import sqlite3
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN or not ADMIN_ID:
    raise ValueError("TOKEN yoki ADMIN_ID topilmadi")

ADMIN_ID = int(ADMIN_ID)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================= DATABASE =================
conn = sqlite3.connect("casino.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 1000,
    last_bonus INTEGER DEFAULT 0
)
""")

conn.commit()

# ================= MENUS =================
def main_menu(user_id):
    keyboard = [
        [KeyboardButton("🎮 O‘yinlar")],
        [KeyboardButton("🎁 Bonus"), KeyboardButton("👤 Profil")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def games_menu():
    keyboard = [
        [KeyboardButton("🎲 Dice"), KeyboardButton("🎯 Dart")],
        [KeyboardButton("⚽ Penalty"), KeyboardButton("🎰 Slot")],
        [KeyboardButton("🪙 Coin"), KeyboardButton("🃏 BlackJack")],
        [KeyboardButton("🏀 Basket"), KeyboardButton("🎳 Bowling")],
        [KeyboardButton("🎮 Lucky"), KeyboardButton("💣 Mines")],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= GAME SETTINGS =================
GAME_RATES = {
    "🎲 Dice": 0.45,
    "🎯 Dart": 0.40,
    "⚽ Penalty": 0.50,
    "🎰 Slot": 0.35,
    "🪙 Coin": 0.50,
    "🃏 BlackJack": 0.42,
    "🏀 Basket": 0.48,
    "🎳 Bowling": 0.46,
    "🎮 Lucky": 0.30,
    "💣 Mines": 0.25
}

awaiting_bet = {}
current_game = {}

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                   (message.from_user.id,))
    conn.commit()

    await message.answer("🎰 Casino Bot", reply_markup=main_menu(message.from_user.id))

# ================= PROFILE =================
@dp.message_handler(lambda m: m.text == "👤 Profil")
async def profile(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?",
                   (message.from_user.id,))
    bal = cursor.fetchone()[0]

    await message.answer(f"💰 Balans: {bal}")

# ================= BONUS =================
@dp.message_handler(lambda m: m.text == "🎁 Bonus")
async def bonus(message: types.Message):
    cursor.execute("SELECT last_bonus FROM users WHERE user_id=?",
                   (message.from_user.id,))
    last = cursor.fetchone()[0]

    now = int(time.time())

    if now - last < 86400:
        await message.answer("⏳ 24 soatda 1 marta bonus!")
        return

    cursor.execute("UPDATE users SET balance=balance+100, last_bonus=? WHERE user_id=?",
                   (now, message.from_user.id))
    conn.commit()

    await message.answer("🎁 +100 coin qo‘shildi!")

# ================= GAMES MENU =================
@dp.message_handler(lambda m: m.text == "🎮 O‘yinlar")
async def games_handler(message: types.Message):
    await message.answer("🎮 O‘yin tanlang:", reply_markup=games_menu())

# ================= UNIVERSAL =================
@dp.message_handler()
async def universal(message: types.Message):
    uid = message.from_user.id
    text = message.text

    # Orqaga
    if text == "🔙 Orqaga":
        await message.answer("🏠 Asosiy menyu", reply_markup=main_menu(uid))
        return

    # O‘yin tanlash
    if text in GAME_RATES:
        awaiting_bet[uid] = True
        current_game[uid] = text
        await message.answer(f"{text} o‘yini tanlandi!\n💵 Stavka kiriting (min 10):")
        return

    # Stavka
    if uid in awaiting_bet and text.isdigit():
        bet = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka noto‘g‘ri")
            return

        game = current_game[uid]
        win_chance = GAME_RATES[game]

        win = random.random() < win_chance

        if win:
            profit = bet
            cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                           (profit, uid))
            result = f"🎉 YUTDINGIZ! +{profit}"
        else:
            cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                           (bet, uid))
            result = f"😢 YUTQAZDINGIZ! -{bet}"

        conn.commit()

        del awaiting_bet[uid]
        del current_game[uid]

        await message.answer(result)
        return

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
