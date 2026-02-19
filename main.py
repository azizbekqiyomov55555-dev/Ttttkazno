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
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("🎮 O‘yinlar")
    ).add(
        KeyboardButton("🎁 Bonus"),
        KeyboardButton("👤 Profil")
    )

def games_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("🎲 Dice"), KeyboardButton("🎯 Dart")
    ).add(
        KeyboardButton("⚽ Penalty"), KeyboardButton("🎰 Slot")
    ).add(
        KeyboardButton("🪙 Coin"), KeyboardButton("🃏 BlackJack")
    ).add(
        KeyboardButton("🏀 Basket"), KeyboardButton("🎳 Bowling")
    ).add(
        KeyboardButton("🎮 Lucky"), KeyboardButton("💣 Mines")
    ).add(
        KeyboardButton("🔙 Orqaga")
    )

# ================= STORAGE =================

awaiting_bet = {}
current_game = {}
progress_games = {}
mines_games = {}

# ================= MINES =================

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

# ================= PROGRESS GAME KEYBOARD =================

def progress_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🎯 O‘ynash", callback_data="play_step"))
    kb.add(InlineKeyboardButton("💰 Yutuqni olish", callback_data="take_profit"))
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

# ================= MENU =================

@dp.message_handler(lambda m: m.text == "🎮 O‘yinlar")
async def games(message: types.Message):
    await message.answer("🎮 O‘yin tanlang:", reply_markup=games_menu())

# ================= UNIVERSAL =================

@dp.message_handler()
async def universal(message: types.Message):
    uid = message.from_user.id
    text = message.text

    if text == "🔙 Orqaga":
        await message.answer("🏠 Asosiy menyu", reply_markup=main_menu())
        return

    # MINES
    if text == "💣 Mines":
        mines_games[uid] = {"awaiting_bet": True}
        await message.answer("💵 Stavka kiriting (min 10):")
        return

    # OTHER GAMES
    if text in ["🎲 Dice","🎯 Dart","⚽ Penalty","🎰 Slot",
                "🪙 Coin","🃏 BlackJack","🏀 Basket",
                "🎳 Bowling","🎮 Lucky"]:
        awaiting_bet[uid] = True
        current_game[uid] = text
        await message.answer("💵 Stavka kiriting (min 10):")
        return

    # MINES BET
    if uid in mines_games and mines_games[uid].get("awaiting_bet"):
        if not text.isdigit():
            return

        bet = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka noto‘g‘ri")
            return

        mines_games[uid] = {
            "bet": bet,
            "mines": random.sample(range(15), 8),
            "opened": [],
            "multiplier": 1.0
        }

        await message.answer(
            "💣 O‘yin boshlandi!\nMultiplier: 1.0x",
            reply_markup=mines_keyboard(mines_games[uid])
        )
        return

    # OTHER GAME BET
    if uid in awaiting_bet and text.isdigit():
        bet = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka noto‘g‘ri")
            return

        progress_games[uid] = {
            "bet": bet,
            "step": 0,
            "multiplier": 1.0
        }

        del awaiting_bet[uid]

        await message.answer(
            "🎯 O‘yin boshlandi!\nMultiplier: 1.0x",
            reply_markup=progress_keyboard()
        )

# ================= PROGRESS CALLBACK =================

@dp.callback_query_handler(lambda c: c.data == "play_step")
async def play_step(callback: types.CallbackQuery):
    await callback.answer()

    uid = callback.from_user.id
    if uid not in progress_games:
        return

    game = progress_games[uid]
    game["step"] += 1

    if game["step"] == 1:
        game["multiplier"] = 1.5
    elif game["step"] == 2:
        game["multiplier"] = 2.0
    elif game["step"] == 3:
        game["multiplier"] = 3.0
    else:
        # LOSE
        cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                       (game["bet"], uid))
        conn.commit()

        await callback.message.edit_text("💥 YUTQAZDINGIZ!")
        del progress_games[uid]
        return

    current_win = int(game["bet"] * game["multiplier"])

    await callback.message.edit_text(
        f"🎯 O‘yin davom etmoqda\n"
        f"📈 Multiplier: {game['multiplier']}x\n"
        f"💰 Hozirgi yutuq: {current_win}",
        reply_markup=progress_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == "take_profit")
async def take_profit(callback: types.CallbackQuery):
    await callback.answer()

    uid = callback.from_user.id
    if uid not in progress_games:
        return

    game = progress_games[uid]
    profit = int(game["bet"] * game["multiplier"])

    cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                   (profit, uid))
    conn.commit()

    await callback.message.edit_text(
        f"💰 Siz {game['multiplier']}x yutdingiz!\n+{profit}"
    )

    del progress_games[uid]

# ================= RUN =================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
