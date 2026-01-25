import flet as ft

def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    def close_alert(e):
        alert.open = False
        page.update()

    # Definindo o alerta
    alert =ft.AlertDialog(
        title = ft.Text("Campo Vazio"),
        content = ft.Text("O Campo de Metas não foi preenchido"),
        actions = [
            ft.TextButton("Entendido", on_click = close_alert),
        ],
    )
    #Lembrar - Aprendizado: Colcoar ele na lista suspensa apenas uma vez
    page.overlay.append(alert)
    
    title = ft.Text("Metas", size=30, color="white" )
    new_goal = ft.TextField(label = "Digite sua nova meta", width=300)

    meta_list = ft.Column(horizontal_alignment = ft.CrossAxisAlignment.CENTER)

    
    def empty_text(e):
        if new_goal.value:
            meta_list.controls.append(ft.Checkbox(label = new_goal.value))
            new_goal.value =""
            page.update()
        else:
            alert.open = True
            page.update()

    

    button = ft.ElevatedButton("Insert", on_click = empty_text)

    page.add(title, 
             new_goal, 
             button,
             meta_list,)

ft.app(target=main)