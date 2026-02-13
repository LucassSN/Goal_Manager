import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("goal.db",  check_same_thread = False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
    CREATE TABLE IF NOT EXISTS goal(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL
                            )
                            """)
        self.conn.commit()
        print("banco de dados e tabelas criado com sucesso!")

    def add_goal(self, title):
        self.cursor.execute("INSERT INTO goal (title) VALUES (?)", (title,))
        self.conn.commit()
        print("meta adicionada com sucesso!")
        return self.cursor.lastrowid
        
    
    def get_goals(self):
        self.cursor.execute("SELECT * FROM goal")
        return self.cursor.fetchall()
        print("arquivo db lido com sucesso!")
        
    
    def  delete_db_goal(self, goal_id):
        self.cursor.execute("DELETE FORM goal WHERE id = ?", (goal_id,))
        self.conn.commit()
        print("arquivo db exluido com sucesso!")

    


        
        

