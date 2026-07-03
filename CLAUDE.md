# Poupy

## Requisitos de Negócio

- Poupy é um app desktop de gastos pessoais local-first: o usuário registra seus gastos de forma simples e é dono dos próprios dados
- Usuário único. Sem contas, sem login, sem nuvem, sem sincronização - os dados vivem localmente na máquina do usuário
- Capacidades centrais: registrar gastos com valor, data, categoria e descrição opcional; listar, editar e excluir; categorias personalizáveis; total gasto do mês; relatórios de gastos por categoria e de evolução mensal como gráficos
- Por enquanto o app é somente de gastos: não há receita nem saldo. Não implementar esses conceitos por antecipação
- Manter o produto simples e focado: priorizar uma UI elegante e profissional, com gráficos prontos, acima da quantidade de funcionalidades. Implementar funcionalidades quando forem pedidas; não adicionar recursos por antecipação

## Detalhes Técnicos

- App desktop em Python com PySide6 (Qt 6), multiplataforma (Windows, macOS, Linux)
- Front-end: widgets Qt via PySide6; estilização com QSS (tema próprio para um visual elegante); gráficos com `pyqtgraph`
- Arquitetura em camadas dentro de um único processo: a UI (telas e widgets) é separada da lógica. Toda a lógica de negócio e o acesso a dados ficam numa camada de serviço/repositório tipada; a UI nunca executa SQL direto, sempre chama o serviço
- Banco: SQLite via módulo `sqlite3` da stdlib, um único arquivo local na máquina do usuário (caminho obtido de `QStandardPaths.AppDataLocation`, sem dependência extra). Mudanças de schema tratadas com migrações simples e versionadas via `PRAGMA user_version`
- Estrutura (`src/` layout): `poupy/ui` (telas e widgets Qt), `poupy/services` (lógica de negócio), `poupy/db` (conexão, repositórios e migrações), `poupy/models` (dataclasses tipadas). Ponto de entrada em `poupy/__main__.py`
- Ambiente e dependências: `uv` (`uv init`, `uv add`, `uv run`). Lint e formatação com `ruff`. Tipos com `mypy` em modo strict. Testes com `pytest` e `pytest-qt`
- Empacotamento e distribuição: `PyInstaller` para as três plataformas

## Interface e UX

- Janela principal: um cabeçalho com o navegador de mês, um número de destaque com o total gasto no mês selecionado, a lista de lançamentos do mês e os gráficos
- Navegação por mês: setas para mês anterior/seguinte, limitadas ao intervalo de meses que possuem registros (do primeiro lançamento até o mês atual); um dropdown lista os meses disponíveis, derivado dos ano-meses distintos no banco. Abre no mês atual por padrão
- Novo gasto: um botão "Novo gasto" (e atalho de teclado) abre um pop-up modal (`QDialog`) que pede Valor, Categoria, Descrição (opcional) e Data (default: hoje). Confirmar salva; cancelar descarta
- Categoria no formulário: um dropdown com as categorias existentes e um botão "Nova categoria" para criar na hora, sem sair do fluxo. Renomear e excluir categorias ficam numa tela de Categorias à parte
- Editar/excluir: selecionar um lançamento na lista abre o mesmo pop-up já preenchido; excluir pede confirmação
- Gráficos, reagindo ao mês/período selecionado: gastos por categoria (pizza ou barras) e evolução mensal do total gasto (linha ou barras) ao longo dos meses registrados
- Valores exibidos como moeda; internamente sempre centavos inteiros

## Estratégia

1. Para cada funcionalidade, escrever um plano com critérios de sucesso a serem marcados antes de codar, incluindo testes
2. Executar o plano, garantindo que todos os critérios sejam atendidos antes de seguir
3. Fazer testes de integração com `pytest` e `pytest-qt`, corrigindo defeitos, e confirmar que os dados persistem após reiniciar o app
4. Considerar uma funcionalidade concluída apenas quando estiver testada, compilando e rodando

## Padrões de Código

1. Usar as versões mais recentes das bibliotecas e abordagens idiomáticas atuais
2. Manter simples - NUNCA superengenharia, SEMPRE simplificar, SEM programação defensiva desnecessária. Sem recursos além do que foi pedido. Na dúvida entre uma solução simples e uma elaborada, escolher a simples
3. Em caso de ambiguidade ou informação faltante, PERGUNTAR antes de codar; nunca presumir requisitos nem inventar escopo
4. Se um comando ou pedido do usuário estiver errado, for inconsistente com este documento ou tecnicamente inviável, apontar isso e sugerir a correção essencial antes de prosseguir; fazer apenas sugestões essenciais, sem ruído
5. Dinheiro é SEMPRE armazenado e calculado como centavos inteiros, NUNCA ponto flutuante. Formatar como moeda apenas na exibição
6. Type hints em tudo; `mypy` em modo strict. Evitar `Any`; deixar os tipos pegarem os erros cedo
7. Manter a UI separada da lógica e dos dados: a UI nunca executa SQL, toda comunicação com o banco passa pela camada de serviço/repositório tipada
8. Ser conciso. Manter o README mínimo. IMPORTANTE: nunca usar emojis
