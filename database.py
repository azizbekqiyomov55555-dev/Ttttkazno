import asyncpg
from config import DATABASE_URL

class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        """Database connection pool yaratish"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            print("✅ PostgreSQL ga muvaffaqiyatli ulandi!")
        except Exception as e:
            print(f"❌ Database xatosi: {e}")
            raise

    async def init_tables(self):
        """Jadvallarni yaratish"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    balance DECIMAL(10, 2) DEFAULT 0,
                    referral_code VARCHAR(50) UNIQUE,
                    referred_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    service_type VARCHAR(50),
                    platform VARCHAR(50),
                    link TEXT,
                    quantity INTEGER,
                    price DECIMAL(10, 2),
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    amount DECIMAL(10, 2),
                    type VARCHAR(20),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            print("✅ Jadvallar yaratildi")

    async def add_user(self, user_id, username, first_name, referral_code=None, referred_by=None):
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''INSERT INTO users (user_id, username, first_name, referral_code, referred_by)
                   VALUES ($1, $2, $3, $4, $5) ON CONFLICT (user_id) DO NOTHING''',
                user_id, username, first_name, referral_code, referred_by
            )

    async def get_user(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)

    async def update_balance(self, user_id, amount):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET balance = balance + $1 WHERE user_id = $2',
                amount, user_id
            )

    async def add_order(self, user_id, service_type, platform, link, quantity, price):
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                '''INSERT INTO orders (user_id, service_type, platform, link, quantity, price)
                   VALUES ($1, $2, $3, $4, $5, $6) RETURNING order_id''',
                user_id, service_type, platform, link, quantity, price
            )
            return result

    async def get_user_orders(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                'SELECT * FROM orders WHERE user_id = $1 ORDER BY created_at DESC LIMIT 10',
                user_id
            )

    async def add_transaction(self, user_id, amount, type_, description):
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''INSERT INTO transactions (user_id, amount, type, description)
                   VALUES ($1, $2, $3, $4)''',
                user_id, amount, type_, description
            )

db = Database()
