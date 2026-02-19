import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils import executor

# ================== CONFIG ==================

TOKEN = "BOT_TOKENINGIZNI_QO‘YING"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ================== DATABASE ==================

conn = sqlite3.connect("casino.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 1000
)
""")
conn.commit()

# ================== STORAGE ==================

awaiting_bet = {}
games = {}

# ================== MENUS ==================

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🎮 O‘yin"))
    kb.add(KeyboardButton("👤 Profil"))
    return kb

def game_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎯 O‘ynash", callback_data="play"))
    kb.add(InlineKeyboardButton("💰 Yutuqni olish", callback_data="cashout"))
    return kb

# ================== START ==================

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                   (msg.from_user.id,))
    conn.commit()

    await msg.answer("🎰 Casino Bot", reply_markup=main_menu())

# ================== PROFILE ==================

@dp.message_handler(lambda m: m.text == "👤 Profil")
async def profile(msg: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?",
                   (msg.from_user.id,))
    bal = cursor.fetchone()[0]
    await msg.answer(f"💰 Balans: {bal}")

# ================== O‘YIN BOSHLASH ==================

@dp.message_handler(lambda m: m.text == "🎮 O‘yin")
async def game_start(msg: types.Message):
    awaiting_bet[msg.from_user.id] = True
    await msg.answer("💵 Stavka kiriting (min 10):")

# ================== STAVKA ==================

@dp.message_handler()
async def bet_handler(msg: types.Message):
    uid = msg.from_user.id

    if uid in awaiting_bet and msg.text.isdigit():
        bet = int(msg.text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await msg.answer("❌ Stavka noto‘g‘ri")
            return

        # balansdan vaqtincha ayirmaymiz (yutqazganda ayriladi)
        games[uid] = {
            "bet": bet,
            "step": 0,
            "multiplier": 1.0
        }

        del awaiting_bet[uid]

        await msg.answer(
            "🎯 O‘yin boshlandi\nMultiplier: 1.0x",
            reply_markup=game_keyboard()
        )

# ================== PLAY ==================

@dp.callback_query_handler(lambda c: c.data == "play")
async def play(callback: types.CallbackQuery):
    await callback.answer()  # ❗ MUHIM

    uid = callback.from_user.id

    if uid not in games:
        return

    game = games[uid]
    game["step"] += 1

    if game["step"] == 1:
        game["multiplier"] = 1.5
    elif game["step"] == 2:
        game["multiplier"] = 2
    elif game["step"] == 3:
        game["multiplier"] = 3
    else:
        # 4-bosishda yutqazadi
        cursor.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id=?",
            (game["bet"], uid)
        )
        conn.commit()

        await callback.message.edit_text("💥 YUTQAZDINGIZ!")
        del games[uid]
        return

    win = int(game["bet"] * game["multiplier"])

    await callback.message.edit_text(
        f"🎉 Siz {game['multiplier']}x yutdingiz!\n"
        f"💰 Hozirgi yutuq: {win}",
        reply_markup=game_keyboard()
    )

# ================== CASHOUT ==================

@dp.callback_query_handler(lambda c: c.data == "cashout")
async def cashout(callback: types.CallbackQuery):
    await callback.answer()

    uid = callback.from_user.id

    if uid not in games:
        return

    game = games[uid]
    win = int(game["bet"] * game["multiplier"])

    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id=?",
        (win, uid)
    )
    conn.commit()

    await callback.message.edit_text(
        f"💰 Siz {game['multiplier']}x bilan {win} coin oldingiz!"
    )

    del games[uid]

# ================== RUN ==================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
