import flet as ft
import flet_charts as fch
from logic import CATEGORY_COLORS


def build_dashboard_content(column: ft.Column, page: ft.Page, db):
    """Reconstrói o conteúdo do dashboard no Column recebido. Chamado na carga e pelo monitor."""
    column.controls.clear()

    goals_kpi       = db.get_goals_kpi()
    tasks_kpi       = db.get_tasks_kpi()
    tasks_per_goal  = db.get_tasks_per_goal()
    categories_kpi  = db.get_kpi_per_category()

    print(f"[DASH] goals_kpi={goals_kpi} | tasks_kpi={tasks_kpi} | categories={categories_kpi}")

    # -------------------------------------------------------------------------
    # 1. Título
    # -------------------------------------------------------------------------
    title = ft.Text("Dashboard Analítico", size=26, weight="bold")

    # -------------------------------------------------------------------------
    # 2. KPI Cards globais (Metas + Tarefas)
    # -------------------------------------------------------------------------
    def kpi_card(label, value_text, icon, icon_color):
        return ft.Card(
            elevation=4,
            expand=True,
            content=ft.Container(
                padding=ft.Padding.symmetric(horizontal=20, vertical=14),
                content=ft.Column([
                    ft.Text(label, size=13, color="grey"),
                    ft.Row([
                        ft.Text(value_text, size=26, weight="bold"),
                        ft.Icon(icon, color=icon_color, size=28),
                    ], alignment="spaceBetween"),
                ], spacing=6),
            ),
        )

    kpis_row = ft.Row([
        kpi_card("Progresso das Metas",
                 f"{goals_kpi['concluidas']} / {goals_kpi['total']}",
                 ft.Icons.FLAG, "blue"),
        kpi_card("Progresso das Tarefas",
                 f"{tasks_kpi['concluidas']} / {tasks_kpi['total']}",
                 ft.Icons.CHECKLIST, "green"),
    ], spacing=16)

    # -------------------------------------------------------------------------
    # 3. Gráfico de Rosca — Status das Metas
    # -------------------------------------------------------------------------
    if goals_kpi["total"] > 0:
        pie_sections = []
        if goals_kpi["concluidas"] > 0:
            pie_sections.append(fch.PieChartSection(
                value=goals_kpi["concluidas"], color="green", radius=40, title=""))
        if goals_kpi["pendentes"] > 0:
            pie_sections.append(fch.PieChartSection(
                value=goals_kpi["pendentes"], color="red", radius=40, title=""))

        pie_content = fch.PieChart(
            sections=pie_sections,
            sections_space=2,
            center_space_radius=45,
            expand=True,
        )
    else:
        pie_content = ft.Text("Nenhuma meta cadastrada.", italic=True, color="grey")

    pie_card = ft.Card(
        elevation=4,
        content=ft.Container(
            width=260,
            padding=16,
            content=ft.Column([
                ft.Text("Status das Metas", weight="bold", size=15),
                ft.Container(content=pie_content, height=180,
                             alignment=ft.Alignment(0, 0)),
                ft.Row([
                    ft.Container(width=12, height=12, border_radius=6, bgcolor="green"),
                    ft.Text("Concluídas", size=11, color="grey"),
                    ft.Container(width=12, height=12, border_radius=6, bgcolor="red"),
                    ft.Text("Pendentes", size=11, color="grey"),
                ], spacing=6),
            ], spacing=8, horizontal_alignment="center"),
        ),
    )

    # -------------------------------------------------------------------------
    # 4. Gráfico de Barras — Volume de Tarefas por Meta
    # -------------------------------------------------------------------------
    bar_groups    = []
    max_y         = 0
    labels_bottom = []

    for index, item in enumerate(tasks_per_goal):
        title_txt = item[0]
        count     = item[1]
        if count > max_y:
            max_y = count
        bar_groups.append(
            fch.BarChartGroup(
                x=index,
                rods=[fch.BarChartRod(
                    from_y=0, to_y=count, color="blue",
                    width=22, tooltip=f"{title_txt}: {count} tarefas", border_radius=4
                )],
            )
        )
        short = title_txt[:10] + "…" if len(title_txt) > 10 else title_txt
        labels_bottom.append(fch.ChartAxisLabel(value=index, label=ft.Text(short, size=10)))

    limite_y  = max_y + 1 if max_y > 0 else 5
    labels_left = [
        fch.ChartAxisLabel(value=i, label=ft.Text(str(i), size=10))
        for i in range(limite_y + 1)
    ]

    if bar_groups:
        bar_content = fch.BarChart(
            groups=bar_groups,
            border=ft.Border.all(1, "outline"),
            left_axis=fch.ChartAxis(labels=labels_left),
            bottom_axis=fch.ChartAxis(labels=labels_bottom),
            max_y=limite_y,
            expand=True,
        )
    else:
        bar_content = ft.Text("Nenhuma tarefa vinculada.", italic=True, color="grey")

    bar_card = ft.Card(
        elevation=4,
        expand=True,
        content=ft.Container(
            padding=16,
            content=ft.Column([
                ft.Text("Volume de Tarefas por Meta", weight="bold", size=15),
                ft.Container(content=bar_content, height=180,
                             alignment=ft.Alignment(0, 0)),
            ], spacing=8, horizontal_alignment="center"),
        ),
    )

    charts_row = ft.Row(
        [pie_card, bar_card],
        alignment="start",
        vertical_alignment="start",
        spacing=16,
    )

    # -------------------------------------------------------------------------
    # 5. Seção de KPIs por Categoria
    # -------------------------------------------------------------------------
    cat_section_title = ft.Text("Desempenho por Categoria", size=20, weight="bold")

    def _progress_bar(progress: float, hex_color: str):
        """Barra de progresso responsiva: usa expand proporcional em vez de pixels fixos,
        garantindo que nunca ultrapasse a largura do card pai."""
        fill_pct = int(progress * 100)
        rest_pct = 100 - fill_pct

        children = []
        if fill_pct > 0:
            children.append(
                ft.Container(height=8, bgcolor=hex_color,        border_radius=4, expand=fill_pct)
            )
        if rest_pct > 0:
            children.append(
                ft.Container(height=8, bgcolor="surfaceVariant", border_radius=4, expand=rest_pct)
            )
        if not children:   # 0% — só o fundo
            children = [ft.Container(height=8, bgcolor="surfaceVariant", border_radius=4, expand=1)]

        return ft.Row(children, spacing=2, expand=True)

    try:
        if categories_kpi:
            cat_cards = []
            for cat in categories_kpi:
                cat_id, cat_name, cat_color, total, completed = cat
                completed  = int(completed or 0)
                total      = int(total or 0)
                pending    = total - completed
                progress   = (completed / total) if total > 0 else 0.0
                hex_color  = CATEGORY_COLORS.get(cat_color, "#1E88E5")

                cat_card = ft.Card(
                    elevation=3,
                    content=ft.Container(
                        width=230,
                        padding=14,
                        content=ft.Column([
                            # Cabeçalho: bolinha + nome
                            ft.Row([
                                ft.Container(
                                    width=14, height=14,
                                    border_radius=7, bgcolor=hex_color,
                                ),
                                ft.Text(cat_name, size=14, weight="bold", expand=True),
                            ], spacing=8),
                            ft.Divider(height=6),
                            # Três métricas
                            ft.Row([
                                ft.Column([
                                    ft.Text(str(total),     size=20, weight="bold"),
                                    ft.Text("Total",        size=10, color="grey"),
                                ], horizontal_alignment="center", spacing=2),
                                ft.Column([
                                    ft.Text(str(completed), size=20, weight="bold", color="green"),
                                    ft.Text("Concluídas",   size=10, color="grey"),
                                ], horizontal_alignment="center", spacing=2),
                                ft.Column([
                                    ft.Text(str(pending),   size=20, weight="bold", color="red"),
                                    ft.Text("Pendentes",    size=10, color="grey"),
                                ], horizontal_alignment="center", spacing=2),
                            ], alignment="spaceAround"),
                            ft.Divider(height=6),
                            # Barra de progresso segura
                            _progress_bar(progress, hex_color),
                            ft.Text(
                                f"{int(progress * 100)}% concluído",
                                size=10, color="grey", text_align="right",
                            ),
                        ], spacing=5),
                    ),
                )
                cat_cards.append(cat_card)

            cat_section_body = ft.Row(cat_cards, spacing=12, wrap=True)

        else:
            cat_section_body = ft.Text(
                "Nenhuma categoria criada ainda. Acesse 'Categorias' para criar.",
                italic=True, color="grey",
            )

    except Exception as err:
        print(f"[DASH] Erro ao montar seção de categorias: {err}")
        cat_section_body = ft.Text(
            f"Erro ao carregar categorias: {err}", color="red", italic=True
        )

    # -------------------------------------------------------------------------
    # Montagem final
    # -------------------------------------------------------------------------
    column.controls.extend([
        title,
        ft.Divider(height=4),
        kpis_row,
        charts_row,
        ft.Divider(height=8),
        cat_section_title,
        cat_section_body,
    ])

    try:
        page.update()
    except Exception:
        pass


def create_dashboard_view(page: ft.Page, db):
    """Cria o container raiz do Dashboard com Column stateful (key='dashboard_content')."""
    dashboard_body = ft.Column(
        key="dashboard_content",
        scroll="auto",
        expand=True,
        spacing=16,
    )
    build_dashboard_content(dashboard_body, page, db)
    return ft.Container(
        content=dashboard_body,
        padding=20,
        expand=True,
    )
