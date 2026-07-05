# Code review - correções e melhorias

Revisão da base em `src/poupy`. Itens ordenados por severidade. Cada um traz o
local (`arquivo:linha`), o problema, por que importa e a correção sugerida.

## Bugs / correções

### 1. `parse_moeda` usa ponto flutuante (viola centavos inteiros)

- Local: `src/poupy/ui/format.py:49-62`
- Problema: a leitura de moeda faz `round(float(limpo) * 100)`. Isso contraria a
  regra 5 do CLAUDE.md ("dinheiro NUNCA em ponto flutuante"). Comportamento
  comprovado:
  - `parse_moeda("99999999999999,99")` -> `9999999999999998` (perda de precisão
    do float; o correto seria `...9999`).
  - `parse_moeda("10,999")` -> `1100`: a terceira casa é engolida sem aviso;
    R$ 10,999 vira R$ 11,00 silenciosamente.
- Por que importa: é justamente o tipo de erro de dinheiro que a arquitetura
  jura evitar. Para valores realistas do app raramente aparece, mas a técnica
  está errada por princípio.
- Correção: fazer o parsing sem float. Separar a parte inteira e a decimal pelo
  separador de vírgula, validar que a parte decimal tem no máximo 2 dígitos
  (rejeitar ou truncar de forma explícita) e montar os centavos com aritmética
  inteira.

### 2. "Criar base nova" sobre uma pasta que já tem `poupy.db` abre a base antiga

- Local: `src/poupy/ui/onboarding.py:118-129` + `src/poupy/db/connection.py:61-72`
- Problema: `_criar` monta `pasta/poupy.db` e chama `abrir_conexao`, que trata
  arquivo já existente como ABRIR (valida identidade e aponta o ponteiro para
  ele). Se a pasta escolhida já contém um `poupy.db`, o fluxo "Criar base nova"
  silenciosamente abre a base existente, com os dados antigos, em vez de criar
  uma nova.
- Por que importa: não é destrutivo, mas engana o usuário que pediu "base nova"
  e recebe dados "vindos do nada". 
- Correção: em `_criar`, se `db_path` já existe, avisar e pedir confirmação
  ("Já existe uma base aqui; deseja abri-la?") ou orientar a escolher outra
  pasta, mantendo o "criar" restrito a arquivo novo.

### 3. `PRAGMA journal_mode = WAL` sem conferir se engatou

- Local: `src/poupy/db/connection.py:79,85` e `fechar_conexao` em `:95-97`
- Problema: o retorno do `PRAGMA journal_mode = WAL` não é verificado. Em alguns
  sistemas de arquivos de rede/nuvem (que o CLAUDE.md lista como destino de
  backup suportado), o SQLite não consegue ativar o WAL e permanece em outro
  modo. Aí o `wal_checkpoint(TRUNCATE)` do fechamento vira no-op e a garantia
  "fechar o app + copiar o arquivo = backup íntegro" enfraquece sem qualquer
  sinal.
- Por que importa: o modelo de backup do produto depende do WAL + checkpoint.
- Correção: ler o resultado do PRAGMA; se não voltar `wal`, ao menos registrar
  o fato (log) ou tratar como base não recomendada. Sem UI nova - apenas não
  assumir cegamente que o WAL está ativo.

## Melhorias

### 4. Resolver o nome da categoria faz uma query de todas as categorias por gasto

- Local: `src/poupy/services/gastos.py:135-139`
- Problema: `_nome_categoria` chama `self.categorias()` (SELECT de todas) e faz
  varredura O(n) a cada `registrar_gasto`/`atualizar_gasto`, só para preencher
  `categoria_nome` no `Gasto` retornado.
- Correção: expor no repositório um `nome_categoria(conn, id)` (SELECT por id) e
  usá-lo, ou devolver o `Gasto` já com JOIN. Impacto pequeno, mas é trabalho
  desnecessário no caminho quente.

### 5. Duplicidade de categoria é sensível a maiúsculas

- Local: `src/poupy/db/migrations.py:26-28` (UNIQUE) + validação em
  `src/poupy/services/gastos.py:23-35`
- Problema: `nome TEXT NOT NULL UNIQUE` usa collation BINARY, então "Lazer" e
  "lazer" coexistem. O usuário acaba com categorias duplicadas na prática.
- Correção: `UNIQUE` com `COLLATE NOCASE` (via migração) ou normalizar/checar de
  forma case-insensitive na camada de serviço antes de inserir/renomear.

### 6. Índice de data não acelera os filtros por mês

- Local: `src/poupy/db/migrations.py:38` (`idx_gasto_data`) usado por
  `substr(data, 1, 7) = ?` em `src/poupy/db/repository.py:80-141`
- Problema: o índice é sobre `data` inteira; os filtros por mês usam
  `substr(data,1,7)`, que não aproveita o índice e faz varredura.
- Por que importa: irrelevante no volume de um app pessoal; anotado só para não
  passar a impressão de que o índice ajuda essas consultas. Alternativa, se um
  dia pesar: filtrar por range (`data >= 'YYYY-MM-01' AND data < proximo_mes`),
  que usa o índice.

### 7. Onboarding não menciona o risco de pasta em nuvem

- Local: `src/poupy/ui/onboarding.py:34-37` (`_EXPLICACAO`)
- Problema: o CLAUDE.md pede que, no máximo, o texto do onboarding mencione o
  risco de corromper a base ao abrir a mesma pasta sincronizada em duas máquinas
  ao mesmo tempo. O texto atual não cita isso.
- Correção: acrescentar uma frase curta no `_EXPLICACAO` sobre não usar a mesma
  base em duas máquinas simultaneamente quando estiver em nuvem.

### 8. Salvar/editar não leva o usuário ao mês do lançamento

- Local: `src/poupy/ui/main_window.py:99-115`
- Problema: ao registrar um gasto (data padrão = hoje) enquanto se navega um mês
  antigo, ou ao editar movendo o gasto para outro mês, `_atualizar` mantém o mês
  atual em tela. O lançamento é salvo, mas some da lista sem feedback.
- Correção: após salvar, selecionar o mês do gasto salvo (`gasto_salvo.data`)
  antes de `_atualizar`, para o usuário ver o que acabou de registrar.

### 9. Cor de fundo dos gráficos fixa em branco

- Local: `src/poupy/ui/graficos.py:11` (`_FUNDO = "#ffffff"`)
- Problema: a cor está acoplada ao tema claro atual. Está coerente com o QSS de
  hoje, mas se o tema mudar (ex.: modo escuro), os gráficos ficam brancos
  destoando do resto.
- Correção: derivar as cores dos gráficos do mesmo conjunto de cores do tema
  (ou de constantes compartilhadas com o QSS), em vez de literais duplicados.
