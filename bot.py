import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "BOT_TOKENINGIZNI_BU_YERGA_QOYING"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Oddiy baza (real loyiha uchun DB ishlating)
users_balance = {}
used_promocodes = set()
valid_promocodes = {
    "Ramazon3": 3000,
    "BONUS10": 10000
}

# ====== STATE ======
class PromoState(StatesGroup):
    waiting_for_code = State()

# ====== MENU ======
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Xizmatlar"), KeyboardButton(text="📱 Nomer olish")],
        [KeyboardButton(text="🛒 Buyurtmalarim"), KeyboardButton(text="👥 Pul ishlash")],
        [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Hisob To'ldirish")],
        [KeyboardButton(text="📞 Murojaat"), KeyboardButton(text="☎️ Qo'llab-quvvatlash")],
        [KeyboardButton(text="🤝 Hamkorlik")]
    ],
    resize_keyboard=True
)

# ====== START ======
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_balance:
        users_balance[user_id] = 0
    await message.answer("Assalomu alaykum! Botga xush kelibsiz.", reply_markup=main_menu)

# ====== HISOBIM ======
@dp.message(lambda msg: msg.text == "💰 Hisobim")
async def balance_handler(message: types.Message):
    balance = users_balance.get(message.from_user.id, 0)
    await message.answer(f"💰 Sizning hisobingiz: {balance} so'm\n\nPromo kod kiritish uchun /promo ni bosing.")

# ====== PROMO BUYRUG'I ======
@dp.message(Command("promo"))
async def promo_start(message: types.Message, state: FSMContext):
    await message.answer("🎟 Promo kodni kiriting:")
    await state.set_state(PromoState.waiting_for_code)

@dp.message(PromoState.waiting_for_code)
async def process_promo(message: types.Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id

    if code in used_promocodes:
        await message.answer("❌ Bu promokod ishlatilib bo‘lingan!")
    elif code in valid_promocodes:
        amount = valid_promocodes[code]
        users_balance[user_id] += amount
        used_promocodes.add(code)
        await message.answer(f"✅ Promo kod qabul qilindi!\n💰 +{amount} so'm qo‘shildi.")
    else:
        await message.answer("❌ Promo kod noto‘g‘ri!")

    await state.clear()

# ====== QO'LLAB-QUVVATLASH ======
@dp.message(lambda msg: msg.text == "☎️ Qo'llab-quvvatlash")
async def support_handler(message: types.Message):
    await message.answer("📞 Admin: @SaleContact\n📢 Yangiliklar: @Sale_Seen")

# ====== RUN ======
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
