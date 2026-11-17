# `specs/` — O que implementar

Especificações técnicas numeradas, agrupadas por módulo. Cada spec é autocontida no seu tema e traz objetivo, escopo, arquivos afetados, especificação técnica, **critérios de aceite** e **casos de teste**.

## Estrutura e ciclo de vida

```
specs/
├── active/                    # Spec EM ANDAMENTO (no máximo uma por vez)
├── _modelo/                   # Modelo de pasta de módulo (copie ao criar um módulo novo)
└── {módulo}/                  # customers, sales, fiscal...
    ├── README.md              # Índice: mapa, dependências, roteamento por tarefa e por arquivo
    ├── ROTEIRO-IMPLEMENTACAO.md   # (séries que cruzam módulos) ordem, pontos de atenção, verificação final
    ├── SPEC-NN-....md         # Backlog: specs ainda não iniciadas
    └── completed/             # Specs concluídas
```

```
specs/{módulo}/SPEC-NN.md  ──ativar──►  specs/active/SPEC-NN.md  ──concluir──►  specs/{módulo}/completed/SPEC-NN.md
       (backlog)                           Status: Em andamento                     Status: Concluída (data)
```

A movimentação é feita pela skill `doc`, que também:
- atualiza o campo `Status` no cabeçalho da spec;
- **corrige os links** no `README.md` do módulo (e em outras specs) para o novo caminho;
- só conclui a spec com todos os critérios de aceite verificados e os testes passando.

## Módulos

Cada módulo ganha uma pasta e uma linha nesta tabela **na primeira spec dele** (skill `spec` §2.6). Nomes de módulo seguem `frontend/src/modules/` (ver o mapa em `@/AGENT.md` §1).

| Módulo | Índice | Observação |
|--------|--------|------------|
| _(nenhum módulo com specs ainda)_ | — | Copie `_modelo/` para `specs/{módulo}/` ao escrever a primeira spec |

## Contrato

- Nome do arquivo: `SPEC-NN-TEMA-MODULO.md` (ex.: `SPEC-05-LISTA-CLIENTES.md`).
- Cabeçalho com tabela `Status / Camada / Dependências / Bloqueia / Referência`.
- Mudanças em specs aprovadas entram como **nota de revisão** no topo (`> **Revisão N (data):** ...`), nunca como edição silenciosa.
- O agente **não altera o escopo** de uma spec sem aprovação do usuário.
- Exemplos de código dentro das specs são em PT-BR e **comentados** (o usuário é iniciante).
