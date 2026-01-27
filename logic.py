import flet as ft


# Preciso criar uma classe para que as metas possam gerenciar seu proprio estado

class ItemGoal(ft.Container):
    def __init__(self, text):
        super().__init__()
        self.padding = 10
        self.border_radius = 10
        self.bgcolor = "surfacevariant"
        self.border = ft.border.all(1, "outlinevariant")

        self.display_text = ft.Text(value =text, size = 16)
        self.checkbox = ft.Checkbox(value = False, on_change = self.card_status)

        self.content = ft.Row(
            controls = [
                self.checkbox,
                self.display_text,
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

        new_card = ItemGoal(new_goal.value)

        #Nao e mais necessario criar esse Container de forma generica
        # new_card = ft.Container(
        #     content = ft.Row(
        #         controls = [
        #             ft.Checkbox(value=False),
        #             ft.Text(new_goal.value, size=16),
        #         ],
        #     ),
        #     padding = 10,
        #     border_radius = 10,
        #     bgcolor = "surfacevariant",
        #     border = ft.border.all(1, "outlinevariant")
        # )

        meta_list.controls.append(new_card)
        new_goal.value = ""
        page.update()
    else:
        alert.open = True
        page.update()
    
def close_alert(page, alert):
    alert.open = False
    page.update()