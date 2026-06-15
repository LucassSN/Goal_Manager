"""
dashboard_builder.py
====================
Dashboard Builder do Goal Manager — inspirado no Power BI / Grafana.

Componentes principais:
  - WIDGET_CATALOG : dicionário com metadados de todos os widgets disponíveis
  - render_widget()         : renderiza um widget pelo seu tipo
  - DashboardBuilderView    : view principal (modo visualização + modo edição)
  - create_builder_view()   : factory chamada pelo main.py
"""

import uuid
import flet as ft
import flet_charts as fch
from logic import CATEGORY_COLORS


# ─────────────────────────────────────────────────────────────────────────────
# PALETA DE CORES (consistente com o restante do app)
# ─────────────────────────────────────────────────────────────────────────────
_C_DONE    = "#5AD8A6"
_C_PENDING = "#FF7875"
_C_BAR     = "#5B8FF9"
_C_ACCENT  = "#A78BFA"


# ─────────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE WIDGETS
# ─────────────────────────────────────────────────────────────────────────────
WIDGET_CATALOG = {
    # ── KPI Cards ──────────────────────────────────────────────────────────
    "kpi_total_goals": {
        "label":        "Total de Metas",
        "description":  "Número total de metas cadastradas",
        "icon":         ft.Icons.FLAG_OUTLINED,
        "icon_color":   _C_BAR,
        "category":     "KPI Cards",
        "default_span": 1,
    },
    "kpi_completed_goals": {
        "label":        "Metas Concluídas",
        "description":  "Quantidade e % de metas concluídas",
        "icon":         ft.Icons.CHECK_CIRCLE_OUTLINE,
        "icon_color":   _C_DONE,
        "category":     "KPI Cards",
        "default_span": 1,
    },
    "kpi_total_tasks": {
        "label":        "Total de Tarefas",
        "description":  "Número total de tarefas cadastradas",
        "icon":         ft.Icons.CHECKLIST,
        "icon_color":   _C_ACCENT,
        "category":     "KPI Cards",
        "default_span": 1,
    },
    "kpi_completed_tasks": {
        "label":        "Tarefas Concluídas",
        "description":  "Quantidade e % de tarefas concluídas",
        "icon":         ft.Icons.TASK_ALT,
        "icon_color":   _C_DONE,
        "category":     "KPI Cards",
        "default_span": 1,
    },
    "kpi_completion_rate": {
        "label":        "Taxa de Conclusão Global",
        "description":  "Percentual geral de conclusão (metas + tarefas)",
        "icon":         ft.Icons.PERCENT,
        "icon_color":   "#FB923C",
        "category":     "KPI Cards",
        "default_span": 1,
    },
    # ── Gráficos ──────────────────────────────────────────────────────────
    "pie_goals_status": {
        "label":        "Status das Metas (Rosca)",
        "description":  "Concluídas vs Pendentes — gráfico de rosca",
        "icon":         ft.Icons.PIE_CHART_OUTLINE,
        "icon_color":   _C_DONE,
        "category":     "Gráficos",
        "default_span": 1,
    },
    "pie_tasks_status": {
        "label":        "Status das Tarefas (Rosca)",
        "description":  "Concluídas vs Pendentes — gráfico de rosca",
        "icon":         ft.Icons.PIE_CHART_OUTLINE,
        "icon_color":   _C_ACCENT,
        "category":     "Gráficos",
        "default_span": 1,
    },
    "bar_tasks_per_goal": {
        "label":        "Tarefas por Meta (Barras)",
        "description":  "Volume de tarefas em cada meta",
        "icon":         ft.Icons.BAR_CHART,
        "icon_color":   _C_BAR,
        "category":     "Gráficos",
        "default_span": 1,
    },
    "bar_progress_per_category": {
        "label":        "Progresso por Categoria (%)",
        "description":  "Percentual de conclusão por categoria",
        "icon":         ft.Icons.BAR_CHART,
        "icon_color":   "#FB923C",
        "category":     "Gráficos",
        "default_span": 1,
    },
    "bar_goals_per_category": {
        "label":        "Metas por Categoria",
        "description":  "Quantidade de metas agrupadas por categoria",
        "icon":         ft.Icons.STACKED_BAR_CHART,
        "icon_color":   _C_ACCENT,
        "category":     "Gráficos",
        "default_span": 1,
    },
    "gauge_global_progress": {
        "label":        "Progresso Global (Gauge)",
        "description":  "Indicador visual de progresso geral em %",
        "icon":         ft.Icons.SPEED,
        "icon_color":   _C_DONE,
        "category":     "Gráficos",
        "default_span": 1,
    },
    # ── Tabelas ───────────────────────────────────────────────────────────
    "table_goals": {
        "label":        "Tabela de Metas",
        "description":  "Lista de metas com status e categoria",
        "icon":         ft.Icons.TABLE_CHART_OUTLINED,
        "icon_color":   _C_BAR,
        "category":     "Tabelas",
        "default_span": 2,
    },
    "table_tasks": {
        "label":        "Tabela de Tarefas",
        "description":  "Lista de tarefas com meta associada",
        "icon":         ft.Icons.TABLE_ROWS_OUTLINED,
        "icon_color":   _C_ACCENT,
        "category":     "Tabelas",
        "default_span": 2,
    },
    # ── Outros ────────────────────────────────────────────────────────────
    "category_cards": {
        "label":        "Cards de Categoria",
        "description":  "KPI individual por categoria com barra de progresso",
        "icon":         ft.Icons.CATEGORY_OUTLINED,
        "icon_color":   "#FB923C",
        "category":     "Outros",
        "default_span": 2,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────────────────────────────────────
def _progress_bar(progress: float, hex_color: str) -> ft.Row:
    fill_pct = max(0, min(100, int(progress * 100)))
    rest_pct = 100 - fill_pct
    children = []
    if fill_pct:
        children.append(ft.Container(height=6, bgcolor=hex_color, border_radius=4, expand=fill_pct))
    if rest_pct:
        children.append(ft.Container(height=6, bgcolor="surfaceVariant", border_radius=4, expand=rest_pct))
    if not children:
        children = [ft.Container(height=6, bgcolor="surfaceVariant", border_radius=4, expand=1)]
    return ft.Row(children, spacing=2, expand=True)


def _bar_chart(groups, labels_bottom, labels_left, max_y) -> fch.BarChart:
    return fch.BarChart(
        groups=groups,
        border=ft.Border.all(1, "outline"),
        left_axis=fch.ChartAxis(labels=labels_left),
        bottom_axis=fch.ChartAxis(labels=labels_bottom),
        max_y=max_y,
        expand=True,
    )


def _widget_card(title: str, content: ft.Control, height: int = 220) -> ft.Card:
    return ft.Card(
        elevation=3,
        content=ft.Container(
            padding=16,
            content=ft.Column([
                ft.Text(title, size=14, weight="bold", color="onSurface"),
                ft.Divider(height=8),
                ft.Container(content=content, height=height,
                             alignment=ft.Alignment(0, 0)),
            ], spacing=4),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# RENDERERS — um por tipo de widget
# ─────────────────────────────────────────────────────────────────────────────
def _render_kpi(label: str, value: str, sub: str, icon, icon_color: str) -> ft.Card:
    return ft.Card(
        elevation=3,
        expand=True,
        content=ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
            content=ft.Column([
                ft.Text(label, size=12, color="grey"),
                ft.Row([
                    ft.Column([
                        ft.Text(value, size=28, weight="bold"),
                        ft.Text(sub, size=11, color="grey"),
                    ], spacing=2, expand=True),
                    ft.Icon(icon, color=icon_color, size=34),
                ], alignment="spaceBetween", vertical_alignment="center"),
            ], spacing=8),
        ),
    )


def _render_pie(title: str, done: int, pending: int, c_done: str, c_pending: str) -> ft.Card:
    if done == 0 and pending == 0:
        content = ft.Text("Sem dados", italic=True, color="grey")
    else:
        sections = []
        if done > 0:
            sections.append(fch.PieChartSection(value=done, color=c_done, radius=44, title=""))
        if pending > 0:
            sections.append(fch.PieChartSection(value=pending, color=c_pending, radius=44, title=""))
        content = fch.PieChart(sections=sections, sections_space=2, center_space_radius=50, expand=True)

    return _widget_card(title, ft.Column([
        ft.Container(content=content, height=150, alignment=ft.Alignment(0, 0)),
        ft.Row([
            ft.Container(width=10, height=10, border_radius=5, bgcolor=c_done),
            ft.Text("Concluídas", size=11, color="grey"),
            ft.Container(width=10, height=10, border_radius=5, bgcolor=c_pending),
            ft.Text("Pendentes", size=11, color="grey"),
        ], spacing=6),
    ], spacing=6, horizontal_alignment="center"), height=200)


def _render_bar_generic(title: str, items: list, color: str) -> ft.Card:
    """items: lista de (label, value)"""
    if not items:
        return _widget_card(title, ft.Text("Sem dados", italic=True, color="grey"), height=180)

    max_y = max((v for _, v in items), default=0) + 1
    groups = [
        fch.BarChartGroup(x=i, rods=[fch.BarChartRod(
            from_y=0, to_y=v, color=color, width=20,
            tooltip=f"{lbl}: {v:.0f}", border_radius=4
        )])
        for i, (lbl, v) in enumerate(items)
    ]
    labels_b = [
        fch.ChartAxisLabel(
            value=i,
            label=ft.Text((lbl[:8] + "…") if len(lbl) > 8 else lbl, size=9)
        )
        for i, (lbl, _) in enumerate(items)
    ]
    labels_l = [
        fch.ChartAxisLabel(value=i, label=ft.Text(str(i), size=9))
        for i in range(int(max_y) + 1)
    ]
    chart = _bar_chart(groups, labels_b, labels_l, max_y)
    return _widget_card(title, chart, height=180)


def _render_gauge(title: str, pct: float) -> ft.Card:
    """Gauge simulado com PieChart semicircular."""
    pct = max(0.0, min(100.0, pct))
    sections = [
        fch.PieChartSection(value=pct,        color=_C_DONE,    radius=28, title=""),
        fch.PieChartSection(value=100 - pct,  color="surfaceVariant", radius=28, title=""),
    ]
    pie = fch.PieChart(
        sections=sections,
        sections_space=2,
        center_space_radius=40,
        start_degree_offset=180,
        expand=True,
    )
    content = ft.Stack([
        ft.Container(content=pie, height=120, alignment=ft.Alignment(0, 0)),
        ft.Container(
            content=ft.Text(f"{pct:.0f}%", size=20, weight="bold"),
            alignment=ft.Alignment(0, 0.6),
        ),
    ])
    return _widget_card(title, content, height=140)


def _render_table_goals(db, filters: dict) -> ft.Card:
    cat_id  = filters.get("category_id")
    goals   = db.load_goals()
    if cat_id:
        goals = [g for g in goals if g[4] == cat_id]

    rows = []
    for g in goals:
        status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=_C_DONE, size=16) if g[2] == 1 \
                      else ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=_C_PENDING, size=16)
        cat_name = g[5] or "—"
        rows.append(ft.DataRow(cells=[
            ft.DataCell(status_icon),
            ft.DataCell(ft.Text(g[1], size=13)),
            ft.DataCell(ft.Text(cat_name, size=12, color="grey")),
        ]))

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("", width=30)),
            ft.DataColumn(ft.Text("Meta")),
            ft.DataColumn(ft.Text("Categoria")),
        ],
        rows=rows,
        column_spacing=16,
        heading_row_height=36,
        data_row_max_height=36,
    )

    content = ft.Column([
        ft.Container(
            content=ft.Column([table], scroll="auto"),
            height=200,
        )
    ], spacing=0)

    return _widget_card("Tabela de Metas", content, height=220)


def _render_table_tasks(db, filters: dict) -> ft.Card:
    cat_id  = filters.get("category_id")
    goals   = db.load_goals()
    if cat_id:
        goals = [g for g in goals if g[4] == cat_id]

    rows = []
    for g in goals:
        tasks = db.load_tasks(g[0])
        for t in tasks:
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=_C_DONE, size=16) if t[3] == 1 \
                          else ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=_C_PENDING, size=16)
            rows.append(ft.DataRow(cells=[
                ft.DataCell(status_icon),
                ft.DataCell(ft.Text(t[2], size=13)),
                ft.DataCell(ft.Text(g[1], size=12, color="grey")),
            ]))

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("", width=30)),
            ft.DataColumn(ft.Text("Tarefa")),
            ft.DataColumn(ft.Text("Meta")),
        ],
        rows=rows,
        column_spacing=16,
        heading_row_height=36,
        data_row_max_height=36,
    )

    content = ft.Column([
        ft.Container(
            content=ft.Column([table], scroll="auto"),
            height=200,
        )
    ], spacing=0)

    return _widget_card("Tabela de Tarefas", content, height=220)


def _render_category_cards(db, filters: dict) -> ft.Control:
    cats = db.get_kpi_per_category()
    if not cats:
        return ft.Text("Nenhuma categoria criada.", italic=True, color="grey")

    cat_id_filter = filters.get("category_id")
    cards = []
    for cat in cats:
        cid, cname, ccolor, total, completed = cat
        if cat_id_filter and cid != cat_id_filter:
            continue
        completed  = int(completed or 0)
        total      = int(total or 0)
        pending    = total - completed
        progress   = (completed / total) if total > 0 else 0.0
        hex_color  = CATEGORY_COLORS.get(ccolor, "#1E88E5")

        card = ft.Card(
            elevation=2,
            content=ft.Container(
                width=200,
                padding=12,
                content=ft.Column([
                    ft.Row([
                        ft.Container(width=12, height=12, border_radius=6, bgcolor=hex_color),
                        ft.Text(cname, size=13, weight="bold", expand=True),
                    ], spacing=8),
                    ft.Divider(height=4),
                    ft.Row([
                        ft.Column([ft.Text(str(total),     size=18, weight="bold"),
                                   ft.Text("Total",        size=10, color="grey")],
                                  horizontal_alignment="center", spacing=1),
                        ft.Column([ft.Text(str(completed), size=18, weight="bold", color=_C_DONE),
                                   ft.Text("Concluídas",   size=10, color="grey")],
                                  horizontal_alignment="center", spacing=1),
                        ft.Column([ft.Text(str(pending),   size=18, weight="bold", color=_C_PENDING),
                                   ft.Text("Pendentes",    size=10, color="grey")],
                                  horizontal_alignment="center", spacing=1),
                    ], alignment="spaceAround"),
                    ft.Divider(height=4),
                    _progress_bar(progress, hex_color),
                    ft.Text(f"{int(progress * 100)}% concluído", size=10, color="grey",
                            text_align="right"),
                ], spacing=4),
            ),
        )
        cards.append(card)

    return ft.Card(
        elevation=3,
        content=ft.Container(
            padding=16,
            content=ft.Column([
                ft.Text("Cards de Categoria", size=14, weight="bold"),
                ft.Divider(height=8),
                ft.Row(cards, wrap=True, spacing=10, run_spacing=10),
            ], spacing=4),
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# RENDER_WIDGET — dispatcher central
# ─────────────────────────────────────────────────────────────────────────────
def render_widget(widget_cfg: dict, db, filters: dict) -> ft.Control:
    """Recebe a config de um widget e retorna o controle Flet renderizado."""
    wtype   = widget_cfg.get("type", "")
    cat_id  = filters.get("category_id")
    st_raw  = filters.get("status", "all")
    st_filt = None if st_raw == "all" else int(st_raw)

    # ── KPI Cards ──────────────────────────────────────────────────────────
    if wtype == "kpi_total_goals":
        kpi = db.get_goals_kpi(category_id=cat_id, status_filter=st_filt)
        return _render_kpi(
            "Total de Metas", str(kpi["total"]),
            f"{kpi['concluidas']} concluídas · {kpi['pendentes']} pendentes",
            ft.Icons.FLAG_OUTLINED, _C_BAR
        )

    if wtype == "kpi_completed_goals":
        kpi = db.get_goals_kpi(category_id=cat_id, status_filter=st_filt)
        pct = int(kpi["concluidas"] / kpi["total"] * 100) if kpi["total"] else 0
        return _render_kpi(
            "Metas Concluídas", str(kpi["concluidas"]),
            f"{pct}% do total ({kpi['total']})",
            ft.Icons.CHECK_CIRCLE_OUTLINE, _C_DONE
        )

    if wtype == "kpi_total_tasks":
        kpi = db.get_tasks_kpi(category_id=cat_id, status_filter=st_filt)
        return _render_kpi(
            "Total de Tarefas", str(kpi["total"]),
            f"{kpi['concluidas']} concluídas · {kpi['pendentes']} pendentes",
            ft.Icons.CHECKLIST, _C_ACCENT
        )

    if wtype == "kpi_completed_tasks":
        kpi = db.get_tasks_kpi(category_id=cat_id, status_filter=st_filt)
        pct = int(kpi["concluidas"] / kpi["total"] * 100) if kpi["total"] else 0
        return _render_kpi(
            "Tarefas Concluídas", str(kpi["concluidas"]),
            f"{pct}% do total ({kpi['total']})",
            ft.Icons.TASK_ALT, _C_DONE
        )

    if wtype == "kpi_completion_rate":
        g = db.get_goals_kpi(category_id=cat_id, status_filter=st_filt)
        t = db.get_tasks_kpi(category_id=cat_id, status_filter=st_filt)
        total    = g["total"] + t["total"]
        done     = g["concluidas"] + t["concluidas"]
        pct      = int(done / total * 100) if total else 0
        return _render_kpi(
            "Taxa de Conclusão Global", f"{pct}%",
            f"{done} de {total} itens concluídos",
            ft.Icons.PERCENT, "#FB923C"
        )

    # ── Gráficos de Rosca ──────────────────────────────────────────────────
    if wtype == "pie_goals_status":
        kpi = db.get_goals_kpi(category_id=cat_id, status_filter=st_filt)
        return _render_pie(
            "Status das Metas",
            kpi["concluidas"], kpi["pendentes"],
            _C_DONE, _C_PENDING
        )

    if wtype == "pie_tasks_status":
        kpi = db.get_tasks_kpi(category_id=cat_id, status_filter=st_filt)
        return _render_pie(
            "Status das Tarefas",
            kpi["concluidas"], kpi["pendentes"],
            _C_DONE, _C_ACCENT
        )

    # ── Gráficos de Barras ─────────────────────────────────────────────────
    if wtype == "bar_tasks_per_goal":
        rows = db.get_tasks_per_goal(category_id=cat_id)
        return _render_bar_generic(
            "Tarefas por Meta",
            [(r[0], r[1]) for r in rows],
            _C_BAR
        )

    if wtype == "bar_progress_per_category":
        rows = db.get_progress_per_category()
        return _render_bar_generic(
            "Progresso por Categoria (%)",
            [(r[0], r[2]) for r in rows],
            "#FB923C"
        )

    if wtype == "bar_goals_per_category":
        cats = db.get_kpi_per_category()
        return _render_bar_generic(
            "Metas por Categoria",
            [(c[1], int(c[3] or 0)) for c in cats],
            _C_ACCENT
        )

    # ── Gauge ──────────────────────────────────────────────────────────────
    if wtype == "gauge_global_progress":
        g = db.get_goals_kpi(category_id=cat_id, status_filter=st_filt)
        t = db.get_tasks_kpi(category_id=cat_id, status_filter=st_filt)
        total = g["total"] + t["total"]
        done  = g["concluidas"] + t["concluidas"]
        pct   = (done / total * 100) if total else 0.0
        return _render_gauge("Progresso Global", pct)

    # ── Tabelas ────────────────────────────────────────────────────────────
    if wtype == "table_goals":
        return _render_table_goals(db, filters)

    if wtype == "table_tasks":
        return _render_table_tasks(db, filters)

    # ── Categoria Cards ────────────────────────────────────────────────────
    if wtype == "category_cards":
        return _render_category_cards(db, filters)

    # Fallback — tipo desconhecido
    return ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Text(f"Widget desconhecido: {wtype}", color="error"),
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD BUILDER VIEW
# ─────────────────────────────────────────────────────────────────────────────
class DashboardBuilderView:
    """
    Controller da view do Dashboard Builder.
    Gerencia o estado de modo (visualização/edição), lista de widgets,
    filtros globais e persistência.
    """

    def __init__(self, page: ft.Page, db, on_dashboard_change=None):
        self.page = page
        self.db   = db
        self.on_dashboard_change = on_dashboard_change

        # Estado
        self._edit_mode      = False
        self._dashboard_id   = db.get_default_dashboard_id()
        self._widgets: list  = []   # lista de dicts: {uid, type, span}
        self._filters: dict  = {"category_id": None, "status": "all"}
        self._drag_index     = None  # índice do widget sendo arrastado

        # Referências para controles stateful
        self._grid_col       = ft.Column(scroll="auto", spacing=8, expand=True)
        self._filter_cat_dd  = None
        self._filter_stat_dd = None
        self._dash_dd        = None
        self._edit_btn       = None

        self._load_dashboard()

    # ── Carregamento ──────────────────────────────────────────────────────
    def _load_dashboard(self):
        data = self.db.load_dashboard_layout(self._dashboard_id)
        self._widgets = data.get("widgets", [])
        self._filters = data.get("filters", {"category_id": None, "status": "all"})
        # Garante UIDs únicos
        for w in self._widgets:
            if "uid" not in w:
                w["uid"] = str(uuid.uuid4())

    def _save_layout(self):
        self.db.save_dashboard_layout(self._dashboard_id, self._widgets, self._filters)

    def refresh(self):
        """Recarrega dados do banco e reconstrói o grid preservando o estado de edição."""
        self._load_dashboard()
        self._rebuild_grid()

    # ── Modo Edição ───────────────────────────────────────────────────────
    def toggle_edit_mode(self, e=None):
        self._edit_mode = not self._edit_mode
        if self._edit_btn:
            self._edit_btn.icon  = ft.Icons.VISIBILITY if self._edit_mode else ft.Icons.EDIT
            self._edit_btn.text  = "Visualizar" if self._edit_mode else "Editar Layout"
            self._edit_btn.style = ft.ButtonStyle(
                bgcolor={"": "primary" if self._edit_mode else None},
                color={"": "onPrimary" if self._edit_mode else None}
            )
            self._edit_btn.update()
        self._rebuild_grid()

    # ── Ações de Widget ───────────────────────────────────────────────────
    def _move_widget(self, uid: str, direction: int):
        idx = next((i for i, w in enumerate(self._widgets) if w["uid"] == uid), None)
        if idx is None:
            return
        new_idx = idx + direction
        if 0 <= new_idx < len(self._widgets):
            self._widgets.insert(new_idx, self._widgets.pop(idx))
            self._save_layout()
            self._rebuild_grid()

    def _remove_widget(self, uid: str):
        self._widgets = [w for w in self._widgets if w["uid"] != uid]
        self._save_layout()
        self._rebuild_grid()

    def _toggle_span(self, uid: str):
        for w in self._widgets:
            if w["uid"] == uid:
                w["span"] = 2 if w.get("span", 1) == 1 else 1
                break
        self._save_layout()
        self._rebuild_grid()

    def _on_drag_start(self, uid: str):
        self._drag_index = next(
            (i for i, w in enumerate(self._widgets) if w["uid"] == uid), None
        )

    def _on_drop(self, uid_target: str, e):
        if self._drag_index is None:
            return
        target_idx = next(
            (i for i, w in enumerate(self._widgets) if w["uid"] == uid_target), None
        )
        if target_idx is None or target_idx == self._drag_index:
            self._drag_index = None
            return
        widget = self._widgets.pop(self._drag_index)
        self._widgets.insert(target_idx, widget)
        self._drag_index = None
        self._save_layout()
        self._rebuild_grid()

    # ── Grid Builder ──────────────────────────────────────────────────────
    def _build_widget_slot(self, widget_cfg: dict, idx: int) -> ft.Control:
        """Envolve um widget renderizado com os controles de edição (se em modo edição)."""
        uid = widget_cfg["uid"]
        try:
            inner = render_widget(widget_cfg, self.db, self._filters)
        except Exception as ex:
            inner = ft.Card(content=ft.Container(
                padding=12,
                content=ft.Text(f"Erro: {ex}", color="error", size=12),
            ))

        if not self._edit_mode:
            return ft.Container(content=inner, expand=True)

        # Barra de controles de edição
        edit_bar = ft.Container(
            bgcolor="#1A1A2E",
            border_radius=ft.BorderRadius(top_left=8, top_right=8, bottom_left=0, bottom_right=0),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            content=ft.Row([
                ft.Icon(ft.Icons.DRAG_INDICATOR, color="grey", size=16),
                ft.Text(
                    WIDGET_CATALOG.get(widget_cfg["type"], {}).get("label", widget_cfg["type"]),
                    size=11, color="grey", expand=True
                ),
                ft.IconButton(
                    icon=ft.Icons.WIDTH_WIDE if widget_cfg.get("span", 1) == 2
                         else ft.Icons.WIDTH_NORMAL,
                    icon_size=16,
                    on_click=lambda _, u=uid: self._toggle_span(u),
                    icon_color="grey",
                    padding=4,
                    tooltip="Alternar Largura",
                ),
                ft.IconButton(
                    ft.Icons.ARROW_UPWARD, icon_size=16,
                    on_click=lambda _, u=uid: self._move_widget(u, -1),
                    icon_color="grey", padding=4,
                    tooltip="Mover para cima",
                ),
                ft.IconButton(
                    ft.Icons.ARROW_DOWNWARD, icon_size=16,
                    on_click=lambda _, u=uid: self._move_widget(u, 1),
                    icon_color="grey", padding=4,
                    tooltip="Mover para baixo",
                ),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, icon_size=16,
                    on_click=lambda _, u=uid: self._remove_widget(u),
                    icon_color="error", padding=4,
                    tooltip="Remover widget",
                ),
            ], spacing=0),
        )

        # Conteúdo do slot com borda de edição
        slot_content = ft.Container(
            border=ft.Border.all(1, "#5B8FF955"),
            border_radius=8,
            content=ft.Column([edit_bar, inner], spacing=0),
            expand=True,
        )

        # Drag & Drop para reordenar
        draggable = ft.Draggable(
            group="dash_widgets",
            content=slot_content,
            data=uid,
            on_drag_start=lambda _, u=uid: self._on_drag_start(u),
        )
        drop_target = ft.DragTarget(
            group="dash_widgets",
            content=draggable,
            data=uid,
            on_accept=lambda e, u=uid: self._on_drop(u, e),
        )
        return ft.Container(content=drop_target, expand=True)

    def _rebuild_grid(self):
        """Reconstrói o grid de widgets no Column."""
        self.page.run_task(self._async_rebuild_grid)

    async def _async_rebuild_grid(self):
        self._grid_col.controls.clear()

        if not self._widgets:
            self._grid_col.controls.append(
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column([
                        ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE_OUTLINED, size=64, color="grey"),
                        ft.Text("Dashboard vazio", size=18, weight="bold", color="onSurface"),
                        ft.Text(
                            "Clique em 'Editar Layout' e depois em '+ Adicionar Widget'",
                            size=13, color="grey", text_align="center",
                        ),
                    ], horizontal_alignment="center", alignment="center", spacing=12),
                    padding=40,
                )
            )
        else:
            # Agrupa widgets em linhas de 2 colunas, respeitando span
            i = 0
            while i < len(self._widgets):
                w = self._widgets[i]
                span = w.get("span", 1)

                if span == 2:
                    slot = self._build_widget_slot(w, i)
                    self._grid_col.controls.append(
                        ft.Row([slot], spacing=12)
                    )
                    i += 1
                else:
                    # Tenta pegar dois widgets de span=1 na mesma linha
                    slot1 = self._build_widget_slot(w, i)
                    if i + 1 < len(self._widgets) and self._widgets[i + 1].get("span", 1) == 1:
                        slot2 = self._build_widget_slot(self._widgets[i + 1], i + 1)
                        self._grid_col.controls.append(
                            ft.Row([slot1, slot2], spacing=12, expand=True)
                        )
                        i += 2
                    else:
                        # Widget sozinho na linha
                        self._grid_col.controls.append(
                            ft.Row([slot1], spacing=12, expand=True)
                        )
                        i += 1

        # Botão de adicionar (sempre visível no modo edição)
        if self._edit_mode:
            self._grid_col.controls.append(
                ft.Container(
                    content=ft.ElevatedButton(
                        "+ Adicionar Widget",
                        icon=ft.Icons.ADD,
                        on_click=self._open_catalog_modal,
                        style=ft.ButtonStyle(
                            bgcolor={"": "primary"},
                            color={"": "onPrimary"},
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    ),
                    padding=ft.Padding.symmetric(vertical=16),
                    alignment=ft.Alignment(0, 0),
                )
            )

        try:
            self.page.update()
        except Exception:
            pass

    # ── Modal do Catálogo de Widgets ──────────────────────────────────────
    def _open_catalog_modal(self, e=None):
        existing_types = {w["type"] for w in self._widgets}
        items = []
        current_cat = [None]

        for wtype, meta in WIDGET_CATALOG.items():
            already_added = wtype in existing_types

            def _add(_, t=wtype, m=meta):
                self._widgets.append({
                    "uid":  str(uuid.uuid4()),
                    "type": t,
                    "span": m["default_span"],
                })
                self._save_layout()
                self.page.pop_dialog()
                self._rebuild_grid()

            cat = meta["category"]
            if cat != current_cat[0]:
                current_cat[0] = cat
                items.append(ft.Container(
                    content=ft.Text(cat.upper(), size=10, weight="bold", color="grey"),
                    padding=ft.Padding.only(top=12, bottom=4),
                ))

            items.append(ft.Container(
                bgcolor="surfaceVariant" if already_added else None,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                content=ft.Row([
                    ft.Icon(meta["icon"], color=meta["icon_color"], size=22),
                    ft.Column([
                        ft.Text(meta["label"], size=13, weight="bold"),
                        ft.Text(meta["description"], size=11, color="grey"),
                    ], spacing=1, expand=True),
                    ft.FilledButton(
                        "Adicionar" if not already_added else "Já adicionado",
                        icon=ft.Icons.ADD if not already_added else ft.Icons.CHECK,
                        disabled=already_added,
                        on_click=_add if not already_added else None,
                        style=ft.ButtonStyle(
                            bgcolor={"": "primary" if not already_added else "surfaceVariant"},
                        ),
                    ),
                ], spacing=12, alignment="start", vertical_alignment="center"),
            ))

        dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row([
                ft.Icon(ft.Icons.WIDGETS_OUTLINED, color="primary"),
                ft.Text("Catálogo de Widgets", size=20, weight="bold"),
            ], spacing=10),
            content=ft.Container(
                width=480,
                height=420,
                content=ft.Column(items, scroll="auto", spacing=4),
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda _: self.page.pop_dialog()),
            ],
            actions_alignment="end",
        )
        self.page.show_dialog(dialog)

    # ── Modal de Novo Dashboard ───────────────────────────────────────────
    def _open_new_dashboard_modal(self, e=None):
        field = ft.TextField(
            label="Nome do Dashboard",
            autofocus=True,
            width=340,
            border_radius=10,
        )

        def _create(e=None):
            name = field.value.strip() if field.value else ""
            if not name:
                field.error_text = "Nome obrigatório"
                field.update()
                return
            new_id = self.db.create_dashboard(name)
            self._switch_dashboard(new_id)
            self.page.pop_dialog()
            self._refresh_dash_selector()

        field.on_submit = _create

        dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row([
                ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE_OUTLINED, color="primary"),
                ft.Text("Novo Dashboard", size=20, weight="bold"),
            ], spacing=10),
            content=ft.Column([field], tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton("Criar", icon=ft.Icons.ADD, on_click=_create),
            ],
            actions_alignment="end",
        )
        self.page.show_dialog(dialog)

    def _delete_current_dashboard(self, e=None):
        dashes = self.db.list_dashboards()
        if len(dashes) <= 1:
            return  # nunca deleta o último

        success = self.db.delete_dashboard(self._dashboard_id)
        if not success:
            return  # era o padrão

        # Volta para o padrão
        self._dashboard_id = self.db.get_default_dashboard_id()
        self._edit_mode = False
        self._load_dashboard()
        self._refresh_dash_selector()
        self._rebuild_grid()

    def _switch_dashboard(self, dashboard_id: int):
        self._dashboard_id = dashboard_id
        self._edit_mode = False
        self._load_dashboard()
        if self._edit_btn:
            self._edit_btn.icon = ft.Icons.EDIT
            self._edit_btn.text = "Editar Layout"
        self._rebuild_grid()
        if self.on_dashboard_change:
            self.on_dashboard_change(dashboard_id)

    def _refresh_dash_selector(self):
        """Atualiza o Dropdown de dashboards."""
        if not self._dash_dd:
            return
        dashes = self.db.list_dashboards()
        self._dash_dd.options = [
            ft.dropdown.Option(key=str(d[0]), text=d[1])
            for d in dashes
        ]
        self._dash_dd.value = str(self._dashboard_id)
        self._dash_dd.update()

    # ── Filtros ───────────────────────────────────────────────────────────
    def _apply_filters(self, e=None):
        cat_val = self._filter_cat_dd.value if self._filter_cat_dd else None
        self._filters["category_id"] = int(cat_val) if cat_val and cat_val != "all" else None
        self._filters["status"]       = self._filter_stat_dd.value if self._filter_stat_dd else "all"
        self._save_layout()
        self._rebuild_grid()

    # ── Construção da View Completa ───────────────────────────────────────
    def build(self) -> ft.Container:
        """Retorna o Container raiz da view do Dashboard Builder."""
        dashes     = self.db.list_dashboards()
        categories = self.db.load_categories()

        # ── Selector de Dashboard ──────────────────────────────────────────
        self._dash_dd = ft.Dropdown(
            value=str(self._dashboard_id),
            options=[ft.dropdown.Option(key=str(d[0]), text=d[1]) for d in dashes],
            border_radius=10,
            width=200,
            on_select=lambda e: self._switch_dashboard(int(e.control.value)),
        )

        # ── Botão Editar Layout ────────────────────────────────────────────
        # Reflete o estado atual de _edit_mode (preserva entre reconstruções)
        self._edit_btn = ft.ElevatedButton(
            "Visualizar" if self._edit_mode else "Editar Layout",
            icon=ft.Icons.VISIBILITY if self._edit_mode else ft.Icons.EDIT,
            on_click=self.toggle_edit_mode,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor={"":  "primary" if self._edit_mode else None},
                color={"":  "onPrimary" if self._edit_mode else None},
            ),
        )

        # ── Barra de ações do dashboard ────────────────────────────────────
        dash_bar = ft.Row([
            ft.Icon(ft.Icons.DASHBOARD_OUTLINED, color="primary", size=22),
            ft.Text("Dashboards:", size=13, color="grey"),
            self._dash_dd,
            ft.IconButton(
                ft.Icons.ADD_CIRCLE_OUTLINE,
                icon_color="primary",
                on_click=self._open_new_dashboard_modal,
                tooltip="Novo Dashboard",
            ),
            ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_color="error",
                on_click=self._delete_current_dashboard,
                tooltip="Excluir Dashboard Atual",
            ),
            ft.VerticalDivider(width=16),
            self._edit_btn,
        ], spacing=8, vertical_alignment="center")

        # ── Filtros Globais ────────────────────────────────────────────────
        cat_options = [ft.dropdown.Option(key="all", text="Todas as categorias")]
        for cat in categories:
            cat_options.append(ft.dropdown.Option(key=str(cat[0]), text=cat[1]))

        current_cat = self._filters.get("category_id")
        self._filter_cat_dd = ft.Dropdown(
            label="Categoria",
            options=cat_options,
            value=str(current_cat) if current_cat else "all",
            border_radius=10,
            width=180,
            on_select=self._apply_filters,
        )

        self._filter_stat_dd = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option(key="all",  text="Todos"),
                ft.dropdown.Option(key="1",    text="✅ Concluídos"),
                ft.dropdown.Option(key="0",    text="⏳ Pendentes"),
            ],
            value=self._filters.get("status", "all"),
            border_radius=10,
            width=160,
            on_select=self._apply_filters,
        )

        filter_bar = ft.Row([
            ft.Icon(ft.Icons.FILTER_LIST, color="grey", size=18),
            ft.Text("Filtros:", size=13, color="grey"),
            self._filter_cat_dd,
            self._filter_stat_dd,
        ], spacing=10, vertical_alignment="center")

        # ── Monta o grid inicial ───────────────────────────────────────────
        self._rebuild_grid()

        return ft.Container(
            content=ft.Column([
                dash_bar,
                ft.Divider(height=6),
                filter_bar,
                ft.Divider(height=8),
                ft.Container(
                    content=self._grid_col,
                    expand=True,
                ),
            ], spacing=8, expand=True),
            padding=20,
            expand=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# FACTORY — chamada pelo main.py
# ─────────────────────────────────────────────────────────────────────────────
def create_builder_view(page: ft.Page, db, builder: DashboardBuilderView = None) -> tuple:
    """Cria (ou reutiliza) o DashboardBuilderView e retorna (builder, container).
    
    Quando `builder` é fornecido, reutiliza a instância existente (preservando
    o estado de edição) e apenas reconstrói a árvore de controles.
    """
    if builder is None:
        builder = DashboardBuilderView(page, db)
    else:
        # Recarrega dados do banco sem resetar _edit_mode
        builder._load_dashboard()
    return builder, builder.build()
