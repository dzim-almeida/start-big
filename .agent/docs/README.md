# `docs/` — Conhecimento consolidado por módulo

A memória de longo prazo do projeto. Enquanto `specs/` diz **o que fazer**, `docs/` guarda **o que já existe, por que foi feito assim e o que aprendemos no caminho**. É o **primeiro lugar** que o agente lê em qualquer tarefa (skill `doc`).

## Estrutura

```
docs/
├── _shared/
│   └── learn/                 # Aprendizados que valem para o projeto todo (ambiente, ferramentas, testes, Tauri)
├── _modelo/                   # Modelo de pasta de módulo (copie ao criar um módulo novo)
└── {módulo}/                  # customers, sales, fiscal...
    ├── README.md              # Visão geral e arquitetura do módulo. Mantido pelo time
    ├── SUMMARY.md             # Estado ATUAL da implementação (reescrito ao concluir a spec avulsa ou a série)
    ├── CHANGELOG.md           # Histórico de alterações (acumulado, mais recente no topo)
    ├── ACORDO.md              # Decisões numeradas do planejamento (skill `spec`)
    ├── adr/                   # Decisões que mudam uma premissa do projeto (ADR-NNN-TITULO.md)
    ├── archive/               # Documentos superados, lidos só para histórico
    ├── handbook/              # Visão Geral, Especificação de Negócio e Documentação Técnica (skill `handbook`)
    ├── learn/                 # Aprendizados da sessão: AAAA-MM-DD-slug.md + README.md (índice)
    └── design/                # Referências visuais (imagens, PDFs, protótipos) e LINKS.md
```

## Quem escreve o quê

| Arquivo | Autor | Quando |
|---------|-------|--------|
| `README.md` | Time (o agente só **propõe** mudanças) | Mudança de arquitetura do módulo. Mantenha curto: o agente lê só as seções que a tarefa toca (skill `doc` §2) |
| `SUMMARY.md` | Agente | Ao concluir uma spec avulsa ou a última spec de uma série (skill `doc` §7.1) |
| `CHANGELOG.md` | Agente | Ao concluir cada spec (skill `doc` §7.2) |
| `learn/*.md` e `learn/README.md` | Agente | Quando surge um aprendizado importante (`rules/session-learnings.md`). O índice é atualizado junto |
| `ACORDO.md`, `adr/` | Agente propõe, usuário aprova | No planejamento do módulo (skill `spec`) |
| `handbook/*` | Agente, sob pedido | Skill `handbook`, depois da aprovação do usuário |
| `design/*` | Time / design | Quando o design muda. O agente não edita |

## Contrato

- Nada que já esteja no código ou na spec é repetido aqui. Docs explicam o **porquê** e o **estado**.
- O `CLAUDE.md` da raiz já documenta portas, sidecar, banco e papel da máquina: **não duplique** aqui; referencie.
- Sem segredos, caminhos de banco de cliente, certificados ou dados pessoais.
- Módulo novo → criar `docs/{módulo}/` a partir de `_modelo/`, com pelo menos `README.md` e `learn/`.
- Texto em PT-BR, escrito para quem está começando: explique o termo técnico na primeira vez que ele aparece.
