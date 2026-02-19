import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = "TOKENINGIZNI_SHU_YERGA_YOZING"

# O'yin ma'lumotlari
user_game = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 O'yinlar", callback_data="games")]
    ]
    await update.message.reply_text(
        "Xush kelibsiz!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# O'yinlar menyusi
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💣 Mines", callback_data="mines")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
    ]

    await query.edit_message_text(
        "O'yin tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Mines tanlandi
async def mines_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("💰 Stavka kiriting (min 10):")

    context.user_data["awaiting_bet"] = True

# Stavka qabul qilish
async def get_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_bet"):
        return

    bet = int(update.message.text)

    if bet < 10:
        await update.message.reply_text("❌ Minimal stavka 10!")
        return

    context.user_data["awaiting_bet"] = False
    context.user_data["bet"] = bet

    # Yutuq quti
    win_box = random.randint(0, 8)
    context.user_data["win_box"] = win_box
    context.user_data["opened"] = False

    # 3x3 katta kvadrat qutilar
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            index = i * 3 + j
            row.append(
                InlineKeyboardButton(
                    "📦 QUTI",
                    callback_data=f"box_{index}"
                )
            )
        keyboard.append(row)

    keyboard.append(
        [InlineKeyboardButton("💰 Pulni olish", callback_data="cashout")]
    )

    await update.message.reply_text(
        "📦 Qutini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Quti bosilganda
async def open_box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("opened"):
        return

    index = int(query.data.split("_")[1])
    win_box = context.user_data["win_box"]
    bet = context.user_data["bet"]

    context.user_data["opened"] = True

    if index == win_box:
        win_amount = bet * 2
        text = f"🎉 Siz {win_amount} so‘m yutdingiz!"
    else:
        text = "💣 Mina chiqdi! Yutqazdingiz!"

    # Qutilarni blok qilish
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            row.append(
                InlineKeyboardButton(
                    "❌",
                    callback_data="blocked"
                )
            )
        keyboard.append(row)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Pulni olish
async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get("opened"):
        await query.edit_message_text("O'yin tugadi!")
    else:
        await query.edit_message_text("Pulni oldingiz!")

# Orqaga
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🎮 O'yinlar", callback_data="games")]
    ]

    await query.edit_message_text(
        "Asosiy menyu",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    if data == "games":
        await games_menu(update, context)
    elif data == "mines":
        await mines_start(update, context)
    elif data.startswith("box_"):
        await open_box(update, context)
    elif data == "cashout":
        await cashout(update, context)
    elif data == "back":
        await back(update, context)

# MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_bet))

print("Bot ishga tushdi...")
app.run_polling()
