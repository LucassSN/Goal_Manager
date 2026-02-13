import flet as ft
from logic import add_goal, close_alert

def main(page: ft.Page):
    page.title = "Gerenciador de Meta"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

 
    # Definindo o alerta
    alert =ft.AlertDialog(
        title = ft.Text("Campo Vazio"),
        content = ft.Text("O Campo de Metas não foi preenchido"),
        actions = [
            ft.TextButton("Entendido", on_click = lambda e: close_alert(page, alert)),
        ],
    )
    #Lembrar - Aprendizado: Colocar ele na lista suspensa apenas uma vez
    page.overlay.append(alert)
    
    title = ft.Text("Metas", size=30, color="white" )
    new_goal = ft.TextField(label = "Digite sua nova meta", width=300)
    meta_list = ft.Column(horizontal_alignment = ft.CrossAxisAlignment.CENTER)
    button = ft.FilledButton("Insert", on_click = lambda e: add_goal(page, new_goal, meta_list, alert))

    # meta seguindo, permitir que o usuario adicione tags
    # drop_down_list = ft.Dropdown(
    #     label = "Escolha uma tag",
    #     hint_text ="Selecione o grupo",
    #     options=[
    #         ft.dropdown.Option("Lazer"),
    #         ft.dropdown.Option("Trabalho"),
    #         ft.dropdown.Option("Educação"),
    #     ],
    #     width=300,
    # )


    page.add(title, 
             new_goal, 
             button,
             meta_list)
    
if __name__ == "__main__":
    ft.run(main)