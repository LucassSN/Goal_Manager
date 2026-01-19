import flet as ft

def main(page: ft.Page):
    page.title = "Gerenciador de Meta "
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    

    texto = ft.Text("Metas", size=30, color="blue")
    new_goal = ft.TextField(label = "Digite sua nova meta", width=300)

    
    def empty_text(e):
        if new_goal.value:
            page.add(ft.Checkbox(label = new_goal.value))
            new_goal.value =""
            page.update()
        else:
            page.add(ft.Text("Campo vazio"))
    #arrumar essa parte de remover as tasks
    def clean_screen(e):
        page.remove(new_goal.value)
        page.update()
    
    

    button = ft.ElevatedButton("Insert", on_click = empty_text)
    button1 = ft.ElevatedButton("Clean", on_click = clean_screen)

    page.add(texto, new_goal, button, button1)

ft.app(target=main)