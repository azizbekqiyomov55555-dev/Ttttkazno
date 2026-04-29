# Fly.io ga deploy qilish (Telegram Obmen Bot)

## 1. Fly CLI o'rnating
**Windows (PowerShell):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```
**Mac/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

## 2. Login
```bash
fly auth login
```

## 3. Loyihaga kiring
ZIP ni oching va papkaga kiring:
```bash
cd Ttttkazno-fly
```

## 4. Ilova nomini o'zgartiring (ixtiyoriy)
`fly.toml` faylida `app = "obmen-bot"` ni o'zingizning unikal nomingizga o'zgartiring (masalan: `app = "ali-obmen-bot"`).

## 5. Ilovani yarating
```bash
fly apps create sizning-bot-nomingiz
```
Yoki avtomatik:
```bash
fly launch --no-deploy --copy-config --name sizning-bot-nomingiz --region fra
```

## 6. Volume yarating (ma'lumotlar uchun)
```bash
fly volumes create bot_data --size 1 --region fra
```

## 7. Maxfiy tokenlarni o'rnating (MUHIM — xavfsizlik)
Kodda token "default" qilib qo'yilgan, lekin uni env orqali yuborish to'g'riroq:
```bash
fly secrets set OBMEN_BOT_TOKEN="8298808352:AAHkD1lraFUAy8xyToDBYX0CMo4twRQ2yYE"
fly secrets set OBMEN_ADMIN_ID="8537782289"
```

## 8. Deploy
```bash
fly deploy
```

## 9. Loglarni ko'rish
```bash
fly logs
```

## 10. Statusni tekshirish
```bash
fly status
```

## Yangilash
Kodni o'zgartirgandan keyin yana:
```bash
fly deploy
```

## Eslatma
- Bot **polling** rejimida ishlaydi (webhook emas) — port ochish shart emas.
- `bot_data/` papkasidagi JSON fayllar volume da doimiy saqlanadi.
- Free plan: 256MB RAM, shared CPU yetarli.
