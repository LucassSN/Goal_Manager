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
        # MIGRATION: Adiciona coluna de posição se o banco já existir
        try:
            self.cursor.execute("ALTER TABLE goal ADD COLUMN position INTEGER DEFAULT 0")
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
        self.conn.commit()

    def add_goal(self, title):
        self.cursor.execute("INSERT INTO goal (title) VALUES (?)", (title,))
        self.conn.commit()
        return self.cursor.lastrowid

    def load_goals(self):
        cursor = self.conn.execute("SELECT * FROM goal ORDER BY position ASC, id ASC")
        data = cursor.fetchall()
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


    # Metodo para o Dashboard
    def get_goals_kpi(self):
        cursor = self.conn.execute("SELECT COUNT(id) FROM goal")
        total_goals = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(id) FROM goal WHERE status = 1")
        completed_goals = cursor.fetchone()[0]

        pending_goals = total_goals - completed_goals

        return{
            "total":total_goals,
            "concluidas":completed_goals,
            "pendentes":pending_goals
        }
    
    def get_tasks_kpi(self):

        cursor = self.conn.execute("SELECT COUNT(id) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        cursor = self.conn.execute("SELECT COUNT(id) FROM tasks WHERE status = 1")
        completed_tasks = cursor.fetchone()[0]

        return{
            "total":total_tasks,
            "concluidas": completed_tasks,
            "pendentes": total_tasks - completed_tasks 
        }

    def get_tasks_per_goal(self):
        cursor = self.conn.execute(""" SELECT goal.title, COUNT(tasks.id)
        FROM goal 
        LEFT JOIN tasks ON goal.id = tasks.goal_id
        GROUP BY goal.id
        ORDER BY COUNT(tasks.id) DESC""")

        return cursor.fetchall()


    


        
        

