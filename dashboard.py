import flet as ft
import flet_charts as fch

def create_dashboard_view(page: ft.Page, db):
    # --- DATA BINDING: Buscando os dados REAIS do banco ---
    goals_kpi = db.get_goals_kpi()
    tasks_kpi = db.get_tasks_kpi()
    tasks_per_goal = db.get_tasks_per_goal() # Retorna: [('title', count), ...]

    # 1. Construindo os Cards de KPI (Linha Superior)
    kpis_row = ft.Row([
        # KPI 1: Metas
        ft.Card(
            elevation=4,
            expand=True,
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Progresso das Metas", size=14, color="grey"),
                    ft.Row([
                        ft.Text(f"{goals_kpi['concluidas']} / {goals_kpi['total']}", size=28, weight="bold"),
                        ft.Icon(ft.Icons.FLAG, color="blue", size=30)
                    ], alignment="spaceBetween")
                ])
            )
        ),
        # KPI 2: Tarefas Globais
        ft.Card(
            elevation=4,
            expand=True,
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Progresso das Tarefas", size=14, color="grey"),
                    ft.Row([
                        ft.Text(f"{tasks_kpi['concluidas']} / {tasks_kpi['total']}", size=28, weight="bold"),
                        ft.Icon(ft.Icons.CHECKLIST, color="green", size=30)
                    ], alignment="spaceBetween")
                ])
            )
        )
    ], spacing=20)

    # 2. Gráfico de Rosca (Pie Chart): Status das Metas
    if goals_kpi["total"] > 0:
        pie_chart = fch.PieChart(
            sections=[
                fch.PieChartSection(
                    value=goals_kpi["concluidas"],
                    color="green",
                    radius=40,
                    title=""
                ),
                fch.PieChartSection(
                    value=goals_kpi["pendentes"],
                    color="red",
                    radius=40,
                    title=""
                ),
            ],
            sections_space=2,
            center_space_radius=50,
            expand=True
        )
    else:
        # Fallback caso não existam metas
        pie_chart = ft.Text("Nenhuma meta cadastrada.", italic=True, color="grey")

    pie_card = ft.Card(
        elevation=4,
        expand=1,
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Status das Metas", weight="bold", size=16),
                ft.Container(content=pie_chart, height=220, padding=10, alignment=ft.Alignment(0, 0))
            ], horizontal_alignment="center")
        )
    )

    # 3. Gráfico de Barras (Bar Chart): Volume de Tarefas por Meta
    bar_groups = []
    max_y = 0 # Usado para calcular o limite visual do eixo Y
    labels_bottom = []

    for index, item in enumerate(tasks_per_goal):
        title = item[0]
        count = item[1]
        if count > max_y:
            max_y = count
            
        # Adiciona a barra
        bar_groups.append(
            fch.BarChartGroup(
                x=index,
                rods=[
                    fch.BarChartRod(
                        from_y=0,
                        to_y=count,
                        color="blue",
                        width=25,
                        tooltip=f"{title}: {count} tarefas",
                        border_radius=4
                    )
                ]
            )
        )
        
        # Adiciona o rótulo do eixo X encurtado para caber bonito
        short_title = title[:10] + "..." if len(title) > 10 else title
        labels_bottom.append(
            fch.ChartAxisLabel(value=index, label=ft.Text(short_title, size=10))
        )

    # Geração forçada de números inteiros para o eixo Y
    limite_y = max_y + 1 if max_y > 0 else 5
    labels_left = [
        fch.ChartAxisLabel(value=i, label=ft.Text(str(i), size=10)) 
        for i in range(limite_y + 1)
    ]

    if bar_groups:
        bar_chart = fch.BarChart(
            groups=bar_groups,
            border=ft.Border.all(1, "outline"),
            left_axis=fch.ChartAxis(labels=labels_left),
            bottom_axis=fch.ChartAxis(labels=labels_bottom),
            max_y=limite_y,
            expand=True
        )
    else:
        bar_chart = ft.Text("Nenhuma tarefa vinculada.", italic=True, color="grey")

    bar_card = ft.Card(
        elevation=4,
        expand=2, # Faz o gráfico de barras ocupar mais espaço lateral que o de rosca
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Volume de Tarefas por Meta", weight="bold", size=16),
                ft.Container(content=bar_chart, height=220, padding=10, alignment=ft.Alignment(0, 0))
            ], horizontal_alignment="center")
        )
    )

    # 4. Retorna a composição final agrupada
    return ft.Container(
        content=ft.Column([
            ft.Text("Dashboard Analítico", size=28, weight="bold"),
            kpis_row,
            ft.Row([pie_card, bar_card], alignment="start", vertical_alignment="start")
        ], scroll="auto", expand=True, spacing=20),
        padding=20,
        expand=True
    )
