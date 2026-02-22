# 🛍 SaleSeenBot — Telegram Sale Bot

## 📁 Fayl tuzilmasi

```
saleseen_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Token va admin ID
├── database.py         # SQLite ma'lumotlar bazasi
├── keyboards.py        # Tugmalar
├── requirements.txt    # Kutubxonalar
└── handlers/
    ├── user.py         # Foydalanuvchi handlerlari
    └── admin.py        # Admin handlerlari
```

## ⚙️ O'rnatish

```bash
pip install -r requirements.txt
```

## 🔧 Sozlash

1. `config.py` faylini oching
2. `BOT_TOKEN` ga @BotFather dan olingan tokenni qo'ying
3. `ADMIN_IDS` ga o'z Telegram ID ingizni qo'ying

```python
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
ADMIN_IDS = [123456789]  # sizning ID
```

> 💡 Telegram ID ni bilish uchun @userinfobot ga /start yuboring

## 🚀 Ishga tushirish

```bash
python bot.py
```

## 👤 Foydalanuvchi imkoniyatlari

- `/start` — Ro'yxatdan o'tish (telefon raqam bilan)
- 🔥 Chegirmalar — Joriy chegirmali mahsulotlar
- 📦 Mahsulotlar — Barcha mahsulotlar
- 🔔 Obuna — Bildirishnoma holati
- 👤 Profilim — Profil ma'lumotlari

## 👑 Admin imkoniyatlari

`/admin` buyrug'i orqali kirish:

- ➕ Mahsulot qo'shish — yangi mahsulot + chegirma qo'shish
- 📋 Mahsulotlar ro'yxati — ro'yxat va o'chirish
- 📢 Xabar yuborish — barcha obunachilarga broadcast
- 📊 Statistika — foydalanuvchilar soni va faol mahsulotlar
- 👥 Foydalanuvchilar — ro'yxat ko'rish
