import random
import sqlite3
import time
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    card TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()

# ================= MENU =================
def main_menu(user_id):
    keyboard = [
        [KeyboardButton("🎮 O‘yinlar")],
        [KeyboardButton("🎁 Bonus")],
        [KeyboardButton("👤 Profil")],
        [KeyboardButton("💸 Pul chiqarish")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("👑 Admin Panel")])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

awaiting_bet = set()
awaiting_withdraw = {}

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                   (message.from_user.id,))
    conn.commit()

    await message.answer("🎰 Casino Bot", reply_markup=main_menu(message.from_user.id))

# ================= PROFIL =================
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

# ================= GAME =================
@dp.message_handler(lambda m: m.text == "🎮 O‘yinlar")
async def game_start(message: types.Message):
    awaiting_bet.add(message.from_user.id)
    await message.answer("💵 Stavka kiriting (min 10):")

@dp.message_handler()
async def universal(message: types.Message):
    uid = message.from_user.id
    text = message.text

    # BET
    if uid in awaiting_bet and text.isdigit():
        awaiting_bet.remove(uid)
        bet = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bet < 10 or bet > bal:
            await message.answer("❌ Stavka xato")
            return

        win = random.random() < 0.4

        if win:
            cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                           (bet, uid))
            result = f"🎉 YUTDINGIZ! +{bet}"
        else:
            cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                           (bet, uid))
            result = f"😢 YUTQAZDINGIZ! -{bet}"

        conn.commit()
        await message.answer(result)
        return

    # ================= WITHDRAW =================
    if text == "💸 Pul chiqarish":
        awaiting_withdraw[uid] = {}
        await message.answer("💰 Qancha miqdor chiqarmoqchisiz?")
        return

    if uid in awaiting_withdraw and "amount" not in awaiting_withdraw[uid]:
        if not text.isdigit():
            return

        amount = int(text)

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cursor.fetchone()[0]

        if amount > bal or amount < 100:
            await message.answer("❌ Noto‘g‘ri summa (min 100)")
            return

        awaiting_withdraw[uid]["amount"] = amount
        await message.answer("💳 Karta raqamini kiriting:")
        return

    if uid in awaiting_withdraw and "card" not in awaiting_withdraw[uid]:
        amount = awaiting_withdraw[uid]["amount"]
        card = text

        cursor.execute("INSERT INTO withdraws (user_id, amount, card) VALUES (?, ?, ?)",
                       (uid, amount, card))
        cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?",
                       (amount, uid))
        conn.commit()

        await message.answer("✅ So‘rov yuborildi. Admin tasdiqlaydi.")
        await bot.send_message(ADMIN_ID,
                               f"💸 Yangi withdraw!\nUser: {uid}\nSumma: {amount}\nKarta: {card}")

        del awaiting_withdraw[uid]
        return

    # ================= ADMIN =================
    if text == "👑 Admin Panel" and uid == ADMIN_ID:
        cursor.execute("SELECT id,user_id,amount,card FROM withdraws WHERE status='pending'")
        rows = cursor.fetchall()

        if not rows:
            await message.answer("❌ Pending withdraw yo‘q")
            return

        for row in rows:
            wid, user_id, amount, card = row
            await message.answer(
                f"ID: {wid}\nUser: {user_id}\nSumma: {amount}\nKarta: {card}\n\nTasdiqlash: /ok_{wid}"
            )
        return

# ================= APPROVE =================
@dp.message_handler(lambda m: m.text.startswith("/ok_"))
async def approve(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    wid = int(message.text.split("_")[1])

    cursor.execute("UPDATE withdraws SET status='approved' WHERE id=?", (wid,))
    conn.commit()

    await message.answer("✅ Tasdiqlandi!")

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
