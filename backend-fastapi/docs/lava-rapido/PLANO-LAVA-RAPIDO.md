# Plano Completo — Segmento Lava-Rápido (Fase 1)

| Campo      | Valor                                                                             |
|------------|-----------------------------------------------------------------------------------|
| Status     | Plano fechado — SPEC-00 na Revisão 2 (12/11); as 🟡 restantes são de desenho técnico e se resolvem dentro de cada spec. Próximo passo: Spec 01A |
| Data       | 12/11/2026                                                                        |
| Branch     | `feat/segmento-lava-rapido` @ `c2228e88` (saiu da `feat/cfop-na-nota`)            |
| Documentos | `SPEC-00` (decisões) + 11 specs de implementação nesta pasta (escritas uma a uma, na ordem dos marcos) |

Este documento junta as specs num só plano: o que a fase 1 entrega, em que ordem construir, onde mexemos no código das lojas em produção e o que conferir antes de instalar no primeiro cliente. Ele **não** substitui as specs: cada linha aponta para a spec que tem os detalhes. Quando uma spec e este plano discordarem, vale a spec (e este plano deve ser corrigido).

---

## 1. O que a fase 1 entrega

**Objetivo (SPEC-00 §1):** o primeiro cliente roda um dia inteiro de pátio pelo sistema, e os segmentos em produção seguem **idênticos**.

O caminho de uma lavagem, e a spec de cada passo:

| # | Passo | Quem faz | Specs |
|---|-------|----------|-------|
| 1 | Ajusta a lista de portes e cadastra os serviços com o preço e a duração de cada porte | Dono | 02A, 02B |
| 2 | *(opcional)* Agenda o cliente; no dia, "Chegou" abre a OS preenchida | Atendente | 08A, 08B |
| 3 | Digita a placa; veículo e dono aparecem (ou cadastro mínimo se é novo; sem placa no tipo "Outros") | Atendente (responsável) | 01B, 03 |
| 4 | Escolhe os serviços (o preço vem do porte e pode ser alterado) e os lavadores (1 ou 2); a previsão aparece | Atendente | 01A, 02A, 02B |
| 5 | Marca as avarias e tira as fotos (no computador ou no celular pelo QR) | Atendente / lavador | 01A, 01B |
| 6 | Imprime o cupom (térmica) ou a via A4/PDF | Atendente | 01B, 03 |
| 7 | Acompanha o pátio: Aberto → Em andamento → Pronto → Finalizado, com um clique | Lavador / atendente | 04A, 04B |
| 8 | Ao marcar "Pronto", avisa o cliente pelo WhatsApp | Atendente | 04B |
| 9 | Finaliza com pagamento (caixa de hoje); comissão para os lavadores, dividida ou inteira conforme o dono configurou | Atendente | 01A, 01B (comissão) |
| 10 | *(se a loja emitir)* NFS-e da lavagem, NFC-e do produto | Atendente | 09 |
| 11 | *(se a loja ligar)* Plano mensal, pacote ou fidelidade baixam a lavagem | Atendente | 05A, 05B |
| 12 | Lembrete de retorno para quem sumiu | Atendente | 07 |
| 13 | *(lava-rápido maior)* Frota fechada no fim do mês | Financeiro | 06A, 06B |

Fora da fase 1 (SPEC-00 §7): agendamento online pelo cliente, OCR de placa, WhatsApp automático pela API, cobrança recorrente no cartão, cashback, lavador por item, vídeo, etapas de estética longa.

---

## 2. As specs

Tamanho é **estimativa relativa** (P/M/G), não prazo.

| Spec | Camada | O que entrega | ⚠️ Código compartilhado | Tamanho |
|------|--------|---------------|------------------------|---------|
| 00 | Documento | Decisões | — | — |
| 01A | Backend | Definição do segmento (4 tipos), 3 status, placa-ou-gerado, capacidades novas, lavadores da OS e comissão | ⚠️ registry, relatório de comissão (por capacidade) | G |
| 01B | Frontend | Segmento nas listas e no onboarding, porte e lavadores no formulário, 3 status, impressão térmica e A4 | ⚠️ constantes, formulário, filtros e impressão da OS | G |
| 02A | Backend | Portes da loja, preço e duração por porte, previsão de entrega | ⚠️ schemas de serviço (acréscimo) | M |
| 02B | Frontend | Configurações › Portes, grade no serviço, preço do porte na OS | ⚠️ cadastro de serviço, itens da OS | M |
| 03 | Frontend | Entrada rápida e cupom de entrada | ⚠️ criação de OS | M |
| 04A | Backend | Rota do pátio e troca rápida de status | — | P |
| 04B | Frontend | Quadro do pátio e WhatsApp | ⚠️ abas de Serviços | M |
| 05A | Backend | Planos, pacotes, fidelidade (opcional) | ⚠️ ganchos da OS | G |
| 05B | Frontend | Telas de planos e saldo na OS | ⚠️ cliente, OS | G |
| 06A | Backend | Frota / fechamento mensal | ⚠️ finalização de OS | M |
| 06B | Frontend | Telas de frota | ⚠️ cliente | M |
| 07 | A + B | Lembrete de retorno | ⚠️ Revisões (oficina) | P |
| 08A | Backend | Agenda: agendamentos, situações, capacidade, "Chegou" → OS | — | M |
| 08B | Frontend | Aba Agenda (dia e semana) e WhatsApp de confirmação | ⚠️ abas de Serviços | G |
| 09 | Conferência | Fiscal do segmento (NFS-e da OS, código de serviço, produto pelo PDV) | ⚠️ fiscal, só se faltar algo | P |

---

## 3. Ordem de implementação

### Marco 1 — Lava-rápido instalável (o que o primeiro cliente recebe)

```
00 ── 01A ─┬─ 01B ── 03
           └─ 02A ── 02B
```

**Pronto quando:** dá para ajustar os portes e cadastrar a tabela de preços do cliente, abrir uma OS pela placa em ≤ 30 s com o preço do porte e os lavadores, abrir uma OS de "Outros" sem placa, marcar avarias com foto, imprimir na térmica e em A4, finalizar com pagamento e ver a comissão nos lavadores; e informática, oficina, serigrafia, PDV e marcenaria passam na prova de não regressão.

### Marco 2 — Pátio

```
01A ── 04A ── 04B
```

**Pronto quando:** o quadro mostra o pátio real do dia, o status anda com um clique e o WhatsApp abre com a mensagem certa.

> Marcos 1 e 2 juntos são o **mínimo para o piloto** (o que todo sistema do ramo tem — SPEC-00 §3.2). O primeiro cliente pode receber o instalador aqui.

### Marco 3 — Agenda e fiscal

```
02A + 03 ── 08A ── 08B
01A ── 09            (conferência; independente, pode andar em paralelo)
```

**Pronto quando:** um agendamento da semana aparece no dia e na hora certos, passa da capacidade com aviso, e "Chegou" abre a OS preenchida; a NFS-e de uma lavagem sai em homologação com o código de serviço sugerido.

### Marco 4 — Fidelização e retorno (opcional por loja; para os próximos clientes)

```
02A ── 05A ── 05B
01A ── 07
```

**Pronto quando:** com a chave desligada nada muda; ligada, um plano mensal gera a conta a receber e baixa as lavagens da placa, um pacote consome o saldo, o cartão fidelidade dá a lavagem grátis, e reabrir/cancelar a OS devolve o saldo. O lembrete lista quem não volta há N dias.

### Marco 5 — Frota (lava-rápidos maiores — SPEC-00 C4)

```
02A ── 06A ── 06B
```

**Pronto quando:** as OS de uma transportadora no mês viram uma conta a receber com o extrato das placas.

### Piloto no primeiro cliente

Depois do Marco 2: roteiro manual de cada spec B, em sequência, no computador do balcão (e no celular do pátio, se ele usar). Os marcos 3 a 5 chegam a ele por atualização, com o banco preservado.

### Andamento

Uma linha por spec entregue, com a suíte medida depois dela.

| Spec | Data | Commit | Testes | Suíte depois |
|------|------|--------|--------|--------------|
| — | — | — | — | — |

---

## 4. Banco de dados

### 4.1. Migrações

Antes de cada uma, `alembic heads`: se outra branch tiver acrescentado migração, o `down_revision` acompanha (sem bifurcação; nunca `alembic merge`).

| Ordem | Spec | O que faz |
|-------|------|-----------|
| 1 | 01A | Tabela `ordem_servico_executores` (OS, funcionário) — lavadores |
| 2 | 02A | Tabelas `portes_veiculo` e `servico_precos_porte` (serviço, porte, preço em centavos, duração em minutos) |
| 3 | 08A | Tabela `agendamentos` |
| 4 | 05A | Tabelas de planos, pacotes, saldo e movimentos de fidelidade |
| 5 | 06A | Marcação de frota no cliente e tabela de fechamento (a definir na spec; preferir tabela nova a coluna em `clientes`) |

01B, 03, 04A, 04B, 07 e 09 **não** criam migração: usam `dados_adicionais`, `data_previsao`, `proxima_revisao_data` e `funcionario_id`, que já existem.

Regras para todas (PR8): decidir pela presença do schema **antigo**; `ADD COLUMN` só se faltar; nunca renomear o arquivo do banco; testar em **banco antigo copiado**.

### 4.2. Tabelas existentes alteradas

Nenhuma prevista (SPEC-00 F5). Se uma spec A precisar, registra aqui com a justificativa.

---

## 5. Onde mexemos no que já funciona (⚠️ PR1)

| Área do sistema | Specs | O que muda para os outros segmentos |
|-----------------|-------|-------------------------------------|
| Registry de segmentos | 01A | Nada (chaves novas opcionais: `portes`, status escondidos) |
| Formulário, filtros e botões de status da OS | 01B, 03 | Nada (status escondidos só onde o segmento declara; entrada rápida por capacidade) |
| Cadastro de serviço | 02B | Nada (grade de portes só com `preco_por_porte`) |
| Itens da OS (preço ao incluir serviço) | 02B | Nada (sem capacidade, preço = `servicos.valor`, como hoje) |
| Abas de Serviços | 04B, 08B | Nada (abas do quadro e da agenda só com `quadro_patio` / `agenda_servicos`) |
| Relatório de comissão | 01A | Nada (lavadores só com `executores_os`; sem lavador na OS, regra de hoje) — conferir comissão dos últimos 3 meses nos bancos copiados |
| Impressão da OS (térmica e A4) | 01B | Nada (porte, lavadores e avarias só aparecem quando existem) — snapshot antes × depois |
| Finalizar, reabrir, cancelar OS | 05A, 06A | Nada (ganchos vazios sem a chave/capacidade) |
| Revisões | 07 | **Oficina idêntica** (KM continua; data configurável só no lava-rápido) |

**Teste obrigatório antes de qualquer instalador:** aplicar as migrações num **banco copiado** de cada loja em produção e conferir: nenhuma linha muda; telas de OS, Serviços e Revisões iguais; comissão e CMV do mês iguais.

---

## 6. Peças novas que outros segmentos podem reaproveitar

| Peça | Spec | Serve também para |
|------|------|-------------------|
| Capacidade `preco_por_porte` + vocabulário `portes` | 01A, 02A | Estética automotiva, pet shop (porte do animal), qualquer preço por categoria do objeto |
| Status escondidos por segmento | 01A | Qualquer segmento que não use "Aguardando peças" |
| Quadro do pátio (`quadro_patio`) | 04A, 04B | Oficina (pátio de carros), assistência (bancada) |
| Botão WhatsApp com texto configurável | 04B | Qualquer OS ("seu aparelho está pronto") |
| Planos, pacotes e fidelidade | 05A, 05B | Qualquer serviço recorrente |

---

## 7. Permissões e cargos

| Chave | Spec | Libera |
|-------|------|--------|
| `servico` (de hoje) | 01–04, 07 | Abrir OS, quadro, vistoria |
| `view_` / `manage_planos` | 05A | Ver / vender e cancelar planos e pacotes |
| `manage_frota` | 06A | Fechamento mensal |

Linhas novas da matriz de cargos com `segmento: 'lava_rapido'` (mecanismo que já existe). Sugestão: **Dono** (tudo), **Atendente** (OS, quadro, caixa, planos), **Lavador** (quadro e vistoria).

---

## 8. Antes do piloto (checklist)

**Técnico**
- [ ] Marcos 1 e 2 completos, com todas as provas de não regressão.
- [ ] Suíte de referência medida na `c2228e88` antes da Spec 01A (backend `pytest test/`, frontend `vitest` + `npx vue-tsc --noEmit` — o `npm run build` não roda o `vue-tsc`).
- [ ] Testes de API com `TestClient(app)` **sem** `with`.
- [ ] Migrações testadas em bancos copiados das lojas em produção.
- [ ] `npm run build:sidecar` e conferência do teto do PyArmor.
- [ ] Instalador gerado **desta branch** e testado sobre banco existente e em instalação nova (onboarding escolhendo "Lava-Rápido").

**No cliente**
- [ ] Respostas da SPEC-00 §10.
- [ ] Tabela de preços cadastrada (serviços × portes, com duração).
- [ ] Funcionários (lavadores) e comissão no cargo.
- [ ] Impressora térmica testada com o cupom de entrada.
- [ ] Celular do pátio abrindo a vistoria pelo QR (mesma rede do servidor).
- [ ] Texto do WhatsApp ajustado em Configurações.
- [ ] Contador definiu o enquadramento da NFS-e (se emitir).
- [ ] Backup do banco antes de instalar.

**Roteiro do piloto (um dia real)**
1. Cliente novo (placa nova, cadastro mínimo) e cliente que volta (placa conhecida).
2. Um carro de cada porte; uma moto; (um caminhão, se atender).
3. Avaria marcada com foto no celular; cupom impresso.
4. Quadro: três veículos ao mesmo tempo, status andando; WhatsApp de "pronto".
5. Finalização com dinheiro, PIX e cartão; relatório de comissão do lavador no fim do dia.

---

## 9. Índice dos documentos

| Arquivo | Conteúdo |
|---------|----------|
| `SPEC-00-DECISOES-LAVA-RAPIDO.md` | Princípios, pesquisa de mercado, decisões, perguntas ao cliente |
| `SPEC-01A` / `SPEC-01B` | Fundação do segmento |
| `SPEC-02A` / `SPEC-02B` | Preço e duração por porte |
| `SPEC-03` | Entrada rápida e cupom |
| `SPEC-04A` / `SPEC-04B` | Quadro do pátio e WhatsApp |
| `SPEC-05A` / `SPEC-05B` | Planos, pacotes e fidelidade |
| `SPEC-06A` / `SPEC-06B` | Frota |
| `SPEC-07` | Lembrete de retorno |
| `SPEC-08A` / `SPEC-08B` | Agenda |
| `SPEC-09` | Fiscal do segmento (conferência) |
