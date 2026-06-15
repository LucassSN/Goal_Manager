import flet as ft
from logic import (add_goal, close_alert, load_initial_data, start_monitor,
                   load_tasks_view, add_task_action,
                   load_categories_view, add_category_action, CATEGORY_COLORS, Sidebar)
from database import Database
from dashboard_builder import create_builder_view, DashboardBuilderView

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

    # Instância singleton do Dashboard Builder — preserva estado entre navegações
    dashboard_builder_instance = [None]

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        # Persiste a escolha no banco de dados
        db.set_setting("theme", "light" if page.theme_mode == ft.ThemeMode.LIGHT else "dark")
        route_change(None)
        page.update()

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
        # Limpa overlays temporários (preserva o alerta persistente)
        page.overlay.clear()
        page.overlay.append(alert)

        # ----------------------------------------------------------------
        # VIEW DE TASKS
        # ----------------------------------------------------------------
        if page.route and page.route.startswith("/tasks/"):
            goal_id = page.route.split("/")[-1]
            goal_title = db.get_goal(goal_id)
            task_list = ft.Column(scroll="adaptive", expand=True, key="task_list")

            new_task_field = ft.TextField(
                label="Título da Task",
                autofocus=True,
                width=380,
                border_radius=10,
            )

            def close_task_dialog(e=None):
                create_task_dialog.open = False
                new_task_field.value = ""
                page.update()

            def on_add_task(e=None):
                if new_task_field.value and new_task_field.value.strip():
                    add_task_action(page, db, task_list, goal_id, new_task_field)
                    close_task_dialog()
                else:
                    create_task_dialog.open = False
                    page.update()
                    alert.open = True
                    page.update()

            new_task_field.on_submit = on_add_task

            create_task_dialog = ft.AlertDialog(
                modal=True,
                shape=ft.RoundedRectangleBorder(radius=16, side=ft.BorderSide(1, "outline")),
                title=ft.Row([
                    ft.Icon(ft.Icons.CHECKLIST, color="primary", size=26),
                    ft.Text("Nova Sub-tarefa", size=22, weight="bold"),
                ], spacing=10),
                content=ft.Column([
                    new_task_field,
                ], spacing=16, tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=close_task_dialog),
                    ft.FilledButton(
                        "Criar Task",
                        icon=ft.Icons.CHECK,
                        on_click=on_add_task,
                    ),
                ],
                actions_alignment="end",
            )
            
            # Garante que só o alert global e o dialog atual fiquem no overlay
            page.overlay.append(create_task_dialog)

            def open_task_dialog(e):
                new_task_field.value = ""
                create_task_dialog.open = True
                page.update()

            page.views.clear()
            page.views.append(
                ft.View(
                    route=page.route,
                    floating_action_button=ft.FloatingActionButton(
                        icon=ft.Icons.ADD,
                        tooltip="Nova Task",
                        on_click=open_task_dialog,
                    ),
                    controls=[
                        ft.Row([
                            Sidebar(page, page.route, toggle_theme),
                            ft.VerticalDivider(width=1),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/")),
                                        ft.Text(f"Metas > {goal_title}", size=24, weight="bold"),
                                    ], spacing=10),
                                    ft.Divider(),
                                    task_list
                                ], expand=True),
                                padding=20, expand=True
                            )
                        ], expand=True)
                    ]
                )
            )
            load_tasks_view(page, db, task_list, goal_id)

        # ----------------------------------------------------------------
        # VIEW DO DASHBOARD (Builder customizável)
        # ----------------------------------------------------------------
        elif page.route == "/dashboard":
            builder, builder_container = create_builder_view(
                page, db, builder=dashboard_builder_instance[0]
            )
            dashboard_builder_instance[0] = builder
            # Armazena no page para o monitor poder chamar refresh()
            page.data = page.data if hasattr(page, 'data') and isinstance(page.data, dict) else {}
            if not isinstance(page.data, dict):
                page.data = {}
            page.data["dashboard_builder"] = builder

            page.views.clear()
            page.views.append(
                ft.View(
                    route="/dashboard",
                    controls=[
                        ft.Row([
                            Sidebar(page, "/dashboard", toggle_theme),
                            ft.VerticalDivider(width=1),
                            builder_container
                        ], expand=True)
                    ]
                )
            )

        # ----------------------------------------------------------------
        # VIEW DE CATEGORIAS
        # ----------------------------------------------------------------
        elif page.route == "/categories":
            cat_list = ft.Column(scroll="adaptive", expand=True, key="cat_list")

            cat_name_field = ft.TextField(
                label="Nome da categoria",
                autofocus=True,
                width=380,
                border_radius=10,
            )
            color_dropdown = ft.Dropdown(
                label="Cor",
                width=380,
                value="blue",
                options=COLOR_OPTIONS,
                border_radius=10,
            )

            def close_cat_dialog(e=None):
                create_cat_dialog.open = False
                cat_name_field.value = ""
                cat_name_field.error_text = None
                color_dropdown.value = "blue"
                page.update()

            def on_add_category(e=None):
                if cat_name_field.value and cat_name_field.value.strip():
                    add_category_action(page, db, cat_name_field, color_dropdown, cat_list)
                    if not cat_name_field.error_text:
                        close_cat_dialog()
                else:
                    create_cat_dialog.open = False
                    page.update()
                    alert.open = True
                    page.update()

            cat_name_field.on_submit = on_add_category

            create_cat_dialog = ft.AlertDialog(
                modal=True,
                shape=ft.RoundedRectangleBorder(radius=16, side=ft.BorderSide(1, "outline")),
                title=ft.Row([
                    ft.Icon(ft.Icons.CATEGORY, color="primary", size=26),
                    ft.Text("Nova Categoria", size=22, weight="bold"),
                ], spacing=10),
                content=ft.Column([
                    cat_name_field,
                    color_dropdown,
                ], spacing=16, tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=close_cat_dialog),
                    ft.FilledButton(
                        "Criar Categoria",
                        icon=ft.Icons.CHECK,
                        on_click=on_add_category,
                    ),
                ],
                actions_alignment="end",
            )

            page.overlay.append(create_cat_dialog)

            def open_cat_dialog(e):
                cat_name_field.value = ""
                cat_name_field.error_text = None
                color_dropdown.value = "blue"
                create_cat_dialog.open = True
                page.update()

            page.views.clear()
            page.views.append(
                ft.View(
                    route="/categories",
                    floating_action_button=ft.FloatingActionButton(
                        icon=ft.Icons.ADD,
                        tooltip="Nova Categoria",
                        on_click=open_cat_dialog,
                    ),
                    controls=[
                        ft.Row([
                            Sidebar(page, "/categories", toggle_theme),
                            ft.VerticalDivider(width=1),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Gerenciar Categorias", size=26, weight="bold"),
                                    ft.Divider(height=20),
                                    cat_list,
                                ], expand=True),
                                padding=20, expand=True
                            )
                        ], expand=True)
                    ]
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
                view_button.icon = ft.Icons.GRID_VIEW if current_view[0] == "list" else ft.Icons.LIST
                load_initial_data(db, meta_list, page, current_view)
                page.update()

            view_button = ft.IconButton(
                icon=ft.Icons.GRID_VIEW if current_view[0] == "list" else ft.Icons.LIST,
                tooltip="Alternar Visualização",
                on_click=toggle_view
            )

            # ---- Campos do modal de criação de meta ----
            new_goal = ft.TextField(
                label="Título da Meta",
                autofocus=True,
                width=380,
                border_radius=10,
            )

            categories = db.load_categories()
            cat_options = [ft.dropdown.Option(key="", text="Sem categoria")]
            for cat in categories:
                cat_options.append(ft.dropdown.Option(key=str(cat[0]), text=cat[1]))

            category_dropdown = ft.Dropdown(
                label="Categoria",
                width=380,
                value="",
                options=cat_options,
                border_radius=10,
            )

            def close_create_dialog(e=None):
                create_dialog.open = False
                new_goal.value = ""
                category_dropdown.value = ""
                page.update()

            def on_add_goal(e=None):
                if new_goal.value and new_goal.value.strip():
                    add_goal(page, db, new_goal, meta_list, alert, current_view, category_dropdown)
                    close_create_dialog()
                else:
                    # Exibe o alerta de campo vazio
                    create_dialog.open = False
                    page.update()
                    alert.open = True
                    page.update()

            new_goal.on_submit = on_add_goal

            create_dialog = ft.AlertDialog(
                modal=True,
                shape=ft.RoundedRectangleBorder(radius=16, side=ft.BorderSide(1, "outline")),
                title=ft.Row([
                    ft.Icon(ft.Icons.ADD_TASK, color="primary", size=26),
                    ft.Text("Nova Meta", size=22, weight="bold"),
                ], spacing=10),
                content=ft.Column([
                    new_goal,
                    category_dropdown,
                ], spacing=16, tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=close_create_dialog),
                    ft.FilledButton(
                        "Criar Meta",
                        icon=ft.Icons.CHECK,
                        on_click=on_add_goal,
                    ),
                ],
                actions_alignment="end",
            )
            page.overlay.append(create_dialog)

            def open_create_dialog(e):
                # Recarrega as categorias sempre que o modal abre
                cats = db.load_categories()
                category_dropdown.options = [
                    ft.dropdown.Option(key="", text="Sem categoria")
                ] + [ft.dropdown.Option(key=str(c[0]), text=c[1]) for c in cats]
                category_dropdown.value = ""
                new_goal.value = ""
                create_dialog.open = True
                page.update()

            page.views.clear()
            page.views.append(
                ft.View(
                    route="/",
                    floating_action_button=ft.FloatingActionButton(
                        icon=ft.Icons.ADD,
                        tooltip="Nova Meta",
                        on_click=open_create_dialog,
                    ),
                    controls=[
                        ft.Row([
                            Sidebar(page, "/", toggle_theme),
                            ft.VerticalDivider(width=1),
                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text("Minhas Metas", size=26, weight="bold"),
                                        view_button
                                    ], alignment="spaceBetween"),
                                    ft.Divider(height=20),
                                    meta_list
                                ], expand=True),
                                padding=20, expand=True
                            )
                        ], expand=True)
                    ]
                )
            )
            load_initial_data(db, meta_list, page, current_view)

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            # Já está na raiz — apenas recarrega a Home
            page.go("/")

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