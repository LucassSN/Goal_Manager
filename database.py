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

        # ── Dashboard Builder ────────────────────────────────────────────────
        # Tabela de Dashboards (múltiplos dashboards nomeados)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboards(
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Tabela de Layouts (JSON por dashboard)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_layouts(
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            dashboard_id INTEGER NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
            layout_json  TEXT NOT NULL DEFAULT '[]',
            filters_json TEXT NOT NULL DEFAULT '{}',
            updated_at   TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Cria o dashboard padrão se ainda não existir
        existing = self.conn.execute("SELECT id FROM dashboards WHERE is_default = 1").fetchone()
        if not existing:
            self.cursor.execute(
                "INSERT INTO dashboards (name, is_default) VALUES (?, 1)",
                ("Dashboard Padrão",)
            )
            default_id = self.cursor.lastrowid
            # Layout inicial equivalente ao dashboard estático anterior
            import json as _json
            default_layout = [
                {"uid": "kpi_total_goals",     "type": "kpi_total_goals",     "span": 1},
                {"uid": "kpi_completed_goals", "type": "kpi_completed_goals", "span": 1},
                {"uid": "pie_goals_status",    "type": "pie_goals_status",    "span": 1},
                {"uid": "bar_tasks_per_goal",  "type": "bar_tasks_per_goal",  "span": 1},
                {"uid": "category_cards",      "type": "category_cards",      "span": 2},
            ]
            self.cursor.execute(
                "INSERT INTO dashboard_layouts (dashboard_id, layout_json) VALUES (?, ?)",
                (default_id, _json.dumps(default_layout))
            )

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

    def update_goal(self, goal_id, title, category_id=None):
        self.cursor.execute("UPDATE goal SET title = ?, category_id = ? WHERE id = ?", (title, category_id, goal_id))
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

    def get_goals_kpi(self, category_id=None, status_filter=None):
        """KPI de metas. Aceita filtros opcionais (None=todos, 0=pendente, 1=concluída)."""
        clauses, params = [], []
        if category_id is not None:
            clauses.append("category_id = ?")
            params.append(category_id)
        if status_filter is not None:
            clauses.append("status = ?")
            params.append(status_filter)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        # Conta total e concluídas numa única query
        row = self.conn.execute(
            f"SELECT COUNT(id), SUM(CASE WHEN status=1 THEN 1 ELSE 0 END) FROM goal {where}",
            params
        ).fetchone()
        total     = row[0] or 0
        completed = int(row[1] or 0)
        if status_filter == 0:
            completed = 0
        return {"total": total, "concluidas": completed, "pendentes": total - completed}

    def get_tasks_kpi(self, category_id=None, status_filter=None):
        """KPI de tarefas. Aceita filtros opcionais."""
        clauses, params = [], []
        join = ""
        if category_id is not None:
            join = "LEFT JOIN goal ON tasks.goal_id = goal.id"
            clauses.append("goal.category_id = ?")
            params.append(category_id)
        if status_filter is not None:
            clauses.append("tasks.status = ?")
            params.append(status_filter)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        row = self.conn.execute(
            f"SELECT COUNT(tasks.id), SUM(CASE WHEN tasks.status=1 THEN 1 ELSE 0 END) "
            f"FROM tasks {join} {where}",
            params
        ).fetchone()
        total     = row[0] or 0
        completed = int(row[1] or 0)
        if status_filter == 0:
            completed = 0
        return {"total": total, "concluidas": completed, "pendentes": total - completed}


    def get_tasks_per_goal(self, category_id=None):
        """Retorna (goal.title, task_count). Filtrável por categoria."""
        where = "WHERE goal.category_id = ?" if category_id is not None else ""
        params = [category_id] if category_id is not None else []
        cursor = self.conn.execute(f"""
            SELECT goal.title, COUNT(tasks.id)
            FROM goal
            LEFT JOIN tasks ON goal.id = tasks.goal_id
            {where}
            GROUP BY goal.id
            ORDER BY COUNT(tasks.id) DESC
        """, params)
        return cursor.fetchall()

    def get_kpi_per_category(self, status_filter=None):
        """Retorna: (cat.id, cat.name, cat.color, total_goals, completed_goals) por categoria."""
        if status_filter is not None:
            extra = f"AND goal.status = {int(status_filter)}"
        else:
            extra = ""
        cursor = self.conn.execute(f"""
            SELECT
                categories.id,
                categories.name,
                categories.color,
                COUNT(CASE WHEN goal.id IS NOT NULL {extra} THEN 1 END) AS total_goals,
                SUM(CASE WHEN goal.status = 1 THEN 1 ELSE 0 END) AS completed_goals
            FROM categories
            LEFT JOIN goal ON goal.category_id = categories.id
            GROUP BY categories.id
            ORDER BY categories.name ASC
        """)
        return cursor.fetchall()

    def get_progress_per_category(self):
        """Retorna (cat.name, cat.color, progress_pct) para o gráfico de barras por categoria."""
        cursor = self.conn.execute("""
            SELECT
                categories.name,
                categories.color,
                COUNT(goal.id) AS total,
                SUM(CASE WHEN goal.status = 1 THEN 1 ELSE 0 END) AS completed
            FROM categories
            LEFT JOIN goal ON goal.category_id = categories.id
            GROUP BY categories.id
            ORDER BY categories.name ASC
        """)
        rows = cursor.fetchall()
        return [
            (name, color, (completed / total * 100) if total else 0.0)
            for name, color, total, completed in rows
        ]

    def get_goals_by_category(self, category_id):
        """Retorna todas as metas de uma categoria (para drill-through)."""
        cursor = self.conn.execute("""
            SELECT goal.id, goal.title, goal.status,
                   COUNT(tasks.id) as total_tasks,
                   SUM(CASE WHEN tasks.status = 1 THEN 1 ELSE 0 END) as done_tasks
            FROM goal
            LEFT JOIN tasks ON goal.id = tasks.goal_id
            WHERE goal.category_id = ?
            GROUP BY goal.id
            ORDER BY goal.position ASC
        """, (category_id,))
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

    # --- MÉTODOS DO DASHBOARD BUILDER ---

    def list_dashboards(self):
        """Retorna todos os dashboards: (id, name, is_default)."""
        return self.conn.execute(
            "SELECT id, name, is_default FROM dashboards ORDER BY id ASC"
        ).fetchall()

    def create_dashboard(self, name: str) -> int:
        """Cria um novo dashboard e retorna seu id."""
        self.cursor.execute("INSERT INTO dashboards (name) VALUES (?)", (name,))
        new_id = self.cursor.lastrowid
        # Cria um layout vazio associado
        self.cursor.execute(
            "INSERT INTO dashboard_layouts (dashboard_id, layout_json) VALUES (?, '[]')",
            (new_id,)
        )
        self.conn.commit()
        return new_id

    def rename_dashboard(self, dashboard_id: int, new_name: str):
        self.cursor.execute(
            "UPDATE dashboards SET name = ? WHERE id = ?", (new_name, dashboard_id)
        )
        self.conn.commit()

    def delete_dashboard(self, dashboard_id: int):
        """Exclui um dashboard (CASCADE remove o layout associado). Não permite excluir o padrão."""
        is_default = self.conn.execute(
            "SELECT is_default FROM dashboards WHERE id = ?", (dashboard_id,)
        ).fetchone()
        if is_default and is_default[0] == 1:
            return False  # não permite excluir o padrão
        self.cursor.execute("DELETE FROM dashboards WHERE id = ?", (dashboard_id,))
        self.conn.commit()
        return True

    def load_dashboard_layout(self, dashboard_id: int) -> dict:
        """Retorna {'widgets': [...], 'filters': {...}} para o dashboard dado."""
        import json as _json
        row = self.conn.execute(
            "SELECT layout_json, filters_json FROM dashboard_layouts WHERE dashboard_id = ?",
            (dashboard_id,)
        ).fetchone()
        if not row:
            return {"widgets": [], "filters": {"category_id": None, "status": "all"}}
        return {
            "widgets": _json.loads(row[0] or "[]"),
            "filters": _json.loads(row[1] or "{}"),
        }

    def save_dashboard_layout(self, dashboard_id: int, widgets: list, filters: dict = None):
        """Persiste o layout (lista de widgets) e filtros do dashboard."""
        import json as _json
        filters = filters or {"category_id": None, "status": "all"}
        self.cursor.execute("""
            UPDATE dashboard_layouts
            SET layout_json = ?, filters_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE dashboard_id = ?
        """, (_json.dumps(widgets), _json.dumps(filters), dashboard_id))
        if self.cursor.rowcount == 0:
            # Garante que existe um registro para este dashboard
            self.cursor.execute(
                "INSERT INTO dashboard_layouts (dashboard_id, layout_json, filters_json) VALUES (?, ?, ?)",
                (dashboard_id, _json.dumps(widgets), _json.dumps(filters))
            )
        self.conn.commit()

    def get_default_dashboard_id(self) -> int:
        """Retorna o id do dashboard padrão."""
        row = self.conn.execute(
            "SELECT id FROM dashboards WHERE is_default = 1"
        ).fetchone()
        return row[0] if row else None
