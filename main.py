import flet as ft
from logic import add_goal, close_alert, load_initial_data, start_monitor, load_tasks_view, add_task_action
from database import Database

db = Database()

def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    page.bgcolor = "black"
    page.theme_mode = "light"
    page.padding = 0 
    
    current_view = ["list"]

    alert = ft.AlertDialog(
        bgcolor="black",
        shape=ft.RoundedRectangleBorder(radius=10, side=ft.BorderSide(2, "white")),
        title=ft.Text("Campo Vazio", size=30, color="white"),
        content=ft.Text("O Campo não foi preenchido", color="white"),
        actions=[
            ft.Container(
                content=ft.TextButton("Entendido", on_click=lambda e: close_alert(page, alert),
                                      style=ft.ButtonStyle(color="black")),
                bgcolor="white", border_radius=5, padding=ft.Padding.symmetric(horizontal=10)
            )
        ],
        actions_alignment="end"
    )
    page.overlay.append(alert)

    def route_change(e):
        page.views.clear()
        
        # --- VIEW DE TASKS ---
        if page.route and page.route.startswith("/tasks/"):
            goal_id = page.route.split("/")[-1]
            task_list = ft.Column(scroll="adaptive", expand=True, key="task_list")
            
            new_task_field = ft.TextField(
                label="Nova Task", width=300, color="white", border_color="white",
                on_submit=lambda e: add_task_action(page, task_list, goal_id, new_task_field)
            )

            page.views.append(
                ft.View(
                    route=page.route,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([new_task_field, ft.FilledButton("Adicionar", color="white",
                                       on_click=lambda e: add_task_action(page, task_list, goal_id, new_task_field))],
                                       alignment="center", spacing=10),
                                ft.Divider(color="white"),
                                task_list
                            ], expand=True),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text(f"Tarefas da Meta #{goal_id}", color="white"),
                        bgcolor="#111111",
                        leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=lambda _: page.go("/"))
                    ),
                    bgcolor="black"
                )
            )
            load_tasks_view(page, task_list, goal_id)

        # --- VIEW DA HOME (PADRÃO) ---
        else:
            meta_list = ft.Column(scroll="adaptive", expand=True, horizontal_alignment="center", key="meta_list")
            
            def toggle_view(e):
                current_view[0] = "grid" if current_view[0] == "list" else "list"
                load_initial_data(meta_list, page, current_view)
                page.update()

            view_button = ft.IconButton(
                icon=ft.Icons.GRID_VIEW if current_view[0] == "list" else ft.Icons.LIST,
                tooltip="Alternar Visualização",
                icon_color="white",
                on_click=toggle_view
            )

            new_goal = ft.TextField(
                label="Nova Meta", width=300, color="white", border_color="white",
                on_submit=lambda e: add_goal(page, new_goal, meta_list, alert, current_view)
            )
            
            page.views.append(
                ft.View(
                    route="/",
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([new_goal, ft.FilledButton("Insert", color="white", 
                                       on_click=lambda e: add_goal(page, new_goal, meta_list, alert, current_view))],
                                       alignment="center", spacing=10),
                                ft.Divider(color="white", height=20),
                                meta_list
                            ], expand=True),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text("Gerenciador de Metas", color="white", weight="bold"),
                        center_title=True, bgcolor="black", actions=[view_button]
                    ),
                    bgcolor="black"
                )
            )
            load_initial_data(meta_list, page, current_view)

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    def custom_go(route):
        page.route = route
        route_change(None) # Dispara manualmente o rebuild das views
        page.update()
    
    page.go = custom_go
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    start_monitor(page, db, current_view)
    
    if not page.route or page.route == "":
        page.route = "/"
    
    route_change(None)
    page.update()

if __name__ == "__main__":
    ft.run(main)