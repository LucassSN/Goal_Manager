import flet as ft
from logic import add_goal, close_alert, load_initial_data, start_monitor
from database import Database

db = Database()

def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.bgcolor = "black"
    page.theme_mode = "light"
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
        actions_alignment="end"
        
        
    )
    #Lembrar - Aprendizado: Colocar ele na lista suspensa apenas uma vez
    page.overlay.append(alert)
    
    # Estado local para o modo de visualização
    current_view = ["list"]

    def toggle_view(e):
        if current_view[0] == "list":
            current_view[0] = "grid"
            view_button.icon = ft.Icons.LIST
            view_button.tooltip = "Mudar para Modo Lista"
        else:
            current_view[0] = "list"
            view_button.icon = ft.Icons.GRID_VIEW
            view_button.tooltip = "Mudar para Modo Card"
        
        load_initial_data(meta_list, page, current_view)
        page.update()

    # Botão de alternância na AppBar
    view_button = ft.IconButton(
        icon=ft.Icons.GRID_VIEW,
        tooltip="Mudar para Modo Card",
        icon_color="white",
        on_click=toggle_view
    )

    page.appbar = ft.AppBar(
        title=ft.Text("Gerenciador de Metas", color="white", weight="bold"),
        center_title=True,
        bgcolor="black",
        actions=[view_button],
    )

    new_goal = ft.TextField(
        label="Digite sua nova meta", 
        width=300, 
        on_submit=lambda e: add_goal(page, new_goal, meta_list, alert, current_view), 
        color="white",
        border_color="white"
    )
    
    # O container principal agora será dinâmico
    meta_list = ft.Column(
        scroll="adaptive",
        expand=True,
        horizontal_alignment="center"
    )

    button = ft.FilledButton("Insert", on_click = lambda e: add_goal(page, new_goal, meta_list, alert, current_view), color = "white")

    load_initial_data(meta_list, page, current_view)

    start_monitor(page, meta_list, db, current_view)

    page.add(
        ft.Row(
            controls = [new_goal, button],
            alignment="center",
            spacing = 10
        ),
        ft.Divider(color="white", height=20),
        ft.Container(content=meta_list, expand=True, padding=10)
    )
    
if __name__ == "__main__":
    ft.run(main)