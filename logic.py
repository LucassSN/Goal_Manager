import flet as ft
from database import Database
import time
import threading

db = Database()


class ItemGoal(ft.Container):
    def __init__(self, text, remove_func, goal_id, db, status=0, view_mode="list"):
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
            
        self.bgcolor = "black"
        self.border = ft.border.all(1, "white")
        
        self.checkbox = ft.Checkbox(
            value=True if status == 1 else False,
            on_change=self.card_status,
            fill_color="white",
            check_color="black",
            border_side=ft.BorderSide(2, "white")
        )
        
        self.display_text = ft.Text(
            value=text,
            size=18 if self.view_mode == "grid" else 16,
            weight="bold" if self.view_mode == "grid" else "normal",
            color="white" if status == 0 else "gray",
            text_align="center",
            style=ft.TextStyle(
                decoration=(ft.TextDecoration.LINE_THROUGH if status == 1 
                          else ft.TextDecoration.NONE)
            )
        )
        
        self.trash_icon = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="white",
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
            self.display_text.color = "gray"
        else:
            self.display_text.style.decoration = ft.TextDecoration.NONE
            self.display_text.color = "white"
        self.update()

def delete_goal_action(page, meta_list, card_to_remove, current_view):
    db.delete_db_goal(card_to_remove.goal_id)
    
    # Atualiza o hash global imediatamente para o monitor não agir
    global last_check_hash
    last_check_hash = str(db.load_goals())
    
    # Recarregamos para manter a interface limpa
    load_initial_data(meta_list, page, current_view)

def add_goal(page, new_goal, meta_list, alert, current_view):
    if new_goal.value:
        goal_id = db.add_goal(new_goal.value)
        
        # Atualiza hash para o monitor não disparar recarga desnecessária
        global last_check_hash
        last_check_hash = str(db.load_goals())

        new_card = ItemGoal(text = new_goal.value, 
                            remove_func=lambda card: delete_goal_action(page, meta_list, card, current_view), 
                            goal_id = goal_id,
                            db = db,
                            view_mode=current_view[0]
                            )
        
        # Em vez de append simples, recarregamos para garantir a ordenação correta e layout de Grid/List
        load_initial_data(meta_list, page, current_view)
        new_goal.value = ""
        page.update()
    else:
        alert.open = True
        page.update()


def load_initial_data(meta_list, page, current_view):
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
                        remove_func=lambda card: delete_goal_action(page, meta_list, card, current_view), 
                        goal_id=g[0],
                        db = db,
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

def start_monitor(page, meta_list, db, current_view):
    def check_database():
        global last_check_hash 
        while True:
            goals_data = db.load_goals()

            current_hash = str(goals_data)

            if current_hash != last_check_hash:
                load_initial_data(meta_list, page, current_view)
                last_check_hash = current_hash
                print("Sincronização em background concluída.")
            time.sleep(0.5) # Muito mais rápido agora
    thread = threading.Thread(target=check_database, daemon=True)
    thread.start()



