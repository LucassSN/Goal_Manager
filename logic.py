import flet as ft
from database import Database
import time
import threading




class ItemGoal(ft.Container):
    def __init__(self, text, remove_func, goal_id, db, page, status=0, view_mode="list"):
        super().__init__()
        self.db = db
        self.goal_id = goal_id
        self.remove_func = remove_func
        self.view_mode = view_mode
        
        # Configurações básicas baseadas no modo
        if self.view_mode == "list":
            self.width = None
            self.height = None
            self.padding = 5
            self.margin = ft.margin.only(bottom=5)
            self.border_radius = 10
        else: # Grid / Card mode
            self.width = 200 # Aumentado um pouco para dar mais espaço
            self.height = 160
            self.padding = 15 # Padding interno do card
            self.border_radius = 15
            
        self.bgcolor = "surfaceVariant"
        self.border = ft.border.all(1, "outline")
        self.on_click = lambda _: page.go(f"/tasks/{self.goal_id}")
        
        self.checkbox = ft.Checkbox(
            value=True if status == 1 else False,
            on_change=self.card_status,
            fill_color="primary"
        )
        
        self.display_text = ft.Text(
            value=text,
            size=18 if self.view_mode == "grid" else 16,
            weight="bold" if self.view_mode == "grid" else "normal",
            color="onSurface" if status == 0 else "#A0A0A0",
            text_align="center",
            style=ft.TextStyle(
                decoration=(ft.TextDecoration.LINE_THROUGH if status == 1 
                          else ft.TextDecoration.NONE)
            )
        )
        
        self.trash_icon = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="error",
            tooltip="Excluir",
            on_click=lambda _: self.remove_func(self),
        )

        if self.view_mode == "list":
            self.content = ft.Row(
                controls=[
                    self.checkbox,
                    self.display_text,
                    ft.VerticalDivider(expand=True),
                    self.trash_icon,
                ],
                alignment="start",
            )
        else: # Grid / Card view mode
            self.content = ft.Column(
                controls=[
                    # Ícones alinhados no topo com espaço entre eles
                    ft.Row(
                        controls=[self.checkbox, self.trash_icon], 
                        alignment="spaceBetween"
                    ),
                    # Texto da meta centralizado com padding extra
                    ft.Container(
                        content=self.display_text, 
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                        padding=ft.padding.only(top=10)
                    )
                ],
                alignment="start", # Começa do topo
                spacing=0
            )

    def card_status(self, e):
        status_int = 1 if self.checkbox.value else 0
        self.db.update_status(self.goal_id, status_int)
        
        # Atualizamos o hash global para o monitor ignorar esta mudança já processada
        global last_check_hash
        last_check_hash = str(self.db.load_goals())

        if self.checkbox.value == True:
            self.display_text.style.decoration = ft.TextDecoration.LINE_THROUGH
            self.display_text.color = "#A0A0A0"
        else:
            self.display_text.style.decoration = ft.TextDecoration.NONE
            self.display_text.color = "onSurface"
        self.update()

def delete_goal_action(page, db, meta_list, card_to_remove, current_view):
    db.delete_db_goal(card_to_remove.goal_id)
    
    # Atualiza o hash global imediatamente para o monitor não agir
    global last_check_hash
    last_check_hash = str(db.load_goals())
    
    # Recarregamos para manter a interface limpa
    load_initial_data(db, meta_list, page, current_view)

def add_goal(page, db, new_goal, meta_list, alert, current_view):
    if new_goal.value:
        goal_id = db.add_goal(new_goal.value)
        
        # Atualiza hash para o monitor não disparar recarga desnecessária
        global last_check_hash
        last_check_hash = str(db.load_goals())

        # Em vez de append simples, recarregamos para garantir a ordenação correta e layout de Grid/List
        load_initial_data(db, meta_list, page, current_view)
        new_goal.value = ""
        page.update()
    else:
        alert.open = True
        page.update()


def load_initial_data(db, meta_list, page, current_view):
    # Limpamos o container principal
    meta_list.controls.clear()
    goals_data = db.load_goals()
    
    # Criamos o container de visualização baseado no modo
    if current_view[0] == "list":
        view_container = ft.ListView(expand=True, spacing=10, padding=10)
    else:
        view_container = ft.GridView(
            expand=True, 
            runs_count=5, 
            max_extent=200, 
            spacing=10, 
            run_spacing=10,
            padding=10
        )

    for g in goals_data:
        card = ItemGoal(text=g[1],
                        remove_func=lambda card: delete_goal_action(page, db, meta_list, card, current_view), 
                        goal_id=g[0],
                        db = db,
                        page = page,
                        status = g[2],
                        view_mode=current_view[0]
                        )
        view_container.controls.append(card)
    
    meta_list.controls.append(view_container)
    page.update()
    
def close_alert(page, alert):
    alert.open = False
    page.update()

last_check_hash = None

def start_monitor(page, db, current_view):
    def check_database():
        global last_check_hash 
        while True:
            # Obtém referências dinâmicas baseadas na rota atual
            try:
                current_route = page.route
                # Se estiver na Home, monitora Metas
                if current_route == "/":
                    goals_data = db.load_goals()
                    current_hash = str(goals_data)
                    if current_hash != last_check_hash:
                        # Busca o meta_list pela key com segurança
                        target_meta_list = None
                        for view in page.views:
                            if view.route == "/":
                                for control in view.controls:
                                    if hasattr(control, "content") and hasattr(control.content, "controls"):
                                        res = control.content.controls
                                        target_meta_list = next((c for c in res if getattr(c, "key", None) == "meta_list"), None)
                                        if target_meta_list:
                                            break
                        
                        if target_meta_list:
                            load_initial_data(db, target_meta_list, page, current_view)
                            last_check_hash = current_hash
                
                # Se estiver em Tasks, monitora Sub-tarefas
                elif current_route.startswith("/tasks/"):
                    goal_id = current_route.split("/")[-1]
                    tasks_data = db.load_tasks(goal_id)
                    current_hash = f"tasks_{goal_id}_{str(tasks_data)}"
                    if current_hash != last_check_hash:
                        target_task_list = None
                        for view in page.views:
                            if view.route.startswith("/tasks/"):
                                for control in view.controls:
                                    if hasattr(control, "content") and hasattr(control.content, "controls"):
                                        res = control.content.controls
                                        target_task_list = next((c for c in res if getattr(c, "key", None) == "task_list"), None)
                                        if target_task_list:
                                            break
                        
                        if target_task_list:
                            load_tasks_view(page, db, target_task_list, goal_id)
                            last_check_hash = current_hash
                
                time.sleep(0.5)
            except Exception as e:
                print(f"Erro no monitor: {e}")
                time.sleep(1)

    thread = threading.Thread(target=check_database, daemon=True)
    thread.start()


# --- NOVAS CLASSES E FUNÇÕES PARA TASKS ---

class TaskItem(ft.Container):
    def __init__(self, text, task_id, goal_id, db, page, meta_list, status=0):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.goal_id = goal_id
        self.app_page = page
        self.meta_list = meta_list
        
        self.padding = 10
        self.bgcolor = "surfaceVariant"
        self.border_radius = 10
        self.border = ft.border.all(1, "outline")
        
        self.checkbox = ft.Checkbox(
            value=True if status == 1 else False,
            on_change=self.toggle_status,
            fill_color="primary"
        )

        self.display_text = ft.Text(
            text, 
            color="#A0A0A0" if status == 1 else "onSurface", 
            size=16, 
            expand=True, 
            style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH if status == 1 else ft.TextDecoration.NONE)
        )

        self.content = ft.Row(
            controls=[
                self.checkbox,
                self.display_text,
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="error", on_click=self.delete_task)
            ]
        )

    def toggle_status(self, e):
        status_int = 1 if self.checkbox.value else 0
        self.db.update_task_status(self.task_id, status_int)
        
        # Atualiza a hash para o estado atualizado do BD, assim o monitor ignora a mudança
        global last_check_hash
        last_check_hash = f"tasks_{self.goal_id}_{str(self.db.load_tasks(self.goal_id))}"
        
        if self.checkbox.value == True:
            self.display_text.style.decoration = ft.TextDecoration.LINE_THROUGH
            self.display_text.color = "#A0A0A0"
        else:
            self.display_text.style.decoration = ft.TextDecoration.NONE
            self.display_text.color = "onSurface"
        self.update()

    def delete_task(self, e):
        self.db.delete_task(self.task_id)
        
        # Atualiza a hash em tempo real para o monitor não sobreescrever a interface
        global last_check_hash
        last_check_hash = f"tasks_{self.goal_id}_{str(self.db.load_tasks(self.goal_id))}"
        
        # Recarrega a view de tasks instantaneamente local
        load_tasks_view(self.app_page, self.db, self.meta_list, self.goal_id)

def load_tasks_view(page, db, meta_list, goal_id):
    meta_list.controls.clear()
    tasks_data = db.load_tasks(goal_id)
    
    view_container = ft.ListView(expand=True, spacing=10, padding=10)
    
    for t in tasks_data:
        # Repassa page e meta_list para o TaskItem atualizar views localmente
        task_card = TaskItem(text=t[2], task_id=t[0], goal_id=t[1], db=db, page=page, meta_list=meta_list, status=t[3])
        view_container.controls.append(task_card)
        
    meta_list.controls.append(view_container)
    page.update()

def add_task_action(page, db, meta_list, goal_id, field):
    if field.value:
        db.add_task(goal_id, field.value)
        field.value = ""
        
        # Atualiza a hash para o monitor ignorar a chamada para evitar flicker
        global last_check_hash
        last_check_hash = f"tasks_{goal_id}_{str(db.load_tasks(goal_id))}"
        
        load_tasks_view(page, db, meta_list, goal_id)
