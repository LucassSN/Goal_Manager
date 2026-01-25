import flet as ft

def dash_view(page):
    return ft.View(
        route = "/dash",
        controls = [
            ft.Text("Dash View")
        ]
    )
    