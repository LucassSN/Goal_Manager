import flet as ft
from logic import add_goal, close_alert, load_initial_data, start_monitor, load_tasks_view, add_task_action
from database import Database

db = Database()

def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    # Iniciando no Tema Escuro padrão
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0 
    
    current_view = ["list"]

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        for view in page.views:
            if view.appbar:
                for action in view.appbar.actions:
                    if action.tooltip == "Alternar Tema":
                        # Lua = ft.Icons.DARK_MODE
                        # Sol = ft.Icons.LIGHT_MODE
                        action.icon = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE
        page.update()

    def create_theme_button():
        return ft.IconButton(
            icon=ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE,
            tooltip="Alternar Tema",
            on_click=toggle_theme
        )

    alert = ft.AlertDialog(
        shape=ft.RoundedRectangleBorder(radius=10, side=ft.BorderSide(2, "outline")),
        title=ft.Text("Campo Vazio", size=30),
        content=ft.Text("O Campo não foi preenchido"),
        actions=[
            ft.Container(
                content=ft.TextButton("Entendido", on_click=lambda e: close_alert(page, alert),
                                      style=ft.ButtonStyle(color="onPrimary")),
                bgcolor="primary", border_radius=5, padding=ft.Padding.symmetric(horizontal=10)
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
            goal_title = db.get_goal(goal_id)
            task_list = ft.Column(scroll="adaptive", expand=True, key="task_list")
            
            new_task_field = ft.TextField(
                label="Nova Task", width=300,
                on_submit=lambda e: add_task_action(page, db, task_list, goal_id, new_task_field)
            )

            page.views.append(
                ft.View(
                    route=page.route,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([new_task_field, ft.FilledButton("Adicionar", 
                                       on_click=lambda e: add_task_action(page, db, task_list, goal_id, new_task_field))],
                                       alignment="center", spacing=10),
                                ft.Divider(),
                                task_list
                            ], expand=True),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text(goal_title),
                        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")),
                        actions=[create_theme_button()]
                    )
                )
            )
            load_tasks_view(page, db, task_list, goal_id)

        # --- VIEW DE DASHBOARD (ANALÍTICO) ---
        elif page.route == "/dashboard":
            page.views.append(
                ft.View(
                    route="/dashboard",
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Visão Analítica", size=26, weight="bold"),
                                ft.Text("Espaço estruturado para futuros gráficos de produtividade.", color="outline"),
                                ft.Row([
                                    # Card 1: Porcentagem de Metas
                                    ft.Container(
                                        content=ft.Column([ft.Icon(ft.Icons.PIE_CHART, size=35), ft.Text("Desempenho Global", weight="bold"), ft.Text("(Em Breve)", size=12)], alignment="center", horizontal_alignment="center"),
                                        bgcolor="surfaceVariant", padding=30, border_radius=10, expand=True, border=ft.border.all(1, "outline")
                                    ),
                                    # Card 2: Metas por Mês
                                    ft.Container(
                                        content=ft.Column([ft.Icon(ft.Icons.BAR_CHART, size=35), ft.Text("Metas por Mês", weight="bold"), ft.Text("(Em Breve)", size=12)], alignment="center", horizontal_alignment="center"),
                                        bgcolor="surfaceVariant", padding=30, border_radius=10, expand=True, border=ft.border.all(1, "outline")
                                    ),
                                ]),
                                ft.Row([
                                    # Card 3: Submetas Concluídas
                                    ft.Container(
                                        content=ft.Column([ft.Icon(ft.Icons.CHECKLIST, size=35), ft.Text("Submetas Concluídas", weight="bold"), ft.Text("(Em Breve)", size=12)], alignment="center", horizontal_alignment="center"),
                                        bgcolor="surfaceVariant", padding=30, border_radius=10, expand=True, border=ft.border.all(1, "outline")
                                    )
                                ])
                            ], expand=True, spacing=20),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text("Dashboard"),
                        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")),
                        actions=[create_theme_button()]
                    )
                )
            )

        # --- VIEW DA HOME (PADRÃO) ---
        else:
            meta_list = ft.Column(scroll="adaptive", expand=True, horizontal_alignment="center", key="meta_list")
            
            def toggle_view(e):
                current_view[0] = "grid" if current_view[0] == "list" else "list"
                load_initial_data(db, meta_list, page, current_view)
                page.update()

            view_button = ft.IconButton(
                icon=ft.Icons.GRID_VIEW if current_view[0] == "list" else ft.Icons.LIST,
                tooltip="Alternar Visualização",
                on_click=toggle_view
            )

            new_goal = ft.TextField(
                label="Nova Meta", width=300,
                on_submit=lambda e: add_goal(page, db, new_goal, meta_list, alert, current_view)
            )
            
            page.views.append(
                ft.View(
                    route="/",
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([new_goal, ft.FilledButton("Insert", 
                                       on_click=lambda e: add_goal(page, db, new_goal, meta_list, alert, current_view))],
                                       alignment="center", spacing=10),
                                ft.Divider(height=20),
                                meta_list
                            ], expand=True),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text("Gerenciador de Metas", weight="bold"),
                        center_title=True, actions=[
                            ft.IconButton(icon=ft.Icons.DASHBOARD, tooltip="Dashboard", on_click=lambda _: page.go("/dashboard")),
                            create_theme_button(), 
                            view_button
                        ]
                    )
                )
            )
            load_initial_data(db, meta_list, page, current_view)

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