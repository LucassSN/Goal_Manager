import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("goal.db",  check_same_thread = False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.create_table()

    def create_table(self):
        # Tabela de Categorias (deve ser criada antes de 'goal' por causa da FK)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT 'blue'
        )
        """)

        # Tabela de Metas
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status INTEGER DEFAULT 0
        )
        """)

        # MIGRATION: Adiciona coluna de posição se o banco já existir
        try:
            self.cursor.execute("ALTER TABLE goal ADD COLUMN position INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        # MIGRATION: Adiciona coluna de categoria se o banco já existir
        try:
            self.cursor.execute("ALTER TABLE goal ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        # Tabela de Tasks vinculadas às Metas
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            title TEXT NOT NULL,
            status INTEGER DEFAULT 0,
            FOREIGN KEY(goal_id) REFERENCES goal(id) ON DELETE CASCADE
        )
        """)
        # Tabela de configurações genéricas (chave/valor)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """)
        self.conn.commit()

    # --- MÉTODOS PARA GOALS ---

    def add_goal(self, title, category_id=None):
        self.cursor.execute("INSERT INTO goal (title, category_id) VALUES (?, ?)", (title, category_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def load_goals(self):
        """Retorna: (goal.id, goal.title, goal.status, goal.position, cat.id, cat.name, cat.color)"""
        cursor = self.conn.execute("""
            SELECT goal.id, goal.title, goal.status, goal.position,
                   categories.id, categories.name, categories.color
            FROM goal
            LEFT JOIN categories ON goal.category_id = categories.id
            ORDER BY goal.position ASC, goal.id ASC
        """)
        return cursor.fetchall()

    def delete_db_goal(self, goal_id):
        self.cursor.execute("DELETE FROM goal WHERE id = ?", (goal_id,))
        self.conn.commit()

    def update_status(self, goal_id, status):
        self.cursor.execute("UPDATE goal SET status =? WHERE id = ?", (status, goal_id))
        self.conn.commit()

    def get_goal(self, goal_id):
        self.cursor.execute("SELECT title FROM goal WHERE id = ?", (goal_id,))
        result = self.cursor.fetchone()
        return result[0] if result else "Meta Desconhecida"

    # --- MÉTODOS DE ORDENAÇÃO ---
    def update_goal_positions(self, goal_ids_ordered):
        for index, goal_id in enumerate(goal_ids_ordered):
            self.cursor.execute("UPDATE goal SET position = ? WHERE id = ?", (index, goal_id))
        self.conn.commit()

    # --- MÉTODOS PARA TASKS ---

    def add_task(self, goal_id, title):
        self.cursor.execute("INSERT INTO tasks (goal_id, title) VALUES (?, ?)", (goal_id, title))
        self.conn.commit()
        return self.cursor.lastrowid

    def load_tasks(self, goal_id):
        cursor = self.conn.execute("SELECT * FROM tasks WHERE goal_id = ?", (goal_id,))
        return cursor.fetchall()

    def update_task_status(self, task_id, status):
        self.cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    # --- MÉTODOS PARA CATEGORIES ---

    def add_category(self, name, color="blue"):
        self.cursor.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
        self.conn.commit()
        return self.cursor.lastrowid

    def load_categories(self):
        """Retorna: (id, name, color)"""
        cursor = self.conn.execute("SELECT id, name, color FROM categories ORDER BY name ASC")
        return cursor.fetchall()

    def delete_category(self, cat_id):
        # ON DELETE SET NULL garante que metas vinculadas ficam sem categoria
        self.cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        self.conn.commit()

    # --- MÉTODOS PARA O DASHBOARD ---

    def get_goals_kpi(self):
        cursor = self.conn.execute("SELECT COUNT(id) FROM goal")
        total_goals = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(id) FROM goal WHERE status = 1")
        completed_goals = cursor.fetchone()[0]
        return {
            "total": total_goals,
            "concluidas": completed_goals,
            "pendentes": total_goals - completed_goals
        }

    def get_tasks_kpi(self):
        cursor = self.conn.execute("SELECT COUNT(id) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(id) FROM tasks WHERE status = 1")
        completed_tasks = cursor.fetchone()[0]
        return {
            "total": total_tasks,
            "concluidas": completed_tasks,
            "pendentes": total_tasks - completed_tasks
        }

    def get_tasks_per_goal(self):
        cursor = self.conn.execute("""
            SELECT goal.title, COUNT(tasks.id)
            FROM goal
            LEFT JOIN tasks ON goal.id = tasks.goal_id
            GROUP BY goal.id
            ORDER BY COUNT(tasks.id) DESC
        """)
        return cursor.fetchall()

    def get_kpi_per_category(self):
        """Retorna: (cat.id, cat.name, cat.color, total_goals, completed_goals) por categoria."""
        cursor = self.conn.execute("""
            SELECT
                categories.id,
                categories.name,
                categories.color,
                COUNT(goal.id) AS total_goals,
                SUM(CASE WHEN goal.status = 1 THEN 1 ELSE 0 END) AS completed_goals
            FROM categories
            LEFT JOIN goal ON goal.category_id = categories.id
            GROUP BY categories.id
            ORDER BY categories.name ASC
        """)
        return cursor.fetchall()

    # --- MÉTODOS DE CONFIGURAÇÕES ---

    def get_setting(self, key: str, default: str = "") -> str:
        """Lê uma configuração pelo nome da chave. Retorna default se não existir."""
        cursor = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else default

    def set_setting(self, key: str, value: str):
        """Salva (ou atualiza) uma configuração pelo nome da chave."""
        self.cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()
