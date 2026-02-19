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

# ================= SIMPLE GAMES =================

GAME_RATES = {
    "🎲 Dice": 0.45,
    "🎯 Dart": 0.40,
    "⚽ Penalty": 0.50,
    "🎰 Slot": 0.35,
    "🪙 Coin": 0.50,
    "🃏 BlackJack": 0.42,
    "🏀 Basket": 0.48,
    "🎳 Bowling": 0.46,
    "🎮 Lucky": 0.30
}

awaiting_bet = {}
current_game = {}

# ================= MINES =================

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

    # MINES START
    if text == "💣 Mines":
        mines_games[uid] = {"awaiting_bet": True}
        await message.answer("💵 Stavka kiriting (min 10):")
        return

    # OTHER GAMES
    if text in GAME_RATES:
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

        game = current_game[uid]
        win = random.random() < GAME_RATES[game]

        if win:
            cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                           (bet, uid))
            result = f"🎉 YUTDINGIZ! +{bet}"
        else:
            cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                           (bet, uid))
            result = f"😢 YUTQAZDINGIZ! -{bet}"

        conn.commit()

        del awaiting_bet[uid]
        del current_game[uid]

        await message.answer(result)

# ================= MINES CALLBACK =================

@dp.callback_query_handler(lambda c: c.data.startswith("mine_"))
async def open_mine(callback: types.CallbackQuery):
    await callback.answer()  # MUHIM!!!

    uid = callback.from_user.id
    if uid not in mines_games:
        return

    game = mines_games[uid]
    index = int(callback.data.split("_")[1])

    if index in game["opened"]:
        return

    game["opened"].append(index)

    # AGAR MINA
    if index in game["mines"]:
        cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                       (game["bet"], uid))
        conn.commit()

        game["opened"] = list(range(15))

        await callback.message.edit_text(
            f"💥 Portladi!\n😢 -{game['bet']}",
            reply_markup=mines_keyboard(game)
        )

        del mines_games[uid]
        return

    # AGAR XAVFSIZ
    game["multiplier"] += 0.5
    current_win = int(game["bet"] * game["multiplier"])

    await callback.message.edit_text(
        f"💣 Mines\n\n"
        f"📈 Multiplier: {game['multiplier']}x\n"
        f"💰 Hozirgi yutuq: {current_win}\n\n"
        f"Qutini davom ettiring yoki yutuqni oling 👇",
        reply_markup=mines_keyboard(game)
    )

# ================= CASHOUT =================

@dp.callback_query_handler(lambda c: c.data == "cashout")
async def cashout(callback: types.CallbackQuery):
    await callback.answer()  # MUHIM!!!

    uid = callback.from_user.id
    if uid not in mines_games:
        return

    game = mines_games[uid]
    profit = int(game["bet"] * game["multiplier"])

    cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                   (profit, uid))
    conn.commit()

    await callback.message.edit_text(
        f"💰 Siz {game['multiplier']}x yutdingiz!\n+{profit}"
    )

    del mines_games[uid]

# ================= RUN =================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
