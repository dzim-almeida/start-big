# Architecture Decision Records (ADRs)

**Propósito:** Documentar decisões arquiteturais importantes do projeto StartBig ERP

---

## O que é um ADR?

Um **Architecture Decision Record** é um documento que captura:
- ✅ O que foi decidido
- ✅ Por quê foi decidido
- ✅ Que alternativas foram consideradas
- ✅ Quais são as consequências

Decisões arquiteturais precisam ser rastreáveis, não apenas em commits.

---

## Quando Criar um ADR

### ✅ Sempre criar
- Mudanças de padrão que afetam 3+ módulos
- Breaking changes (compatibilidade quebrada)
- Trade-offs significativos (performance vs. legibilidade)
- Soluções para incidentes recorrentes
- Novas camadas ou abstrações

### ⚠️ Considerar criar
- Padrões emergentes em um módulo
- Alternativas entre 2+ abordagens principais

### ❌ Não precisa (use commit message)
- Bug fixes
- Features locais (1 componente)
- Refactoring sem mudança de padrão

---

## Estrutura de um ADR

```markdown
# ADR-XXX: Título em PascalCase

**Status:** Accepted | Proposed | Deprecated
**Data:** 2026-09-16
**Decidido por:** Nome / Agente de IA
**Última atualização:** 2026-09-16

## Contexto
Descrever a situação que motivou a decisão.
- Por que o status quo não funciona?
- Quais são as restrições?
- Qual é o problema específico?

## Decisão
Descrever a decisão tomada de forma clara.
- O que foi decidido?
- Como será implementado?
- Quem está responsável?

## Alternativas Consideradas

### Alternativa A
Breve descrição.
**Por que rejeitada:** [razão específica]

### Alternativa B
Breve descrição.
**Por que rejeitada:** [razão específica]

## Consequências

### ✅ Benefícios
- Melhoria 1
- Melhoria 2

### ❌ Riscos/Custos
- Custo 1
- Custo 2

### 🔄 Mitigation
Como reduzir riscos? (se necessário)

## Referências
- ADR-NNN (relacionado)
- Arquivo afetado: `backend-fastapi/app/services/fiscal/`
- Commit: `abc1234` (implementação)
- Memory: `memory/modulo-fiscal-refatoracao.md` (contexto)

## Próximos Passos
- [ ] Implementar em X
- [ ] Atualizar docs em Y
- [ ] Review em Z

---

**Última atualização:** 2026-09-16
```

---

## Nomenclatura

**Formato:** `ADR-NNN_titulo_em_snake_case.md`

**Exemplos:**
```
ADR-001_fiscal_engine_puro.md
ADR-002_form_context_provider_injection.md
ADR-003_valores_monetarios_centavos.md
```

**Ordem:**
- ADRs mais antigos = números baixos
- Novos ADRs = número sequencial

---

## Processo

### 1. Agente de IA Propõe Decisão
```markdown
# ADR-NNN: [Título]
**Status:** Proposed
```

### 2. Review
- Desenvolvedor revisa
- Valida trade-offs
- Marca como `Accepted` ou pede revisão

### 3. Implementação
Código referencia ADR:
```python
# ADR-NNN: motivo da decisão
def funcao_importante():
    pass
```

### 4. Fechamento (Opcional)
Se decisão for superada:
```markdown
**Status:** Deprecated
**Substituído por:** ADR-YYY
**Data de Deprecação:** 2026-10-01
```

---

## ADRs Existentes

| ADR | Título | Status |
|-----|--------|--------|
| [ADR-001](ADR-001_eventos_fiscais_em_tabela_propria.md) | Eventos fiscais (CC-e) em tabela própria | Accepted |
| [ADR-002](ADR-002_devolucao_a_partir_do_snapshot.md) | NF-e de devolução nasce do snapshot, saldo por item | Accepted |

---

## Integração com Documentação

### Consulte também
- `AGENT.md § 7` — Esta seção
- `CLAUDE.md` — Setup e deploy
- `memory/MEMORY.md` — Padrões recorrentes

### Quando criar, atualize
1. **Código:** Adicione comentário referenciando ADR-NNN
2. **AGENT.md:** Se afeta padrões globais (seção 4)
3. **memory/MEMORY.md:** Se é padrão de projeto (confirme)
4. **rules/:** Se muda contrato arquitetural

---

**Última atualização:** 2026-09-16
**Mantido por:** Harness Engineering Team
