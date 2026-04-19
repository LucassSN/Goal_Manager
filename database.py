import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("goal.db",  check_same_thread = False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.create_table()

    def create_table(self):
        # Tabela de Metas
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status INTEGER DEFAULT 0
        )
        """)
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
        self.conn.commit()

    def add_goal(self, title):
        self.cursor.execute("INSERT INTO goal (title) VALUES (?)", (title,))
        self.conn.commit()
        return self.cursor.lastrowid

    def load_goals(self):
        self.cursor.execute("SELECT * FROM goal")
        data = self.cursor.fetchall()
        return data

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

    # --- MÉTODOS PARA TASKS ---

    def add_task(self, goal_id, title):
        self.cursor.execute("INSERT INTO tasks (goal_id, title) VALUES (?, ?)", (goal_id, title))
        self.conn.commit()
        return self.cursor.lastrowid

    def load_tasks(self, goal_id):
        self.cursor.execute("SELECT * FROM tasks WHERE goal_id = ?", (goal_id,))
        return self.cursor.fetchall()

    def update_task_status(self, task_id, status):
        self.cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    


        
        

