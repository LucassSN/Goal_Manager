# ✅ Goal Manager
Um gerenciador de metas desenvolvido com Python e Flet, focado em uma experiência visual limpa e sincronização de dados eficiente. Este projeto faz parte dos meus estudos sobre interfaces ricas e persistência de dados local.

## 🚀 Funcionalidades

- Persistência em SQLite: Suas metas são salvas em um banco de dados local (goal.db).

- Monitoramento em Tempo Real: O app utiliza multi-threading para monitorar o banco de dados e atualizar a interface automaticamente sem necessidade de recarregar.

- Feedback Visual de Conclusão: Ao marcar uma meta, o texto é riscado e sua cor alterada dinamicamente.

- Sistema de Alertas: Tratamento de exceções para campos vazios com componentes personalizados.

## 🛠️ Tecnologias Utilizadas
- Flet: Framework para construção de interfaces (baseado em Flutter).

- SQLite: Banco de dados relacional leve.

- Threading: Para processamento paralelo do monitor de sincronia.

## 📂 Estrutura do Projeto
- main.py: Ponto de entrada do aplicativo e definição da interface principal.

- logic.py: Contém a classe ItemGoal e toda a lógica de manipulação da UI e monitoramento.

- database.py: Camada de persistência (CRUD) e conexão com o SQLite.

## 🧠 O que eu aprendi neste estudo
- Separação de responsabilidades (UI vs Lógica vs Banco de Dados).

- Uso de global variables e hashing (str comparison) para evitar renderizações desnecessárias na tela.

- Customização profunda de componentes Flet (Alerts, Buttons e Containers).
