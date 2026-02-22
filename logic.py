import flet as ft
from database import Database
import time
import threading

db = Database()

# Preciso criar uma classe para que as metas possam gerenciar seu proprio estado
class ItemGoal(ft.Container):
    def __init__(self, text, remove_func, goal_id,db, status = 0):
        super().__init__()
        self.db = db
        self.goal_id = goal_id
        self.padding = 5
        self.margin = ft.margin.only(bottom=5)
        self.border_radius = 10
        self.bgcolor = "black"
        self.border = ft.border.all(1, "white")
        self.remove_func = remove_func
        self.display_text = ft.Text(value =text, size = 16, color="white")

        self.checkbox = ft.Checkbox(
            value = True if status == 1 else False, 
            on_change = self.card_status, 
            fill_color="white", 
            check_color="black",
            border_side=ft.BorderSide(2, "white")
        )
        

        self.display_text = ft.Text(
            value = text,
            size=16, 
            color = "gray" if status == 1 else "white",
            style = ft.TextStyle(
                decoration = (ft.TextDecoration.LINE_THROUGH if status == 1 
                              else ft.TextDecoration.NONE
                        )
                )
            
        )
        
        self.trash_icon = ft.IconButton(
            icon = ft.Icons.DELETE_OUTLINE,
            icon_color = "white",
            tooltip = "Excluir",
            on_click = lambda _: self.remove_func(self),
        )

        self.content = ft.Row(
            controls = [
                self.checkbox,
                self.display_text,
                ft.VerticalDivider(expand = True),
                self.trash_icon,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    def card_status(self, e):

        status_int = 1 if self.checkbox.value else 0
        
        self.db.update_status(self.goal_id, status_int)

        if self.checkbox.value == True:
            self.display_text.style = ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH,
                color = "gray"
            )
        else:
            self.display_text.style = ft.TextStyle(
                decoration= ft.TextDecoration.NONE,
                color = "white"
            )
        self.update()

def add_goal(page, new_goal, meta_list, alert):
    if new_goal.value:
        goal_id = db.add_goal(new_goal.value)

        def delete_goal(card_to_remove):
            db.delete_db_goal(card_to_remove.goal_id)
            meta_list.controls.remove(card_to_remove)
            page.update()


        new_card = ItemGoal(text = new_goal.value, 
                            remove_func=delete_goal, 
                            goal_id = goal_id,
                            db = db,
                            )

        meta_list.controls.append(new_card)
        new_goal.value = ""
        page.update()
    else:
        alert.open = True
        page.update()


def load_initial_data(meta_list, page):

    meta_list.controls.clear()

    goals_data = db.load_goals()

    for g in goals_data:
        
        def delete_goal(card_to_remove):
            db.delete_db_goal(card_to_remove.goal_id)
            if card_to_remove in meta_list.controls:
                meta_list.controls.remove(card_to_remove)
            page.update()

        card = ItemGoal(text=g[1],
                        remove_func=delete_goal, 
                        goal_id=g[0],
                        db = db,
                        status = g[2]
                        )
        meta_list.controls.append(card)
    page.update()
    
def close_alert(page, alert):
    alert.open = False
    page.update()

last_check_hash = None

def start_monitor(page, meta_list, db):
    def check_database():
        global last_check_hash 
        while True:
            goals_data = db.load_goals()

            current_hash = str(goals_data)

            if current_hash != last_check_hash:
                load_initial_data(meta_list, page)
                last_check_hash = current_hash
                print("interface sincronizada com o banco")
            time.sleep(3)
    thread = threading.Thread(target=check_database, daemon=True)
    thread.start()



