import flet as ft
from database import Database

db = Database()

# Preciso criar uma classe para que as metas possam gerenciar seu proprio estado
class ItemGoal(ft.Container):
    def __init__(self, text, remove_func, goal_id,db):
        super().__init__()
        self.db = db
        self.goal_id = goal_id
        self.padding = 10
        self.border_radius = 10
        self.bgcolor = "surfacevariant"
        self.border = ft.border.all(1, "outlinevariant")
        self.remove_func = remove_func

        self.display_text = ft.Text(value =text, size = 16)
        self.checkbox = ft.Checkbox(value = False, on_change = self.card_status)
        self.trash_icon = ft.IconButton(
            icon = ft.Icons.DELETE_OUTLINE,
            icon_color = "red",
            tooltip = "Excluir",
            on_click = lambda _: self.remove_func(self),
        )

        self.content = ft.Row(
            controls = [
                self.checkbox,
                self.display_text,
                ft.VerticalDivider(width =0),
                self.trash_icon,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    def card_status(self, e):
        if self.checkbox.value == True:
            self.display_text.style = ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH,
                color = "grey"
            )
        else:
            self.display_text.style = ft.TextStyle(
                decoration= ft.TextDecoration.NONE,
                color = None
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
                            db = db)

        meta_list.controls.append(new_card)
        new_goal.value = ""
        page.update()
    else:
        alert.open = True
        page.update()

def load_initial_data(meta_list, page):
    goals_data = db.get_goals()

    for g in goals_data:
        
        def delete_goal(card_to_remove):
            db.delete_db_goal(card_to_remove.goal_id)
            meta_list.controls.remove(card_to_remove)
            page.update()
        card = ItemGoal(text=g[1],
                        remove_func=delete_goal, 
                        goal_id=g[0],
                        db = db)
        meta_list.controls.append(card)
    
def close_alert(page, alert):
    alert.open = False
    page.update()



