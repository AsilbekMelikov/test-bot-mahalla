import psycopg2
from psycopg2.extras import DictCursor


class Database:
    def __init__(
        self, db_name: str, db_user: str, db_password: str, db_port: int, db_host: str
    ) -> None:
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

    @property
    def connect(self):
        return psycopg2.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            cursor_factory=DictCursor,
        )

    def execute(
        self,
        sql: str,
        params: tuple = None,
        fetchall: bool = False,
        fetchone: bool = False,
        commit: bool = False,
    ) -> dict | tuple | None:
        connection = self.connect

        if not params:
            params = ()

        cursor = connection.cursor()

        cursor.execute(sql, params)

        data = None
        if fetchall:
            data = cursor.fetchall()

        elif fetchone:
            data = cursor.fetchone()

        if commit:
            connection.commit()

        connection.close()
        return data

    def create_admins_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,       -- Auto-incrementing ID
            full_name VARCHAR(255),      -- Admin's full name
            user_id BIGINT UNIQUE,       -- Telegram user ID (unique)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of registration
        )
        """
        self.execute(sql=sql, commit=True)

    def create_table_groups(self):
        sql = """
        CREATE TABLE IF NOT EXISTS groups_tb (
            id SERIAL PRIMARY KEY,       -- Auto-incrementing ID
            group_name VARCHAR(255),     -- Group name
            group_id BIGINT UNIQUE,      -- Telegram group ID (unique)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of registration
        )
        """
        self.execute(sql=sql, commit=True)

    def register_groups(self, group_name, group_id):
        sql = """
        INSERT INTO groups_tb (group_name, group_id)
        VALUES (%s, %s)
        ON CONFLICT (group_id) DO NOTHING  -- Avoid duplicates
        """
        params = (
            group_name,
            group_id,
        )
        self.execute(sql=sql, params=params, commit=True)

    def get_groups(self):

        sql = """
        SELECT group_id FROM groups_tb"""

        return self.execute(sql=sql, fetchall=True)

    def get_all_groups(self):

        sql = """
        SELECT * FROM groups_tb"""

        return self.execute(sql=sql, fetchall=True)

    def register_admin(self, full_name, user_id):
        sql = """
        INSERT INTO admins (full_name, user_id)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO NOTHING  -- Avoid duplicates
        """
        params = (full_name, user_id)
        self.execute(sql=sql, params=params, commit=True)

    def delete_group(self, group_id):

        sql = """
        DELETE FROM groups_tb WHERE group_id = %s
        """

        params = (group_id,)
        self.execute(sql=sql, params=params, commit=True)

    def get_admin(self, user_id):

        sql = """
        SELECT user_id FROM admins WHERE user_id = %s"""

        params = (user_id,)

        return self.execute(sql=sql, params=params, fetchone=True)

    def get_admins(self):

        sql = """
        SELECT * FROM admins"""

        return self.execute(sql=sql, fetchall=True)

    def delete_admin(self, user_id):

        sql = """
        DELETE FROM admins WHERE user_id = %s
        """

        params = (user_id,)
        self.execute(sql=sql, params=params, commit=True)


db = Database(
    db_name="mahallanewsbot",
    db_user="postgres",
    db_password="0000",
    db_host="localhost",
    db_port=5432,
)


db.create_admins_table()
db.create_table_groups()
