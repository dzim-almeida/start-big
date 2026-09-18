# ADR-001: Eventos fiscais (CC-e) em tabela própria, não em colunas do documento

**Status:** Accepted
**Data:** 2026-09-17
**Decidido por:** Agente de IA (sessão TASK002), seguindo o precedente de `InutilizacaoFiscal`
**Última atualização:** 2026-09-17

## Contexto
A Carta de Correção Eletrônica (CC-e) é um **evento** vinculado a uma NF-e já autorizada: não consome numeração, não altera a nota, não tem itens. Uma nota aceita até **20** cartas, cada uma com protocolo, sequência, XML e PDF próprios, e a SEFAZ considera vigente só a última. A spec original (`TASK002`) chegou descrevendo a devolução (finalidade 4) — que é uma **emissão** nova, com número e itens — e foi reescrita antes da implementação.

O `DocumentoFiscal` já carrega o cancelamento como mudança de `status`, o que funciona porque o cancelamento é único e terminal. A carta não é nem um nem outro.

## Decisão
Criar `carta_correcao_fiscal` (`app/db/models/carta_correcao_fiscal.py`) com FK para `documento_fiscal`, `sequencia` atribuída pela SEFAZ, `status` próprio (`PROCESSANDO | AUTORIZADA | REJEITADA | ERRO`), protocolo, mensagem, URLs e caminhos locais de XML/PDF. Serviço em `app/services/fiscal/carta_correcao.py`; o `DocumentoFiscal` expõe só `total_cartas_correcao` e `ultima_carta_correcao` na leitura (derivados, não persistidos).

Regras do serviço, aplicadas **antes** de chamar a emissora: só `tipo_documento == "NFE"`, só `status == "AUTORIZADA"`, no máximo 20 autorizadas, nunca duas `PROCESSANDO` na mesma nota (409). O registro nasce `PROCESSANDO` antes da chamada HTTP, para falha de rede não perder o pedido.

Arquivos: XML/PDF da carta são guardados com sufixo `_cce_NN` no nome, porque `guardar_xml` nunca sobrescreve e a carta cairia no mesmo caminho do XML da nota.

## Alternativas Consideradas

### Colunas no `DocumentoFiscal` (`carta_correcao_texto`, `carta_correcao_protocolo`)
**Por que rejeitada:** só guardaria a última carta; o histórico (que o contador precisa, e que a SEFAZ mantém) se perderia, e o XML/PDF de cada evento não teria onde morar.

### Tabela genérica `evento_fiscal` (cancelamento + carta + futuros)
**Por que rejeitada:** o cancelamento já vive em `DocumentoFiscal.status` e refatorá-lo agora é risco sem ganho; a inutilização já tem tabela própria. Uma tabela genérica exigiria colunas opcionais por tipo (YAGNI). Se um terceiro evento surgir, aí vale reavaliar.

## Consequências

### ✅ Benefícios
- Histórico completo, na ordem da SEFAZ; cada carta com seus arquivos.
- A nota permanece imutável (testado byte a byte em `test_carta_nao_altera_a_nota`).
- Mesmo desenho da inutilização — quem conhece uma entende a outra.

### ❌ Riscos/Custos
- Uma tabela e uma migration a mais (`t3u4v5w6x7y8`).
- `total_cartas_correcao`/`ultima_carta_correcao` são calculados por leitura (carrega a relação); irrelevante para 20 linhas.

### 🔄 Mitigation
- Migration idempotente (`has_table → return`) por causa do `create_all()` antes das migrations.

## Referências
- Spec: `.agent/specs/completed/TASK002-EmitirCartaCorrecao.md`
- Focus NFe: https://doc.focusnfe.com.br/reference/emitir_carta_correcao
- Código: `backend-fastapi/app/services/fiscal/carta_correcao.py`, `app/db/models/carta_correcao_fiscal.py`
- Precedente: `app/db/models/inutilizacao_fiscal.py`, `app/services/fiscal/inutilizacao.py`
- Progresso: `.agent/docs/progress/TASK002.md`

## Próximos Passos
- [ ] API intermediária StartBig: expor `POST /erp/fiscal/nfe/carta-correcao` (`{ref, correcao}`) repassando à Focus — bloqueia o teste em homologação.
