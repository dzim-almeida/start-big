# Skills — Padrões de Qualidade e Teste

**Versão:** 1.0
**Propósito:** Guias práticos para agentes de IA garantirem qualidade arquitetural
**Data:** 2026-09-16

---

## 📚 Skills Disponíveis

### 1. [code-quality](code-quality/SKILL.md)
**Quando usar:** Antes de implementar features, durante code review, refatoração

**Garante:**
- ✅ DRY — Lógica não repetida
- ✅ YAGNI — Sem features/parâmetros desnecessários
- ✅ CLEAN CODE — Nomes claros, funções focadas, abstração única

**Seções:**
1. DRY + padrões de reutilização (composables, services, constantes)
2. YAGNI + quando estender
3. CLEAN CODE (nomes, tamanho, abstração, erros, comentários)
4. Checklist de qualidade
5. Estrutura esperada (frontend/backend)
6. Exceções documentadas

### 2. [tdd](tdd/SKILL.md)
**Quando usar:** Ao desenvolver features, corrigir bugs com cobertura

**Garante:**
- ✅ RED → GREEN → REFACTOR — Ciclo completo
- ✅ Backend — pytest + FastAPI (fixtures, endpoints, services)
- ✅ Frontend — Vitest + Vue 3 (composables, componentes, builders)
- ✅ Cobertura > 70% (ideal 85%+)

**Seções:**
1. Ciclo TDD com exemplos reais
2. Backend: fixtures, services, endpoints
3. Frontend: composables, componentes, mocks
4. Padrões do projeto (fiscal, form context)
5. Comandos para rodar testes
6. Boas práticas
7. CI/CD
8. Cobertura esperada

---

## 🎯 Como Usar

### Para Agentes de IA

#### Opção 1: Consultar antes de implementar
```
Tarefa: Implementar nova feature X
↓
Consulte: .agent/skill/code-quality.md (seção 2-3)
Consulte: .agent/skill/tdd.md (seção 1-2)
↓
Implemente: Código limpo + testes primeiro
```

#### Opção 2: Code Review
```
Código de colega para revisar
↓
Use: .agent/skill/code-quality.md (seção 4 — Checklist)
Use: .agent/skill/tdd.md (seção 6 — Boas Práticas)
↓
Feedback com referências às skills
```

#### Opção 3: Melhorar Código Existente
```
Refatorar módulo antigo
↓
Leia: .agent/skill/code-quality.md (seção 3 + 5)
Escreva: Testes primeiro (.agent/skill/tdd.md)
↓
Refatore com confiança
```

### Para Desenvolvedores Humanos

- **Dúvida sobre DRY/YAGNI/CLEAN:** Consulte `code-quality.md`
- **Como testar algo:** Consulte `tdd.md` (seção backend/frontend apropriada)
- **Code review:** Use checklists em ambos os docs
- **Cobertura baixa:** Veja `tdd.md § 8` (mínimos esperados)

---

## 🔗 Integração com Projeto

### Relação com AGENT.md
| Documento | Foco | Quando Consultar |
|-----------|------|------------------|
| `AGENT.md` | Stack, arquitetura, troubleshooting | Setup inicial |
| `code-quality.md` | Qualidade de código (DRY/YAGNI) | Antes de implementar |
| `tdd.md` | Testes e cobertura | Durante desenvolvimento |

### Relação com rules/
- **rules/architecture-communication.md** — Contrato obrigatório (schema, response)
- **code-quality.md** — Como escrever código limpo DENTRO do contrato
- **tdd.md** — Como validar código + contrato com testes

### Relação com CLAUDE.md
- Leia CLAUDE.md § "Development Commands" para saber como rodar testes
- Execute `pytest test/` ou `npm run test` conforme instruções em tdd.md

---

## ✅ Checklist de Uso

### Antes de Implementar Feature
- [ ] Consultar `code-quality.md § 2` — Posso estender sem ser YAGNI?
- [ ] Consultar `code-quality.md § 3` — Será clean code?
- [ ] Consultar `tdd.md § 1-2` — Qual é o ciclo TDD para isso?

### Durante Desenvolvimento
- [ ] RED: Teste específico falha (tdd.md)
- [ ] GREEN: Implementação mínima passa
- [ ] REFACTOR: Melhorar com code-quality.md
- [ ] Rodar testes (commands em tdd.md)

### Code Review
- [ ] Checklist em code-quality.md § 4
- [ ] Checklist em tdd.md § 6
- [ ] Cobertura mínima atingida? (tdd.md § 8)

---

## 🚀 Exemplos Rápidos

### Dúvida: "Preciso desse parâmetro?"
→ Consulte `code-quality.md § 2` (YAGNI)

### Dúvida: "Como estruturar meu teste?"
→ Consulte `tdd.md § 2.3` (backend) ou `tdd.md § 3.2` (frontend)

### Dúvida: "Função está muito grande"
→ Consulte `code-quality.md § 3.2` (tamanho de funções)

### Dúvida: "Qual cobertura esperar?"
→ Consulte `tdd.md § 8` (cobertura por camada)

---

## 📖 Leitura Recomendada

### Ordem Sugerida
1. **code-quality.md** — 20 min (visão geral de qualidade)
2. **tdd.md § 1-2** — 15 min (ciclo TDD aplicado)
3. **tdd.md § 3-4** — 10 min (padrões do projeto)

### Por Necessidade
| Necessidade | Arquivo | Seção |
|-------------|---------|-------|
| Remover código duplicado | code-quality.md | § 1 |
| Não estender sem razão | code-quality.md | § 2 |
| Nomes significativos | code-quality.md | § 3.1 |
| Testar backend | tdd.md | § 2 |
| Testar frontend | tdd.md | § 3 |
| Fixtures/builders | tdd.md | § 2.4, 3.4 |

---

## 🔄 Feedback e Atualizações

### Encontrou ambiguidade?
→ Abrir issue mencionando a seção

### Padrão recorrente não coberto?
→ Propor adição em code-quality.md ou tdd.md

### Novo padrão no projeto?
→ Adicionar exemplo em tdd.md § 4 (Padrões Específicos)

---

**Última atualização:** 2026-09-16
**Próxima revisão:** Após primeira PR usando estas skills
