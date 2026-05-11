import flet as ft
from logic import (add_goal, close_alert, load_initial_data, start_monitor,
                   load_tasks_view, add_task_action,
                   load_categories_view, add_category_action, CATEGORY_COLORS)
from database import Database
from dashboard import create_dashboard_view

db = Database()

# Opções de cor para o dropdown de categorias
COLOR_OPTIONS = [
    ft.dropdown.Option(key="blue",   text="🔵 Azul"),
    ft.dropdown.Option(key="green",  text="🟢 Verde"),
    ft.dropdown.Option(key="red",    text="🔴 Vermelho"),
    ft.dropdown.Option(key="purple", text="🟣 Roxo"),
    ft.dropdown.Option(key="orange", text="🟠 Laranja"),
    ft.dropdown.Option(key="teal",   text="🩵 Teal"),
    ft.dropdown.Option(key="pink",   text="🩷 Rosa"),
    ft.dropdown.Option(key="indigo", text="🔵 Índigo"),
]


def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    # Carrega o tema salvo pelo usuário; padrão = escuro na primeira execução
    saved_theme = db.get_setting("theme", "dark")
    page.theme_mode = ft.ThemeMode.LIGHT if saved_theme == "light" else ft.ThemeMode.DARK
    page.padding = 0

    current_view = ["list"]

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        # Persiste a escolha no banco de dados
        db.set_setting("theme", "light" if page.theme_mode == ft.ThemeMode.LIGHT else "dark")
        for view in page.views:
            if view.appbar:
                for action in view.appbar.actions:
                    if action.tooltip == "Alternar Tema":
                        action.icon = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE
        page.update()

    def create_theme_button():
        return ft.IconButton(
            icon=ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE,
            tooltip="Alternar Tema",
            on_click=toggle_theme
        )

    # Alerta de campo vazio (metas)
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

        # ----------------------------------------------------------------
        # VIEW DE TASKS
        # ----------------------------------------------------------------
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
                                ft.Row([new_task_field, ft.FilledButton(
                                    "Adicionar",
                                    on_click=lambda e: add_task_action(page, db, task_list, goal_id, new_task_field)
                                )], alignment="center", spacing=10),
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

        # ----------------------------------------------------------------
        # VIEW DO DASHBOARD
        # ----------------------------------------------------------------
        elif page.route == "/dashboard":
            page.views.append(
                ft.View(
                    route="/dashboard",
                    controls=[create_dashboard_view(page, db)],
                    appbar=ft.AppBar(
                        title=ft.Text("Dashboard"),
                        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")),
                        actions=[create_theme_button()]
                    )
                )
            )

        # ----------------------------------------------------------------
        # VIEW DE CATEGORIAS
        # ----------------------------------------------------------------
        elif page.route == "/categories":
            cat_list = ft.Column(scroll="adaptive", expand=True, key="cat_list")

            cat_name_field = ft.TextField(label="Nome da categoria", width=250)
            color_dropdown = ft.Dropdown(
                label="Cor",
                width=160,
                value="blue",
                options=COLOR_OPTIONS,
            )

            def on_add_category(e):
                add_category_action(page, db, cat_name_field, color_dropdown, cat_list)

            cat_name_field.on_submit = on_add_category

            page.views.append(
                ft.View(
                    route="/categories",
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Gerenciar Categorias", size=22, weight="bold"),
                                ft.Row([
                                    cat_name_field,
                                    color_dropdown,
                                    ft.FilledButton("Adicionar", on_click=on_add_category,
                                                    icon=ft.Icons.ADD),
                                ], alignment="start", spacing=10, wrap=True),
                                ft.Divider(height=20),
                                cat_list,
                            ], expand=True),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text("Categorias"),
                        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")),
                        actions=[create_theme_button()]
                    )
                )
            )
            load_categories_view(page, db, cat_list)

        # ----------------------------------------------------------------
        # VIEW DA HOME (padrão)
        # ----------------------------------------------------------------
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

            new_goal = ft.TextField(label="Nova Meta", width=280)

            # Dropdown de categoria (opcional)
            categories = db.load_categories()
            cat_options = [ft.dropdown.Option(key="", text="Sem categoria")]
            for cat in categories:
                cat_options.append(ft.dropdown.Option(key=str(cat[0]), text=cat[1]))

            category_dropdown = ft.Dropdown(
                label="Categoria",
                width=170,
                value="",
                options=cat_options,
            )

            def on_add_goal(e):
                add_goal(page, db, new_goal, meta_list, alert, current_view, category_dropdown)

            new_goal.on_submit = on_add_goal

            page.views.append(
                ft.View(
                    route="/",
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    new_goal,
                                    category_dropdown,
                                    ft.FilledButton("Insert", on_click=on_add_goal),
                                ], alignment="center", spacing=10, wrap=True),
                                ft.Divider(height=20),
                                meta_list
                            ], expand=True),
                            padding=20, expand=True
                        )
                    ],
                    appbar=ft.AppBar(
                        title=ft.Text("Gerenciador de Metas", weight="bold"),
                        center_title=True,
                        actions=[
                            ft.IconButton(icon=ft.Icons.LABEL, tooltip="Categorias",
                                          on_click=lambda _: page.go("/categories")),
                            ft.IconButton(icon=ft.Icons.DASHBOARD, tooltip="Dashboard",
                                          on_click=lambda _: page.go("/dashboard")),
                            create_theme_button(),
                            view_button,
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
        route_change(None)
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