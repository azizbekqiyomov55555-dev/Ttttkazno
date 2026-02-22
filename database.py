import aiosqlite

DB_PATH = "saleseen.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                phone TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_subscribed INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                original_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                discount_percent REAL,
                description TEXT,
                image_url TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(telegram_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username, full_name)
            VALUES (?, ?, ?)
        """, (telegram_id, username, full_name))
        await db.commit()

async def update_user_phone(telegram_id, phone):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET phone=? WHERE telegram_id=?", (phone, telegram_id))
        await db.commit()

async def get_user(telegram_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)) as cursor:
            return await cursor.fetchone()

async def get_all_subscribed_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT telegram_id FROM users WHERE is_subscribed=1") as cursor:
            return await cursor.fetchall()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()

async def add_product(name, original_price, sale_price, description, image_url=None):
    discount = round((original_price - sale_price) / original_price * 100, 1)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO products (name, original_price, sale_price, discount_percent, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, original_price, sale_price, discount, description, image_url))
        await db.commit()

async def get_active_products():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM products WHERE is_active=1") as cursor:
            return await cursor.fetchall()

async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM products") as cursor:
            return await cursor.fetchall()

async def delete_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,))
        await db.commit()

async def count_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]
