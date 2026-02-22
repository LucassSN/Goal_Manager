import flet as ft
from logic import add_goal, close_alert, load_initial_data, start_monitor
from database import Database

db = Database()

def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = page.bgcolor = "black"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 40

    

    alert =ft.AlertDialog(

        bgcolor= "black",
        shape = ft.RoundedRectangleBorder(
            radius=10,
            side=ft.BorderSide(2, "white")
        ),
        
        title = ft.Text("Campo Vazio", size = 30,color = "white"),
        content = ft.Text("O Campo de Metas não foi preenchido", color="white"),
        actions = [
            ft.Container(
                content = ft.TextButton("Entendido", on_click = lambda e: close_alert(page, alert),
                            style = ft.ButtonStyle(color="black")
                            ),
                bgcolor="white",
                border_radius=5,
                padding = ft.Padding.symmetric(horizontal=10)

            )
            
        ],
        actions_alignment=ft.MainAxisAlignment.END
        
        
    )
    #Lembrar - Aprendizado: Colocar ele na lista suspensa apenas uma vez
    page.overlay.append(alert)
    
    title = ft.Text("Metas", size=30, color="white" )
    new_goal = ft.TextField(label = "Digite sua nova meta", width=300, on_submit = lambda e: add_goal(page, new_goal, meta_list, alert), color = "white")
    meta_list = ft.Column(horizontal_alignment = ft.CrossAxisAlignment.CENTER,expand = True, spacing = 10, scroll = ft.ScrollMode.ADAPTIVE)
    button = ft.FilledButton("Insert", on_click = lambda e: add_goal(page, new_goal, meta_list, alert), color = "white")

    

    load_initial_data(meta_list, page)

    start_monitor(page, meta_list, db)

    page.add(title,
             ft.Row(
                 controls = [new_goal, button],
                 alignment=ft.MainAxisAlignment.CENTER,
                 spacing = 10
             ),
             meta_list)
    
if __name__ == "__main__":
    ft.run(main)