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
# AUXILIAR: Barra de progresso para o card no modo Grid
# ---------------------------------------------------------------------------
def _build_card_progress_bar(progress: float, category_color: str = None):
    """Barra de progresso proporcional (expand) — nunca estoura o card."""
    fill_pct = int(progress * 100)
    rest_pct = 100 - fill_pct
    bar_color = CATEGORY_COLORS.get(category_color, "#1E88E5") if category_color else "#1E88E5"

    children = []
    if fill_pct > 0:
        children.append(
            ft.Container(height=5, bgcolor=bar_color, border_radius=3, expand=fill_pct)
        )
    if rest_pct > 0:
        children.append(
            ft.Container(height=5, bgcolor="#FFFFFF25", border_radius=3, expand=rest_pct)
        )
    if not children:
        children = [ft.Container(height=5, bgcolor="#FFFFFF25", border_radius=3, expand=1)]

    return ft.Row(children, spacing=2, expand=True)


# ---------------------------------------------------------------------------
# COMPONENTE: ItemGoal
# ---------------------------------------------------------------------------
class ItemGoal(ft.Container):
    def __init__(self, text, remove_func, edit_func, goal_id, db, page, status=0,
                 view_mode="list", category_id=None, category_name=None, category_color=None):
        super().__init__()
        self.db = db
        self.app_page = page
        self.goal_id = goal_id
        self.remove_func = remove_func
        self.edit_func = edit_func
        self.category_id = category_id
        self.view_mode = view_mode

        # -- Progresso das sub-tarefas (buscado apenas no modo grid para evitar N queries desnecessárias) --
        if view_mode == "grid":
            tasks = db.load_tasks(goal_id)
            total_tasks    = len(tasks)
            done_tasks     = sum(1 for t in tasks if t[3] == 1)
            progress_ratio = done_tasks / total_tasks if total_tasks > 0 else 0.0
        else:
            total_tasks, done_tasks, progress_ratio = 0, 0, 0.0

        # -- Configurações de layout e cor baseadas no modo --
        if self.view_mode == "list":
            self.width         = None
            self.height        = None
            self.padding       = 5
            self.margin        = ft.Margin.only(bottom=5)
            self.border_radius = 10
            self.bgcolor       = "surfaceVariant"
            self.border        = ft.Border.all(1, "outline")
            # Hover sutil no modo lista
            self.animate_scale = ft.Animation(150, "easeOut")
            self.on_hover      = self._hover_card
        else:  # Grid / Card mode
            self.width         = 230
            self.height        = 200
            self.padding       = 15
            self.border_radius = 16
            # Borda colorida pela categoria (ou outline padrão do tema)
            _cat_hex = CATEGORY_COLORS.get(category_color) if category_color else None
            self.bgcolor = "surfaceVariant"
            self.border  = ft.Border.all(2, _cat_hex or "outline")
            # salva a cor original da borda para restaurar ao desmarcar
            self._original_border_color = _cat_hex or "outline"
            # Hover de escala no modo grid
            self.animate_scale = ft.Animation(200, "easeOut")
            self.on_hover      = self._hover_card

        self.on_click = lambda _: page.go(f"/tasks/{self.goal_id}")

        self.checkbox = ft.Checkbox(
            value=True if status == 1 else False,
            on_change=self.card_status,
            fill_color="primary"
        )

        # Cor do texto: adaptativo ao tema (surfaceVariant responde ao dark/light mode)
        text_color = "#A0A0A0" if status == 1 else "onSurface"

        self.display_text = ft.Text(
            value=text,
            size=18 if self.view_mode == "grid" else 16,
            weight="bold" if self.view_mode == "grid" else "normal",
            color=text_color,
            text_align="center" if view_mode == "grid" else "left",
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

        self.edit_icon = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            icon_color="primary",
            tooltip="Editar",
            on_click=lambda _: self.edit_func(self),
        )

        # Badge de categoria no modo Lista (mantido igual)
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
                    self.edit_icon,
                    self.trash_icon,
                ],
                alignment="start",
            )
        else:  # Grid / Card view mode — novo layout visual
            # Badge de categoria para o Grid: pílula colorida no topo direito
            if category_name:
                badge_hex   = CATEGORY_COLORS.get(category_color, "#1E88E5")
                badge_txt_c = "#1A1A1A" if category_color in ("orange",) else "white"
                grid_cat_badge = ft.Container(
                    content=ft.Text(category_name, size=10, color=badge_txt_c, weight="bold"),
                    bgcolor=badge_hex,
                    border_radius=12,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                )
            else:
                grid_cat_badge = ft.Container()  # espaçador vazio

            # Barra de progresso proporcional
            progress_bar = _build_card_progress_bar(progress_ratio, category_color)

            # Contador de tarefas
            task_counter = ft.Text(
                f"{done_tasks}/{total_tasks} tarefas",
                size=11,
                color="grey",
            )

            self.content = ft.Column(
                controls=[
                    # 1. Topo: checkbox (esquerda) + badge categoria (direita)
                    ft.Row(
                        controls=[self.checkbox, grid_cat_badge],
                        alignment="spaceBetween",
                    ),
                    # 2. Centro: título expandindo o espaço restante
                    ft.Container(
                        content=self.display_text,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    ),
                    # 3. Barra de progresso
                    progress_bar,
                    # 4. Rodapé: contador (esquerda) + botões de ação (direita)
                    ft.Row(
                        controls=[
                            task_counter,
                            ft.Row(
                                controls=[self.edit_icon, self.trash_icon],
                                spacing=0,
                            ),
                        ],
                        alignment="spaceBetween",
                        vertical_alignment="center",
                    ),
                ],
                spacing=4,
                expand=True,
            )

    def _hover_card(self, e):
        """Aumenta ligeiramente a escala ao passar o mouse sobre o card."""
        entering = e.data == "true"
        if self.view_mode == "grid":
            self.scale = 1.04 if entering else 1.0
        else:
            self.scale = 1.01 if entering else 1.0
        self.update()

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


def edit_goal_action(page, db, meta_list, card_to_edit, current_view):
    title_field = ft.TextField(
        label="Título da Meta",
        value=card_to_edit.display_text.value,
        autofocus=True,
        width=380,
        border_radius=10,
    )

    categories = db.load_categories()
    cat_options = [ft.dropdown.Option(key="", text="Sem categoria")]
    for cat in categories:
        cat_options.append(ft.dropdown.Option(key=str(cat[0]), text=cat[1]))

    initial_cat_value = str(card_to_edit.category_id) if card_to_edit.category_id is not None else ""

    category_dropdown = ft.Dropdown(
        label="Categoria",
        width=380,
        value=initial_cat_value,
        options=cat_options,
        border_radius=10,
    )

    dialog = None  # será atribuído abaixo

    def _close_dialog(e=None):
        """Fecha o dialog e o remove do overlay sem disparar navegação."""
        if dialog is not None:
            dialog.open = False
            if dialog in page.overlay:
                page.overlay.remove(dialog)
        page.update()

    def _find_live_meta_list():
        """Busca o meta_list ATUAL na árvore de views (evita usar referência stale)."""
        for view in page.views:
            if view.route == "/":
                found = _find_control_by_key(view.controls, "meta_list")
                if found:
                    return found
        # fallback: usa a referência do closure (pode ser stale, mas é melhor que nada)
        return meta_list

    def save_goal(e=None):
        try:
            if title_field.value and title_field.value.strip():
                new_title = title_field.value.strip()
                new_category_id = int(category_dropdown.value) if category_dropdown.value else None

                db.update_goal(card_to_edit.goal_id, new_title, new_category_id)

                global last_check_hash
                last_check_hash = str(db.load_goals())

                # 1. Fecha o dialog PRIMEIRO (sem navegar)
                _close_dialog()

                # 2. Encontra o meta_list VIVO na árvore de views
                live_meta_list = _find_live_meta_list()

                # 3. Recarrega os cards na lista viva
                load_initial_data(db, live_meta_list, page, current_view)
            else:
                title_field.error_text = "O título não pode ser vazio."
                title_field.update()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            with open("error_save.txt", "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)

    title_field.on_submit = save_goal

    dialog = ft.AlertDialog(
        modal=True,
        shape=ft.RoundedRectangleBorder(radius=16, side=ft.BorderSide(1, "outline")),
        title=ft.Row([
            ft.Icon(ft.Icons.EDIT_OUTLINED, color="primary", size=26),
            ft.Text("Editar Meta", size=22, weight="bold"),
        ], spacing=10),
        content=ft.Column([
            title_field,
            category_dropdown,
        ], spacing=16, tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=_close_dialog),
            ft.FilledButton(
                "Salvar",
                icon=ft.Icons.CHECK,
                on_click=save_goal,
            ),
        ],
        actions_alignment="end",
    )

    # Adiciona ao overlay e abre manualmente (sem usar show_dialog que pode ter side-effects)
    page.overlay.append(dialog)
    dialog.open = True
    page.update()


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


def _build_empty_state():
    """Tela de estado vazio exibida quando não há nenhuma meta cadastrada."""
    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.TRACK_CHANGES_OUTLINED,
                    size=72,
                    color="#555555",
                ),
                ft.Text(
                    "Nenhuma meta definida ainda.",
                    size=20,
                    weight="bold",
                    color="onSurface",
                    text_align="center",
                ),
                ft.Text(
                    "Que tal começar agora? Crie sua primeira meta!",
                    size=14,
                    color="grey",
                    text_align="center",
                ),
            ],
            horizontal_alignment="center",
            alignment="center",
            spacing=12,
        ),
    )


def load_initial_data(db, meta_list, page, current_view):
    with _rebuild_lock:
        meta_list.controls.clear()
        goals_data = db.load_goals()

        # ---- Estado Vazio ----
        if not goals_data:
            meta_list.controls.append(_build_empty_state())
            page.update()
            return

        if current_view[0] == "list":
            view_container = ft.ListView(expand=True, spacing=10, padding=10)
        else:
            view_container = ft.GridView(
                expand=True,
                runs_count=5,
                max_extent=240,
                spacing=12,
                run_spacing=12,
                padding=10
            )

        for g in goals_data:
            # g: (id, title, status, position, cat_id, cat_name, cat_color)
            card = ItemGoal(
                text=g[1],
                remove_func=lambda card: delete_goal_action(page, db, meta_list, card, current_view),
                edit_func=lambda card: edit_goal_action(page, db, meta_list, card, current_view),
                goal_id=g[0],
                db=db,
                page=page,
                status=g[2],
                view_mode=current_view[0],
                category_id=g[4],
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
            # Só limpa o campo após confirmar sucesso no banco
            name_field.value = ""
            name_field.error_text = None
            load_categories_view(page, db, cat_list)
        except Exception:
            # Mantém o valor digitado para o usuário ver o que estava tentando criar
            name_field.error_text = "Categoria já existe."
            name_field.update()
    else:
        name_field.error_text = "Campo obrigatório."
        name_field.update()


def show_delete_category_dialog(page, db, cat_list, cat_id, cat_name):
    def _close_dialog():
        dialog.open = False
        # Remove o dialog do overlay para não acumular referências
        if dialog in page.overlay:
            page.overlay.remove(dialog)
        page.update()

    def confirm_delete(e):
        _close_dialog()
        db.delete_category(cat_id)

        global last_check_hash
        last_check_hash = str(db.load_goals()) + str(db.load_categories())

        load_categories_view(page, db, cat_list)

    def cancel_delete(e):
        _close_dialog()

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


def _find_control_by_key(controls, key):
    """Busca recursiva por um controle com a `key` especificada na árvore de controles."""
    for ctrl in controls:
        if getattr(ctrl, "key", None) == key:
            return ctrl
        # Desce em listas de filhos (controls, content.controls, etc.)
        children = []
        if hasattr(ctrl, "controls") and isinstance(ctrl.controls, list):
            children = ctrl.controls
        elif hasattr(ctrl, "content") and ctrl.content is not None:
            if hasattr(ctrl.content, "controls") and isinstance(ctrl.content.controls, list):
                children = ctrl.content.controls
        if children:
            found = _find_control_by_key(children, key)
            if found:
                return found
    return None


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
                                target_meta_list = _find_control_by_key(view.controls, "meta_list")
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
                                target_task_list = _find_control_by_key(view.controls, "task_list")
                                if target_task_list:
                                    break
                        if target_task_list:
                            load_tasks_view(page, db, target_task_list, goal_id)
                            last_check_hash = current_hash

                # ---- Monitora DASHBOARD (/dashboard): Builder ----
                elif current_route == "/dashboard":
                    goals_data = db.load_goals()
                    cats_data = db.load_categories()
                    current_hash = f"dashboard_{str(goals_data)}_{str(cats_data)}"
                    if current_hash != last_check_hash:
                        builder = getattr(page, '_dashboard_builder', None)
                        if builder is not None:
                            builder.refresh()
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


# ---------------------------------------------------------------------------
# COMPONENTE: Sidebar (Navegação Principal)
# ---------------------------------------------------------------------------
class Sidebar(ft.Container):
    def __init__(self, page: ft.Page, active_route: str, on_theme_toggle):
        super().__init__()
        self._app_page = page  # Evita conflito com a prop somente-leitura 'page' de ft.Container
        self.active_route = active_route
        self.on_theme_toggle = on_theme_toggle
        
        self.width = 240
        self.bgcolor = "surfaceVariant"
        self.padding = ft.Padding(left=15, right=15, top=20, bottom=20)
        
        theme_icon = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.LIGHT_MODE
        theme_label = "Modo Claro" if page.theme_mode == ft.ThemeMode.DARK else "Modo Escuro"

        self.content = ft.Column(
            controls=[
                # Logotipo
                ft.Row([
                    ft.Icon(ft.Icons.TRACK_CHANGES, size=32, color="primary"),
                    ft.Text("Goal\nManager", size=20, weight="bold", color="primary")
                ], alignment="center", spacing=12),
                
                ft.Divider(height=30),
                
                # Links de Navegação
                self._nav_button(ft.Icons.LIST, "Metas", "/"),
                self._nav_button(ft.Icons.CATEGORY, "Categorias", "/categories"),
                self._nav_button(ft.Icons.DASHBOARD, "Dashboard", "/dashboard"),
                
                ft.Container(expand=True),  # Empurra o rodapé para baixo
                ft.Divider(height=20),
                
                # Rodapé (Tema)
                ft.Container(
                    content=ft.Row([
                        ft.Icon(theme_icon, color="onSurfaceVariant", size=20),
                        ft.Text(theme_label, color="onSurfaceVariant", size=14, weight="bold")
                    ], spacing=12),
                    padding=12,
                    border_radius=8,
                    on_click=self.on_theme_toggle,
                    ink=True
                )
            ],
            expand=True
        )

    def _nav_button(self, icon, text, route):
        # Verifica se é a rota ativa
        is_active = False
        if route == "/" and (self.active_route == "/" or self.active_route.startswith("/tasks/")):
            is_active = True
        elif route != "/" and self.active_route == route:
            is_active = True

        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color="primary" if is_active else "onSurfaceVariant", size=22),
                ft.Text(text, weight="bold" if is_active else "normal", 
                        color="primary" if is_active else "onSurfaceVariant", size=15)
            ], spacing=12),
            bgcolor="primaryContainer" if is_active else "transparent",
            border_radius=8,
            padding=12,
            margin=ft.Margin.only(bottom=5),
            on_click=lambda _: self._app_page.go(route),
            ink=True
        )
