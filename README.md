# 📊 Goal Manager

Um gerenciador de metas desenvolvido com Python e Flet, focado em uma experiência visual limpa e sincronização de dados eficiente. Este projeto faz parte dos meus estudos sobre interfaces ricas e persistência de dados local.

🚀 Funcionalidades
- **Visualização Dual (v2.0)**: Alternância dinâmica entre **Modo Lista** e **Modo Card** com `GridView` e `ListView`.
- **Drag & Drop**: Reordenação de metas por arrastar e soltar com persistência no banco.
- **Sistema de Categorias (v2.2)**: Criação de categorias com cores personalizadas, atribuição opcional às metas e badge visual nos cards.
- **Dashboard Analítico em Tempo Real**: KPIs globais (metas e tarefas), gráficos de rosca e barras, e cards de desempenho por categoria atualizados automaticamente.
- **Sub-tarefas por Meta**: Adição e conclusão de tarefas vinculadas a cada meta.
- **Persistência em SQLite**: Metas, tarefas, categorias e preferências salvas localmente em `goal.db`.
- **Monitoramento Assíncrono**: Multi-threading com hashing (0.5s) para sincronização sem re-renderizações desnecessárias.
- **Preferências Persistidas**: Tema claro/escuro salvo entre sessões.
- **Feedback Visual Dinâmico**: Riscado, mudança de cor e badges ao concluir metas.

🛠️ Tecnologias Utilizadas
- **Flet**: Framework moderno para interfaces ricas cross-platform.
- **SQLite**: Banco de dados leve e eficiente.
- **flet-charts**: Biblioteca de gráficos (PieChart, BarChart).
- **Threading**: Processamento paralelo para monitoramento fluído.

📂 Estrutura do Projeto
- `main.py`: Entry point, roteamento e setup de Views.
- `logic.py`: Componentes dinâmicos (`ItemGoal`, `TaskItem`, `CategoryItem`), lógica de negócio e monitor assíncrono.
- `database.py`: Classe de manipulação do SQLite (goals, tasks, categories, settings).
- `dashboard.py`: Dashboard analítico stateful com KPIs e gráficos.

🧠 O que eu aprendi neste estudo
- **Arquitetura Escalável**: Separação clara entre UI, Lógica e Dados.
- **Otimização de Performance**: Sistema de hash + threading lock para evitar race conditions e re-renderizações duplicadas.
- **UX Adaptativo**: Layouts que se ajustam entre diferentes modos de visualização.
- **Dashboards em Tempo Real**: Componentes stateful monitorados por thread assíncrona.
- **Versionamento com Git**: Fluxo de trabalho com branches e Conventional Commits.