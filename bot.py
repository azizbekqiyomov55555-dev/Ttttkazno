import asyncio
import aiohttp
import aiosqlite
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import *
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN="8001146442:AAG5oPF_FmKsDZC-yaHgbNIMl8xU0IrLFzI"
ADMIN_ID=8537782289
API_URL="https://saleseen.uz/api/v2"
API_KEY="16f2daabf5bf7fb4494fdffc5bcaf6bc"

logging.basicConfig(level=logging.INFO)

bot=Bot(token=TOKEN,parse_mode="HTML")
dp=Dispatcher(storage=MemoryStorage())

# ================= DB =================
async def init_db():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            balance REAL DEFAULT 0,
            referal_from INTEGER,
            created_at TEXT)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS services(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            api_id TEXT,
            price REAL,
            percent REAL DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_id INTEGER,
            api_order_id TEXT,
            quantity INTEGER,
            link TEXT,
            total REAL,
            status TEXT,
            created_at TEXT)""")
        await db.commit()

# ================= STATES =================
class AddService(StatesGroup):
    category=State()
    name=State()
    api_id=State()
    price=State()

class AddPercent(StatesGroup):
    service_id=State()
    percent=State()

class OrderState(StatesGroup):
    service_id=State()
    quantity=State()
    link=State()

class TopUpState(StatesGroup):
    amount=State()
    receipt=State()

# ================= MENUS =================
def user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Xizmatlar")],
            [KeyboardButton(text="💰 Hisobim"),KeyboardButton(text="💳 Hisob To‘ldirish")],
            [KeyboardButton(text="🛒 Buyurtmalarim")],
            [KeyboardButton(text="👥 Referal")]
        ],resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Xizmat qo‘shish")],
            [KeyboardButton(text="❌ Xizmat o‘chirish")],
            [KeyboardButton(text="💹 Foiz qo‘shish")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="⬅ Ortga")]
        ],resize_keyboard=True)

# ================= START =================
@dp.message(Command("start"))
async def start(message:types.Message):
    args=message.text.split()
    ref=None
    if len(args)>1:
        try: ref=int(args[1])
        except: ref=None
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("INSERT OR IGNORE INTO users VALUES(?,?,?,?,?)",
                         (message.from_user.id,
                          message.from_user.full_name,
                          0,
                          ref,
                          datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()
    await message.answer("Assalomu alaykum 👋",reply_markup=user_menu())

# ================= ADMIN =================
@dp.message(Command("admin"))
async def admin(message:types.Message):
    if message.from_user.id==ADMIN_ID:
        await message.answer("Admin panel",reply_markup=admin_menu())

@dp.message(F.text=="⬅ Ortga")
async def back(message:types.Message):
    await message.answer("Asosiy menyu",reply_markup=user_menu())

# ================= BALANCE =================
@dp.message(F.text=="💰 Hisobim")
async def balance(message:types.Message):
    async with aiosqlite.connect("db.sqlite") as db:
        cur=await db.execute("SELECT balance FROM users WHERE user_id=?",(message.from_user.id,))
        bal=(await cur.fetchone())[0]
    await message.answer(f"💰 Balans: <b>{bal}</b> so'm")

# ================= ADD SERVICE =================
@dp.message(F.text=="➕ Xizmat qo‘shish")
async def add_s1(m:types.Message,state:FSMContext):
    if m.from_user.id!=ADMIN_ID:return
    await m.answer("Kategoriya:")
    await state.set_state(AddService.category)

@dp.message(AddService.category)
async def add_s2(m,state):
    await state.update_data(category=m.text)
    await m.answer("Nomi:")
    await state.set_state(AddService.name)

@dp.message(AddService.name)
async def add_s3(m,state):
    await state.update_data(name=m.text)
    await m.answer("API ID:")
    await state.set_state(AddService.api_id)

@dp.message(AddService.api_id)
async def add_s4(m,state):
    await state.update_data(api_id=m.text)
    await m.answer("Narx:")
    await state.set_state(AddService.price)

@dp.message(AddService.price)
async def add_s5(m,state):
    d=await state.get_data()
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("INSERT INTO services(category,name,api_id,price) VALUES(?,?,?,?)",
                         (d["category"],d["name"],d["api_id"],float(m.text)))
        await db.commit()
    await m.answer("Qo‘shildi")
    await state.clear()

# ================= DELETE =================
@dp.message(F.text=="❌ Xizmat o‘chirish")
async def del_menu(m):
    if m.from_user.id!=ADMIN_ID:return
    async with aiosqlite.connect("db.sqlite") as db:
        cur=await db.execute("SELECT id,name FROM services")
        rows=await cur.fetchall()
    kb=[[InlineKeyboardButton(text=r[1],callback_data=f"del_{r[0]}")]for r in rows]
    await m.answer("Tanlang:",reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("del_"))
async def delete(cb):
    sid=cb.data.split("_")[1]
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("DELETE FROM services WHERE id=?",(sid,))
        await db.commit()
    await cb.message.edit_text("O‘chirildi")

# ================= SHOW SERVICES =================
@dp.message(F.text=="🛍 Xizmatlar")
async def show(m):
    async with aiosqlite.connect("db.sqlite") as db:
        cur=await db.execute("SELECT id,name,price FROM services")
        rows=await cur.fetchall()
    kb=[[InlineKeyboardButton(text=f"{r[1]}-{r[2]}",callback_data=f"order_{r[0]}")]for r in rows]
    await m.answer("Tanlang:",reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# ================= ORDER =================
@dp.callback_query(F.data.startswith("order_"))
async def o1(cb,state):
    await state.update_data(service_id=cb.data.split("_")[1])
    await cb.message.answer("Miqdor:")
    await state.set_state(OrderState.quantity)

@dp.message(OrderState.quantity)
async def o2(m,state):
    await state.update_data(quantity=int(m.text))
    await m.answer("Link:")
    await state.set_state(OrderState.link)

@dp.message(OrderState.link)
async def o3(m,state):
    d=await state.get_data()
    async with aiosqlite.connect("db.sqlite") as db:
        cur=await db.execute("SELECT name,price,api_id FROM services WHERE id=?",(d["service_id"],))
        s=await cur.fetchone()
        total=s[1]*d["quantity"]
        cur=await db.execute("SELECT balance FROM users WHERE user_id=?",(m.from_user.id,))
        bal=(await cur.fetchone())[0]
        if bal<total:
            await m.answer("Balans yetarli emas")
            await state.clear()
            return
        payload={"key":API_KEY,"action":"add","service":s[2],"link":m.text,"quantity":d["quantity"]}
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL,data=payload) as r:
                res=await r.json()
        await db.execute("UPDATE users SET balance=balance-? WHERE user_id=?",(total,m.from_user.id))
        await db.execute("""INSERT INTO orders(user_id,service_id,api_order_id,
                          quantity,link,total,status,created_at)
                          VALUES(?,?,?,?,?,?,?,?)""",
                          (m.from_user.id,d["service_id"],res.get("order"),
                           d["quantity"],m.text,total,"Yuborildi",
                           datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()
    await m.answer("Buyurtma qabul qilindi")
    await state.clear()

# ================= MY ORDERS =================
@dp.message(F.text=="🛒 Buyurtmalarim")
async def my_orders(m):
    async with aiosqlite.connect("db.sqlite") as db:
        cur=await db.execute("""SELECT s.name,o.quantity,o.total,o.status
                                FROM orders o JOIN services s
                                ON o.service_id=s.id
                                WHERE o.user_id=?""",(m.from_user.id,))
        rows=await cur.fetchall()
    txt="Buyurtmalar:\n"
    for r in rows:
        txt+=f"{r[0]} | {r[1]} | {r[2]} | {r[3]}\n"
    await m.answer(txt)

# ================= REFERAL =================
@dp.message(F.text=="👥 Referal")
async def ref(m):
    link=f"https://t.me/{(await bot.get_me()).username}?start={m.from_user.id}"
    await m.answer(f"Referal link:\n{link}")

# ================= PAYMENT (MANUAL) =================
@dp.message(F.text=="💳 Hisob To‘ldirish")
async def t1(m,state):
    await m.answer("Miqdor:")
    await state.set_state(TopUpState.amount)

@dp.message(TopUpState.amount)
async def t2(m,state):
    await state.update_data(amount=float(m.text))
    await m.answer("Chek rasm yuboring:")
    await state.set_state(TopUpState.receipt)

@dp.message(TopUpState.receipt,F.photo)
async def t3(m,state):
    d=await state.get_data()
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Tasdiq",callback_data=f"pay_{m.from_user.id}_{d['amount']}")]
    ])
    await bot.send_photo(ADMIN_ID,m.photo[-1].file_id,
                         caption=f"{m.from_user.id} {d['amount']}",reply_markup=kb)
    await m.answer("Admin tasdiqlaydi")
    await state.clear()

@dp.callback_query(F.data.startswith("pay_"))
async def pay(cb):
    _,uid,amount=cb.data.split("_")
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("UPDATE users SET balance=balance+? WHERE user_id=?",(float(amount),int(uid)))
        await db.commit()
    await bot.send_message(int(uid),"Balans to‘ldirildi")
    await cb.message.edit_caption(cb.message.caption+"\nTasdiqlandi")

# ================= STAT =================
@dp.message(F.text=="📊 Statistika")
async def stat(m):
    if m.from_user.id!=ADMIN_ID:return
    async with aiosqlite.connect("db.sqlite") as db:
        u=(await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        o=(await (await db.execute("SELECT COUNT(*) FROM orders")).fetchone())[0]
        s=(await (await db.execute("SELECT SUM(total) FROM orders")).fetchone())[0]
    await m.answer(f"Users:{u}\nOrders:{o}\nSavdo:{s or 0}")

# ================= AUTO STATUS =================
async def auto_status():
    while True:
        await asyncio.sleep(60)
        async with aiosqlite.connect("db.sqlite") as db:
            cur=await db.execute("SELECT id,api_order_id FROM orders WHERE status='Yuborildi'")
            rows=await cur.fetchall()
            for r in rows:
                payload={"key":API_KEY,"action":"status","order":r[1]}
                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL,data=payload) as resp:
                        res=await resp.json()
                if res.get("status"):
                    await db.execute("UPDATE orders SET status=? WHERE id=?",
                                     (res.get("status"),r[0]))
            await db.commit()

# ================= MAIN =================
async def main():
    await init_db()
    asyncio.create_task(auto_status())
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())
