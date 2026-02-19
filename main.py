import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

games = {}

def keyboard(game):
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
            InlineKeyboardButton(text, callback_data=f"m_{i}")
        )

    kb.add(*buttons)
    kb.add(InlineKeyboardButton("💰 Olish", callback_data="cash"))
    return kb


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    games[message.from_user.id] = {
        "bet": 100,
        "mines": random.sample(range(15), 8),
        "opened": [],
        "multiplier": 1.0
    }

    await message.answer(
        "💣 Mines boshlandi\nMultiplier: 1.0x",
        reply_markup=keyboard(games[message.from_user.id])
    )


@dp.callback_query_handler(lambda c: c.data.startswith("m_"))
async def open_box(callback: types.CallbackQuery):
    await callback.answer()  # MUHIM

    uid = callback.from_user.id
    game = games.get(uid)

    if not game:
        return

    index = int(callback.data.split("_")[1])

    if index in game["opened"]:
        return

    game["opened"].append(index)

    if index in game["mines"]:
        game["opened"] = list(range(15))
        await callback.message.edit_text(
            "💥 Portladi!",
            reply_markup=keyboard(game)
        )
        del games[uid]
        return

    game["multiplier"] += 0.5

    await callback.message.edit_text(
        f"💣 Mines\nMultiplier: {game['multiplier']}x",
        reply_markup=keyboard(game)
    )


@dp.callback_query_handler(lambda c: c.data == "cash")
async def cash(callback: types.CallbackQuery):
    await callback.answer()

    uid = callback.from_user.id
    game = games.get(uid)

    if not game:
        return

    await callback.message.edit_text(
        f"💰 Siz {game['multiplier']}x yutdingiz!"
    )

    del games[uid]


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
