import flet as ft
from database import Database
import time
import threading


# Mapeamento de cores de categoria para hex (garante boa legibilidade em dark/light mode)
CATEGORY_COLORS = {
    "blue":   "#1E88E5",
    "green":  "#43A047",
    "red":    "#E53935",
    "purple": "#8E24AA",
    "orange": "#FB8C00",
    "teal":   "#00897B",
    "pink":   "#D81B60",
    "indigo": "#3949AB",
}


# ---------------------------------------------------------------------------
# COMPONENTE: Badge de categoria (usado em ItemGoal)
# ---------------------------------------------------------------------------
def build_category_badge(cat_name: str, cat_color: str):
    hex_color = CATEGORY_COLORS.get(cat_color, cat_color)
    return ft.Container(
        content=ft.Text(cat_name, size=10, color="white", weight="bold"),
        bgcolor=hex_color,
        border_radius=10,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
    )


# ---------------------------------------------------------------------------
# COMPONENTE: ItemGoal
# ---------------------------------------------------------------------------
class ItemGoal(ft.Container):
    def __init__(self, text, remove_func, goal_id, db, page, status=0,
                 view_mode="list", category_name=None, category_color=None):
        super().__init__()
        self.db = db
        self.app_page = page
        self.goal_id = goal_id
        self.remove_func = remove_func
        self.view_mode = view_mode

        # Configurações básicas baseadas no modo
        if self.view_mode == "list":
            self.width = None
            self.height = None
            self.padding = 5
            self.margin = ft.Margin.only(bottom=5)
            self.border_radius = 10
        else:  # Grid / Card mode
            self.width = 200
            self.height = 170
            self.padding = 15
            self.border_radius = 15

        self.bgcolor = "surfaceVariant"
        self.border = ft.Border.all(1, "outline")
        self.on_click = lambda _: page.go(f"/tasks/{self.goal_id}")

        self.checkbox = ft.Checkbox(
            value=True if status == 1 else False,
            on_change=self.card_status,
            fill_color="primary"
        )

        self.display_text = ft.Text(
            value=text,
            size=18 if self.view_mode == "grid" else 16,
            weight="bold" if self.view_mode == "grid" else "normal",
            color="onSurface" if status == 0 else "#A0A0A0",
            text_align="center",
            style=ft.TextStyle(
                decoration=(ft.TextDecoration.LINE_THROUGH if status == 1
                            else ft.TextDecoration.NONE)
            )
        )

        self.trash_icon = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color="error",
            tooltip="Excluir",
            on_click=lambda _: self.remove_func(self),
        )

        # Badge de categoria (opcional)
        cat_badge = build_category_badge(category_name, category_color) if category_name else ft.Container()

        if self.view_mode == "list":
            self.content = ft.Row(
                controls=[
                    self.checkbox,
                    ft.Column(
                        controls=[
                            self.display_text,
                            cat_badge,
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.VerticalDivider(),
                    self.trash_icon,
                ],
                alignment="start",
            )
        else:  # Grid / Card view mode
            self.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.checkbox, self.trash_icon],
                        alignment="spaceBetween"
                    ),
                    ft.Container(
                        content=self.display_text,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                        padding=ft.Padding.only(top=5)
                    ),
                    ft.Container(content=cat_badge, alignment=ft.Alignment(0, 0)),
                ],
                alignment="start",
                spacing=0
            )

    def card_status(self, e):
        status_int = 1 if self.checkbox.value else 0
        self.db.update_status(self.goal_id, status_int)

        global last_check_hash
        last_check_hash = str(self.db.load_goals())

        if self.checkbox.value:
            self.display_text.style.decoration = ft.TextDecoration.LINE_THROUGH
            self.display_text.color = "#A0A0A0"
        else:
            self.display_text.style.decoration = ft.TextDecoration.NONE
            self.display_text.color = "onSurface"
        # Usa page.update() em vez de self.update() para evitar erro
        # 'Control must be added to the page first' caso o monitor
        # tenha reconstruido a lista e descartado este controle da arvore.
        self.app_page.update()


# ---------------------------------------------------------------------------
# COMPONENTE: CategoryItem
# ---------------------------------------------------------------------------
class CategoryItem(ft.Container):
    def __init__(self, cat_id, name, color, page, on_delete):
        super().__init__()
        self.cat_id = cat_id
        self.padding = 12
        self.bgcolor = "surfaceVariant"
        self.border_radius = 10
        self.border = ft.Border.all(1, "outline")
        self.margin = ft.Margin.only(bottom=5)

        hex_color = CATEGORY_COLORS.get(color, color)
        color_dot = ft.Container(
            width=18, height=18, border_radius=9, bgcolor=hex_color,
        )

        self.content = ft.Row(
            controls=[
                color_dot,
                ft.Text(name, size=16, expand=True),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    icon_color="error",
                    tooltip="Excluir categoria",
                    on_click=lambda _: on_delete(cat_id, name),
                ),
            ],
            alignment="start",
        )


# ---------------------------------------------------------------------------
# FUNÇÕES DE GOALS
# ---------------------------------------------------------------------------
def delete_goal_action(page, db, meta_list, card_to_remove, current_view):
    db.delete_db_goal(card_to_remove.goal_id)
    global last_check_hash
    last_check_hash = str(db.load_goals())
    load_initial_data(db, meta_list, page, current_view)


def add_goal(page, db, new_goal, meta_list, alert, current_view, category_dropdown=None):
    if new_goal.value:
        category_id = None
        if category_dropdown and category_dropdown.value:
            try:
                category_id = int(category_dropdown.value)
            except (ValueError, TypeError):
                category_id = None

        db.add_goal(new_goal.value, category_id)

        global last_check_hash
        last_check_hash = str(db.load_goals())

        load_initial_data(db, meta_list, page, current_view)
        new_goal.value = ""
        if category_dropdown:
            category_dropdown.value = None
        page.update()
    else:
        alert.open = True
        page.update()


def handle_drag_accept(e, page, db, meta_list, current_view):
    src_control = page.get_control(e.src_id)
    if not src_control:
        return

    src_goal_id = src_control.data
    dest_goal_id = e.control.data

    if src_goal_id == dest_goal_id:
        return

    goals = db.load_goals()
    goal_ids = [g[0] for g in goals]

    src_goal_id = int(src_goal_id)
    dest_goal_id = int(dest_goal_id)

    if src_goal_id in goal_ids and dest_goal_id in goal_ids:
        src_index = goal_ids.index(src_goal_id)
        dest_index = goal_ids.index(dest_goal_id)

        goal_ids.pop(src_index)
        goal_ids.insert(dest_index, src_goal_id)

        db.update_goal_positions(goal_ids)

        global last_check_hash
        last_check_hash = str(db.load_goals())

        load_initial_data(db, meta_list, page, current_view)


def load_initial_data(db, meta_list, page, current_view):
    with _rebuild_lock:
        meta_list.controls.clear()
        goals_data = db.load_goals()

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
            # g: (id, title, status, position, cat_id, cat_name, cat_color)
            card = ItemGoal(
                text=g[1],
                remove_func=lambda card: delete_goal_action(page, db, meta_list, card, current_view),
                goal_id=g[0],
                db=db,
                page=page,
                status=g[2],
                view_mode=current_view[0],
                category_name=g[5],
                category_color=g[6],
            )

            draggable_card = ft.Draggable(
                group="goals",
                content=card,
                data=str(g[0])
            )

            drag_target = ft.DragTarget(
                group="goals",
                content=draggable_card,
                data=str(g[0]),
                on_accept=lambda e: handle_drag_accept(e, page, db, meta_list, current_view)
            )

            view_container.controls.append(drag_target)

        meta_list.controls.append(view_container)
        page.update()


def close_alert(page, alert):
    alert.open = False
    page.update()


# ---------------------------------------------------------------------------
# FUNÇÕES DE CATEGORIES
# ---------------------------------------------------------------------------
def load_categories_view(page, db, cat_list):
    cat_list.controls.clear()
    categories = db.load_categories()

    if not categories:
        cat_list.controls.append(
            ft.Container(
                content=ft.Text("Nenhuma categoria criada ainda.", italic=True, color="grey"),
                padding=20,
            )
        )
        page.update()
        return

    view_container = ft.ListView(expand=True, spacing=8, padding=10)
    for cat in categories:
        # cat: (id, name, color)
        item = CategoryItem(
            cat_id=cat[0],
            name=cat[1],
            color=cat[2],
            page=page,
            on_delete=lambda cid=cat[0], cname=cat[1]: show_delete_category_dialog(page, db, cat_list, cid, cname),
        )
        view_container.controls.append(item)

    cat_list.controls.append(view_container)
    page.update()


def add_category_action(page, db, name_field, color_dropdown, cat_list):
    if name_field.value.strip():
        try:
            db.add_category(name_field.value.strip(), color_dropdown.value or "blue")
            name_field.value = ""
            name_field.error_text = None
            load_categories_view(page, db, cat_list)
        except Exception:
            name_field.error_text = "Categoria já existe."
            page.update()
    else:
        name_field.error_text = "Campo obrigatório."
        page.update()


def show_delete_category_dialog(page, db, cat_list, cat_id, cat_name):
    def confirm_delete(e):
        dialog.open = False
        page.update()
        db.delete_category(cat_id)

        global last_check_hash
        last_check_hash = str(db.load_goals()) + str(db.load_categories())

        load_categories_view(page, db, cat_list)

    def cancel_delete(e):
        dialog.open = False
        page.update()

    dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=10, side=ft.BorderSide(2, "outline")),
        title=ft.Row([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="error", size=28),
            ft.Text("Excluir Categoria", size=22, weight="bold"),
        ], spacing=8),
        content=ft.Text(
            f'Tem certeza que deseja excluir a categoria "{cat_name}"?\n\n'
            "⚠️ Atenção: as metas vinculadas a ela ficarão sem categoria e "
            "os dados desta categoria serão removidos do Dashboard.",
            size=14,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=cancel_delete),
            ft.Container(
                content=ft.TextButton(
                    "Excluir",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color="white"),
                ),
                bgcolor="error",
                border_radius=5,
                padding=ft.Padding.symmetric(horizontal=10),
            ),
        ],
        actions_alignment="end",
    )
    page.overlay.append(dialog)
    dialog.open = True
    page.update()


# ---------------------------------------------------------------------------
# MONITOR ASSÍNCRONO
# ---------------------------------------------------------------------------
last_check_hash = None
_rebuild_lock = threading.Lock()


def start_monitor(page, db, current_view):
    def check_database():
        global last_check_hash
        while True:
            try:
                current_route = page.route

                # ---- Monitora HOME (/): Metas ----
                if current_route == "/":
                    goals_data = db.load_goals()
                    current_hash = str(goals_data)
                    if current_hash != last_check_hash:
                        target_meta_list = None
                        for view in page.views:
                            if view.route == "/":
                                for control in view.controls:
                                    if hasattr(control, "content") and hasattr(control.content, "controls"):
                                        res = control.content.controls
                                        target_meta_list = next(
                                            (c for c in res if getattr(c, "key", None) == "meta_list"), None
                                        )
                                        if target_meta_list:
                                            break
                        if target_meta_list:
                            load_initial_data(db, target_meta_list, page, current_view)
                            last_check_hash = current_hash

                # ---- Monitora TASKS (/tasks/...): Sub-tarefas ----
                elif current_route.startswith("/tasks/"):
                    goal_id = current_route.split("/")[-1]
                    tasks_data = db.load_tasks(goal_id)
                    current_hash = f"tasks_{goal_id}_{str(tasks_data)}"
                    if current_hash != last_check_hash:
                        target_task_list = None
                        for view in page.views:
                            if view.route.startswith("/tasks/"):
                                for control in view.controls:
                                    if hasattr(control, "content") and hasattr(control.content, "controls"):
                                        res = control.content.controls
                                        target_task_list = next(
                                            (c for c in res if getattr(c, "key", None) == "task_list"), None
                                        )
                                        if target_task_list:
                                            break
                        if target_task_list:
                            load_tasks_view(page, db, target_task_list, goal_id)
                            last_check_hash = current_hash

                # ---- Monitora DASHBOARD (/dashboard) ----
                elif current_route == "/dashboard":
                    goals_data = db.load_goals()
                    cats_data = db.load_categories()
                    current_hash = f"dashboard_{str(goals_data)}_{str(cats_data)}"
                    if current_hash != last_check_hash:
                        target_dash = None
                        for view in page.views:
                            if view.route == "/dashboard":
                                for control in view.controls:
                                    if hasattr(control, "content") and hasattr(control.content, "controls"):
                                        res = control.content.controls
                                        target_dash = next(
                                            (c for c in res if getattr(c, "key", None) == "dashboard_content"), None
                                        )
                                        if target_dash:
                                            break
                        if target_dash:
                            from dashboard import build_dashboard_content
                            build_dashboard_content(target_dash, page, db)
                            last_check_hash = current_hash

                time.sleep(0.5)
            except Exception as ex:
                print(f"Erro no monitor: {ex}")
                time.sleep(1)

    thread = threading.Thread(target=check_database, daemon=True)
    thread.start()


# ---------------------------------------------------------------------------
# COMPONENTE E FUNÇÕES DE TASKS
# ---------------------------------------------------------------------------
class TaskItem(ft.Container):
    def __init__(self, text, task_id, goal_id, db, page, meta_list, status=0):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.goal_id = goal_id
        self.app_page = page
        self.meta_list = meta_list

        self.padding = 10
        self.bgcolor = "surfaceVariant"
        self.border_radius = 10
        self.border = ft.Border.all(1, "outline")

        self.checkbox = ft.Checkbox(
            value=True if status == 1 else False,
            on_change=self.toggle_status,
            fill_color="primary"
        )

        self.display_text = ft.Text(
            text,
            color="#A0A0A0" if status == 1 else "onSurface",
            size=16,
            expand=True,
            style=ft.TextStyle(
                decoration=ft.TextDecoration.LINE_THROUGH if status == 1 else ft.TextDecoration.NONE
            )
        )

        self.content = ft.Row(
            controls=[
                self.checkbox,
                self.display_text,
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="error", on_click=self.delete_task)
            ]
        )

    def toggle_status(self, e):
        status_int = 1 if self.checkbox.value else 0
        self.db.update_task_status(self.task_id, status_int)

        global last_check_hash
        last_check_hash = f"tasks_{self.goal_id}_{str(self.db.load_tasks(self.goal_id))}"

        if self.checkbox.value:
            self.display_text.style.decoration = ft.TextDecoration.LINE_THROUGH
            self.display_text.color = "#A0A0A0"
        else:
            self.display_text.style.decoration = ft.TextDecoration.NONE
            self.display_text.color = "onSurface"
        # Usa page.update() pelo mesmo motivo do ItemGoal.card_status
        self.app_page.update()

    def delete_task(self, e):
        self.db.delete_task(self.task_id)

        global last_check_hash
        last_check_hash = f"tasks_{self.goal_id}_{str(self.db.load_tasks(self.goal_id))}"

        load_tasks_view(self.app_page, self.db, self.meta_list, self.goal_id)


def load_tasks_view(page, db, meta_list, goal_id):
    meta_list.controls.clear()
    tasks_data = db.load_tasks(goal_id)

    view_container = ft.ListView(expand=True, spacing=10, padding=10)

    for t in tasks_data:
        task_card = TaskItem(
            text=t[2], task_id=t[0], goal_id=t[1],
            db=db, page=page, meta_list=meta_list, status=t[3]
        )
        view_container.controls.append(task_card)

    meta_list.controls.append(view_container)
    page.update()


def add_task_action(page, db, meta_list, goal_id, field):
    if field.value:
        db.add_task(goal_id, field.value)
        field.value = ""

        global last_check_hash
        last_check_hash = f"tasks_{goal_id}_{str(db.load_tasks(goal_id))}"

        load_tasks_view(page, db, meta_list, goal_id)
