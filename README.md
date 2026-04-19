# 📊 Goal Manager

Um gerenciador de metas desenvolvido com Python e Flet, focado em uma experiência visual limpa e sincronização de dados eficiente. Este projeto faz parte dos meus estudos sobre interfaces ricas e persistência de dados local.

🚀 Funcionalidades
- **Visualização Dual (Versão 2.0)**: Alternância dinâmica entre **Modo Lista** e **Modo Card** através de um botão dedicado na AppBar.
- **Layout Inteligente**: Uso de `GridView` para cards e `ListView` para listas, garantindo organização automática.
- **Persistência em SQLite**: Suas metas são salvas de forma segura em um banco de dados local (`goal.db`).
- **Monitoramento em Tempo Real Otimizado**: O app utiliza multi-threading com um sistema de hashing ultra-rápido (0.5s) para atualizar a interface instantaneamente.
- **Feedback Visual Dinâmico**: Estilização rica com riscado e mudança de cor ao concluir metas.
- **Sistema de Alertas**: Validação de campos e tratamento de exceções com componentes personalizados.

🛠️ Tecnologias Utilizadas
- **Flet**: Framework moderno para interfaces ricas.
- **SQLite**: Banco de dados leve e eficiente.
- **Threading**: Processamento paralelo para monitoramento fluído.

📂 Estrutura do Projeto
- `main.py`: Interface principal, AppBar e navegação.
- `logic.py`: Componentes dinâmicos (`ItemGoal`), lógica de visualização e monitor de banco.
- `database.py`: Classe de manipulação do SQLite.

🧠 O que eu aprendi neste estudo
- **Arquitetura Escalável**: Separação clara entre UI, Lógica e Dados.
- **Otimização de Performance**: Uso de comparações de estado para evitar re-renderizações custosas.
- **UX Adaptativo**: Criação de layouts que se ajustam entre diferentes modos de visualização.
- **Versionamento com Git**: Fluxo de trabalho com branches para desenvolvimento de novas versões (v2.0).
