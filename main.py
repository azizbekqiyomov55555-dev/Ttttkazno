import random
import sqlite3
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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

def main_menu():
    keyboard = [
        [KeyboardButton("🎮 O‘yinlar")],
        [KeyboardButton("🎁 Bonus"), KeyboardButton("👤 Profil")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def games_menu():
    keyboard = [
        [KeyboardButton("💣 Mines")],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= MINES GAME =================

mines_games = {}

def mines_keyboard(game):
    kb = InlineKeyboardMarkup(row_width=5)
    buttons = []

    for i in range(15):
        if i in game["opened"]:
            if i in game["mines"]:
                text = "💣"
            else:
                text = "✅"
        else:
            text = "⬜"

        buttons.append(
            InlineKeyboardButton(text, callback_data=f"mine_{i}")
        )

    kb.add(*buttons)
    kb.add(InlineKeyboardButton("💰 Yutuqni olish", callback_data="cashout"))
    return kb

# ================= START =================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                   (message.from_user.id,))
    conn.commit()

    await message.answer("🎰 Casino Bot", reply_markup=main_menu())

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

# ================= GAMES =================

@dp.message_handler(lambda m: m.text == "🎮 O‘yinlar")
async def games_handler(message: types.Message):
    await message.answer("🎮 O‘yin tanlang:", reply_markup=games_menu())

@dp.message_handler(lambda m: m.text == "💣 Mines")
async def mines_start(message: types.Message):
    await message.answer("💵 Stavka kiriting (min 10):")
    mines_games[message.from_user.id] = {"awaiting_bet": True}

@dp.message_handler()
async def handle_bet(message: types.Message):
    uid = message.from_user.id

    if uid in mines_games and mines_games[uid].get("awaiting_bet"):
        if not message.text.isdigit():
            return

        bet = int(message.text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka noto‘g‘ri")
            return

        mines = random.sample(range(15), 8)

        mines_games[uid] = {
            "bet": bet,
            "mines": mines,
            "opened": [],
            "multiplier": 1.0,
            "awaiting_bet": False
        }

        await message.answer(
            "💣 O‘yin boshlandi!\nQutini tanlang:",
            reply_markup=mines_keyboard(mines_games[uid])
        )

# ================= CALLBACK =================

@dp.callback_query_handler(lambda c: c.data.startswith("mine_"))
async def open_mine(callback: types.CallbackQuery):
    uid = callback.from_user.id

    if uid not in mines_games:
        return

    game = mines_games[uid]
    index = int(callback.data.split("_")[1])

    if index in game["opened"]:
        return

    game["opened"].append(index)

    if index in game["mines"]:
        cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                       (game["bet"], uid))
        conn.commit()

        await callback.message.edit_text(
            f"💥 Portladi!\n😢 -{game['bet']}",
        )
        del mines_games[uid]
        return
    else:
        game["multiplier"] += 0.5

        await callback.message.edit_reply_markup(
            reply_markup=mines_keyboard(game)
        )

        await callback.answer(
            f"🎉 Siz yutdingiz! {game['multiplier']}x",
            show_alert=True
        )

@dp.callback_query_handler(lambda c: c.data == "cashout")
async def cashout(callback: types.CallbackQuery):
    uid = callback.from_user.id

    if uid not in mines_games:
        return

    game = mines_games[uid]

    profit = int(game["bet"] * game["multiplier"])

    cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                   (profit, uid))
    conn.commit()

    await callback.message.edit_text(
        f"💰 Yutuq olindi!\nMultiplier: {game['multiplier']}x\n+{profit}"
    )

    del mines_games[uid]

# ================= RUN =================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
