import random
import sqlite3
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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
        [KeyboardButton("💣 Mines")],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= GLOBAL =================
awaiting_bet = {}
mines_games = {}

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
        await message.answer("⏳ 24 soatda 1 marta!")
        return

    cursor.execute("UPDATE users SET balance=balance+100, last_bonus=? WHERE user_id=?",
                   (now, message.from_user.id))
    conn.commit()

    await message.answer("🎁 +100 coin qo‘shildi!")

# ================= GAMES =================
@dp.message_handler(lambda m: m.text == "🎮 O‘yinlar")
async def games_handler(message: types.Message):
    await message.answer("🎮 O‘yin tanlang:", reply_markup=games_menu())

@dp.message_handler(lambda m: m.text == "🔙 Orqaga")
async def back_handler(message: types.Message):
    await message.answer("🏠 Asosiy menyu", reply_markup=main_menu(message.from_user.id))

# ================= MINES START =================
@dp.message_handler(lambda m: m.text == "💣 Mines")
async def mines_start(message: types.Message):
    awaiting_bet[message.from_user.id] = True
    await message.answer("💵 Stavka kiriting (min 10):")

# ================= BET =================
@dp.message_handler()
async def universal(message: types.Message):
    uid = message.from_user.id
    text = message.text

    if uid in awaiting_bet and text.isdigit():
        bet = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka noto‘g‘ri")
            return

        bombs = random.sample(range(10), 4)

        mines_games[uid] = {
            "bet": bet,
            "bombs": bombs,
            "opened": 0,
            "multiplier": 1
        }

        keyboard = InlineKeyboardMarkup(row_width=5)

        for i in range(10):
            keyboard.insert(
                InlineKeyboardButton("📦", callback_data=f"mine_{i}")
            )

        keyboard.add(
            InlineKeyboardButton("💵 Pulni olish", callback_data="cashout")
        )

        await message.answer("📦 Qutini tanlang:", reply_markup=keyboard)
        del awaiting_bet[uid]
        return

# ================= CALLBACK =================
@dp.callback_query_handler(lambda c: c.data.startswith("mine_") or c.data == "cashout")
async def mines_callback(callback: types.CallbackQuery):
    uid = callback.from_user.id

    if uid not in mines_games:
        await callback.answer("O‘yin topilmadi", show_alert=True)
        return

    game = mines_games[uid]
    bet = game["bet"]
    bombs = game["bombs"]
    opened = game["opened"]

    # ===== CASHOUT =====
    if callback.data == "cashout":
        if opened == 0:
            await callback.answer("Hech narsa ochilmadi!", show_alert=True)
            return

        multiplier = game["multiplier"]
        win_amount = int(bet * multiplier)

        cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                       (win_amount, uid))
        conn.commit()

        await callback.message.edit_text(
            f"💵 Pul olindi!\nMultiplier: x{multiplier}\nYutuq: {win_amount}"
        )

        del mines_games[uid]
        return

    # ===== BOX CLICK =====
    index = int(callback.data.split("_")[1])

    if index in bombs:
        cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                       (bet, uid))
        conn.commit()

        # Bombalarni ko‘rsatish
        keyboard = InlineKeyboardMarkup(row_width=5)
        for i in range(10):
            if i in bombs:
                text = "💣"
            else:
                text = "✅"
            keyboard.insert(InlineKeyboardButton(text, callback_data="end"))

        await callback.message.edit_text(
            "💥 TUZOQGA TUSHDINGIZ!\nPul yo‘qotildi!",
            reply_markup=keyboard
        )

        del mines_games[uid]
        return

    # Safe box
    game["opened"] += 1

    if game["opened"] == 1:
        game["multiplier"] = 1.5
    elif game["opened"] == 2:
        game["multiplier"] = 2
    elif game["opened"] == 3:
        game["multiplier"] = 2.6
    elif game["opened"] >= 4:
        game["multiplier"] = 4

    # Klaviaturani yangilash
    keyboard = InlineKeyboardMarkup(row_width=5)

    for i in range(10):
        if i in bombs:
            text_btn = "📦"
        elif i < game["opened"]:
            text_btn = "✅"
        else:
            text_btn = "📦"

        keyboard.insert(
            InlineKeyboardButton(text_btn, callback_data=f"mine_{i}")
        )

    keyboard.add(
        InlineKeyboardButton("💵 Pulni olish", callback_data="cashout")
    )

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"Xavfsiz! x{game['multiplier']}")

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
