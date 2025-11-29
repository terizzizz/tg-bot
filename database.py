import aiosqlite
import json
from datetime import datetime
from config import DATABASE_PATH, ROLE_USER, STATUS_PENDING


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Пользователи
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    role TEXT DEFAULT '{ROLE_USER}',
                    phone TEXT,
                    city TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Дети
            await db.execute("""
                CREATE TABLE IF NOT EXISTS children (
                    child_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_id INTEGER,
                    name TEXT NOT NULL,
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES users(user_id)
                )
            """)

            # Образовательные центры
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS centers (
                    center_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER,
                    name TEXT NOT NULL,
                    city TEXT,
                    address TEXT,
                    phone TEXT,
                    category TEXT,
                    description TEXT,
                    logo TEXT,
                    status TEXT DEFAULT '{STATUS_PENDING}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (partner_id) REFERENCES users(user_id)
                )
            """)

            # Преподаватели
            await db.execute("""
                CREATE TABLE IF NOT EXISTS teachers (
                    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    center_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (center_id) REFERENCES centers(center_id)
                )
            """)

            # Курсы
            await db.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    center_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    age_min INTEGER,
                    age_max INTEGER,
                    requirements TEXT,
                    schedule TEXT,
                    rating REAL DEFAULT 0,
                    price_4 INTEGER,
                    price_8 INTEGER,
                    price_unlimited INTEGER,
                    photo TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (center_id) REFERENCES centers(center_id)
                )
            """)

            # Абонементы
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    child_id INTEGER,
                    course_id INTEGER,
                    center_id INTEGER,
                    tariff TEXT,
                    lessons_total INTEGER,
                    lessons_remaining INTEGER,
                    qr_code TEXT UNIQUE,
                    status TEXT DEFAULT 'active',
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (child_id) REFERENCES children(child_id),
                    FOREIGN KEY (course_id) REFERENCES courses(course_id),
                    FOREIGN KEY (center_id) REFERENCES centers(center_id)
                )
            """)

            # Посещения
            await db.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER,
                    user_id INTEGER,
                    child_id INTEGER,
                    center_id INTEGER,
                    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (child_id) REFERENCES children(child_id),
                    FOREIGN KEY (center_id) REFERENCES centers(center_id)
                )
            """)

            # Платежи
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id INTEGER,
                    user_id INTEGER,
                    amount REAL,
                    currency TEXT DEFAULT 'KZT',
                    method TEXT,
                    status TEXT DEFAULT 'pending',
                    transaction_id TEXT,
                    invoice_id TEXT,
                    airba_payment_id TEXT,
                    redirect_url TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Возвраты платежей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payment_refunds (
                    refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id INTEGER,
                    airba_refund_id TEXT,
                    ext_id TEXT,
                    amount REAL,
                    reason TEXT,
                    status TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (payment_id) REFERENCES payments(payment_id)
                )
            """)

            # Отзывы
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER,
                    user_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(course_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            await db.commit()

    # Методы для работы с пользователями
    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def create_user(self, user_id: int, username: str = None, full_name: str = None, role: str = ROLE_USER):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, full_name, role)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, full_name, role))
            await db.commit()

    async def update_user_role(self, user_id: int, role: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
            await db.commit()

    async def update_user_city(self, user_id: int, city: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET city = ? WHERE user_id = ?", (city, user_id))
            await db.commit()

    # Методы для работы с детьми
    async def add_child(self, parent_id: int, name: str, age: int):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO children (parent_id, name, age)
                VALUES (?, ?, ?)
            """, (parent_id, name, age))
            await db.commit()
            return cursor.lastrowid

    async def get_children(self, parent_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM children WHERE parent_id = ?", (parent_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_child(self, child_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM children WHERE child_id = ?", (child_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # Методы для работы с центрами
    async def create_center(self, partner_id: int, data: dict):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO centers (partner_id, name, city, address, phone, category, description, logo, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                partner_id,
                data.get("name"),
                data.get("city"),
                data.get("address"),
                data.get("phone"),
                data.get("category"),
                data.get("description"),
                data.get("logo"),
                data.get("status", STATUS_PENDING)
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_centers(self, city: str = None, category: str = None, status: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM centers WHERE 1=1"
            params = []
            
            if city:
                query += " AND city = ?"
                params.append(city)
            if category:
                query += " AND category = ?"
                params.append(category)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_center(self, center_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM centers WHERE center_id = ?", (center_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_center_status(self, center_id: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE centers SET status = ? WHERE center_id = ?", (status, center_id))
            await db.commit()

    # Методы для работы с курсами
    async def create_course(self, center_id: int, data: dict):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO courses (center_id, name, description, category, age_min, age_max, requirements, 
                                   schedule, price_4, price_8, price_unlimited, photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                center_id,
                data.get("name"),
                data.get("description"),
                data.get("category"),
                data.get("age_min"),
                data.get("age_max"),
                data.get("requirements"),
                data.get("schedule"),
                data.get("price_4"),
                data.get("price_8"),
                data.get("price_unlimited"),
                data.get("photo")
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_courses(self, city: str = None, category: str = None, age: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT c.*, ce.name as center_name, ce.address, ce.city, ce.phone
                FROM courses c
                JOIN centers ce ON c.center_id = ce.center_id
                WHERE ce.status = 'approved' AND 1=1
            """
            params = []
            
            if city:
                query += " AND ce.city = ?"
                params.append(city)
            if category:
                query += " AND c.category = ?"
                params.append(category)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                courses = [dict(row) for row in rows]
                # Фильтрация по возрасту на уровне Python
                if age:
                    courses = [c for c in courses if 
                              (not c.get("age_min") or c["age_min"] <= age) and
                              (not c.get("age_max") or c["age_max"] >= age)]
                return courses

    async def get_course(self, course_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT c.*, ce.name as center_name, ce.address, ce.city, ce.phone
                FROM courses c
                JOIN centers ce ON c.center_id = ce.center_id
                WHERE c.course_id = ?
            """, (course_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    # Методы для работы с абонементами
    async def create_subscription(self, user_id: int, course_id: int, tariff: str, qr_code: str, child_id: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем данные курса
            course = await self.get_course(course_id)
            if not course:
                return None
            
            # Определяем количество занятий и цену
            tariff_map = {
                "4": (4, course.get("price_4", 0)),
                "8": (8, course.get("price_8", 0)),
                "unlimited": (999, course.get("price_unlimited", 0))
            }
            lessons_total, price = tariff_map.get(tariff, (4, 0))
            
            cursor = await db.execute("""
                INSERT INTO subscriptions (user_id, child_id, course_id, center_id, tariff, 
                                         lessons_total, lessons_remaining, qr_code, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                user_id,
                child_id,
                course_id,
                course["center_id"],
                tariff,
                lessons_total,
                lessons_total,
                qr_code
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_user_subscriptions(self, user_id: int, child_id: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if child_id:
                query = """
                    SELECT s.*, c.name as course_name, ce.name as center_name
                    FROM subscriptions s
                    JOIN courses c ON s.course_id = c.course_id
                    JOIN centers ce ON s.center_id = ce.center_id
                    WHERE s.child_id = ? AND s.status = 'active'
                """
                params = (child_id,)
            else:
                query = """
                    SELECT s.*, c.name as course_name, ce.name as center_name
                    FROM subscriptions s
                    JOIN courses c ON s.course_id = c.course_id
                    JOIN centers ce ON s.center_id = ce.center_id
                    WHERE s.user_id = ? AND s.child_id IS NULL AND s.status = 'active'
                """
                params = (user_id,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_subscription_by_qr(self, qr_code: str):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.*, c.name as course_name, ce.name as center_name, 
                       u.user_id as owner_id, ch.name as child_name, ch.age as child_age
                FROM subscriptions s
                JOIN courses c ON s.course_id = c.course_id
                JOIN centers ce ON s.center_id = ce.center_id
                LEFT JOIN users u ON s.user_id = u.user_id
                LEFT JOIN children ch ON s.child_id = ch.child_id
                WHERE s.qr_code = ? AND s.status = 'active'
            """, (qr_code,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def record_visit(self, subscription_id: int, center_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем данные абонемента
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM subscriptions WHERE subscription_id = ?", (subscription_id,)) as cursor:
                sub = await cursor.fetchone()
                if not sub:
                    return False
            
            sub = dict(sub)
            
            # Записываем посещение
            await db.execute("""
                INSERT INTO visits (subscription_id, user_id, child_id, center_id)
                VALUES (?, ?, ?, ?)
            """, (subscription_id, sub.get("user_id"), sub.get("child_id"), center_id))
            
            # Уменьшаем количество оставшихся занятий (если не безлимит)
            if sub["tariff"] != "unlimited":
                await db.execute("""
                    UPDATE subscriptions 
                    SET lessons_remaining = lessons_remaining - 1
                    WHERE subscription_id = ?
                """, (subscription_id,))
                
                # Если занятия закончились, деактивируем абонемент
                await db.execute("""
                    UPDATE subscriptions 
                    SET status = 'expired'
                    WHERE subscription_id = ? AND lessons_remaining <= 0
                """, (subscription_id,))
            
            await db.commit()
            return True

    async def get_visit_stats(self, user_id: int, child_id: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if child_id:
                # Статистика для ребёнка
                async with db.execute("""
                    SELECT 
                        COUNT(v.visit_id) as visits_count,
                        SUM(CASE WHEN s.lessons_total > 0 THEN s.lessons_total ELSE 0 END) as total_lessons,
                        SUM(CASE WHEN s.lessons_remaining >= 0 THEN s.lessons_remaining ELSE 0 END) as remaining_lessons
                    FROM subscriptions s
                    LEFT JOIN visits v ON s.subscription_id = v.subscription_id
                    WHERE s.child_id = ?
                """, (child_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else {"visits_count": 0, "total_lessons": 0, "remaining_lessons": 0}
            else:
                # Статистика для взрослого
                async with db.execute("""
                    SELECT 
                        COUNT(v.visit_id) as visits_count,
                        SUM(CASE WHEN s.lessons_total > 0 THEN s.lessons_total ELSE 0 END) as total_lessons,
                        SUM(CASE WHEN s.lessons_remaining >= 0 THEN s.lessons_remaining ELSE 0 END) as remaining_lessons
                    FROM subscriptions s
                    LEFT JOIN visits v ON s.subscription_id = v.subscription_id
                    WHERE s.user_id = ? AND s.child_id IS NULL
                """, (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else {"visits_count": 0, "total_lessons": 0, "remaining_lessons": 0}

    # Методы для партнёров
    async def get_partner_center(self, partner_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM centers WHERE partner_id = ?", (partner_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_center_students(self, center_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT DISTINCT 
                    s.user_id, s.child_id, u.full_name, ch.name as child_name,
                    SUM(s.lessons_remaining) as remaining_lessons
                FROM subscriptions s
                LEFT JOIN users u ON s.user_id = u.user_id
                LEFT JOIN children ch ON s.child_id = ch.child_id
                WHERE s.center_id = ? AND s.status = 'active'
                GROUP BY s.user_id, s.child_id
            """, (center_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_center_analytics(self, center_id: int, month: int = None, year: int = None):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Посещения
            visits_query = """
                SELECT COUNT(*) as visits_count
                FROM visits
                WHERE center_id = ?
            """
            visits_params = (center_id,)
            
            if month and year:
                visits_query += " AND strftime('%m', visited_at) = ? AND strftime('%Y', visited_at) = ?"
                visits_params = (center_id, f"{month:02d}", str(year))
            
            async with db.execute(visits_query, visits_params) as cursor:
                visits_row = await cursor.fetchone()
                visits_count = visits_row["visits_count"] if visits_row else 0
            
            # Продажи абонементов
            sales_query = """
                SELECT COUNT(*) as sales_count, SUM(
                    CASE 
                        WHEN tariff = '4' THEN price_4
                        WHEN tariff = '8' THEN price_8
                        WHEN tariff = 'unlimited' THEN price_unlimited
                        ELSE 0
                    END
                ) as total_revenue
                FROM subscriptions s
                JOIN courses c ON s.course_id = c.course_id
                WHERE s.center_id = ?
            """
            sales_params = (center_id,)
            
            if month and year:
                sales_query += " AND strftime('%m', purchased_at) = ? AND strftime('%Y', purchased_at) = ?"
                sales_params = (center_id, f"{month:02d}", str(year))
            
            async with db.execute(sales_query, sales_params) as cursor:
                sales_row = await cursor.fetchone()
                sales_count = sales_row["sales_count"] if sales_row else 0
                total_revenue = sales_row["total_revenue"] if sales_row else 0
            
            return {
                "visits_count": visits_count,
                "sales_count": sales_count,
                "total_revenue": total_revenue or 0
            }

    # Методы для админа
    async def get_pending_centers(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM centers WHERE status = 'pending'") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # Методы для работы с платежами
    async def create_payment(self, user_id: int, subscription_id: int, amount: float, 
                           currency: str = "KZT", invoice_id: str = None, 
                           airba_payment_id: str = None, redirect_url: str = None, 
                           status: str = "pending"):
        """Создать платеж"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO payments (user_id, subscription_id, amount, currency, 
                                    invoice_id, airba_payment_id, redirect_url, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, subscription_id, amount, currency, invoice_id, 
                  airba_payment_id, redirect_url, status))
            await db.commit()
            return cursor.lastrowid

    async def get_payment(self, payment_id: int, user_id: int = None):
        """Получить платеж"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if user_id:
                async with db.execute(
                    "SELECT * FROM payments WHERE payment_id = ? AND user_id = ?",
                    (payment_id, user_id)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
            else:
                async with db.execute(
                    "SELECT * FROM payments WHERE payment_id = ?",
                    (payment_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def update_payment_status(self, payment_id: int, status: str, 
                                  transaction_id: str = None, error_message: str = None):
        """Обновить статус платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            if status == "success":
                await db.execute("""
                    UPDATE payments 
                    SET status = ?, transaction_id = ?, processed_at = CURRENT_TIMESTAMP,
                        error_message = ?
                    WHERE payment_id = ?
                """, (status, transaction_id, error_message, payment_id))
            else:
                await db.execute("""
                    UPDATE payments 
                    SET status = ?, transaction_id = ?, error_message = ?
                    WHERE payment_id = ?
                """, (status, transaction_id, error_message, payment_id))
            await db.commit()

    async def get_user_payments(self, user_id: int):
        """Получить все платежи пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def create_payment_refund(self, payment_id: int, airba_refund_id: str, 
                                   ext_id: str, amount: float, reason: str, status: str):
        """Создать возврат платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO payment_refunds (payment_id, airba_refund_id, ext_id, amount, reason, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (payment_id, airba_refund_id, ext_id, amount, reason, status))
            await db.commit()
            return cursor.lastrowid

