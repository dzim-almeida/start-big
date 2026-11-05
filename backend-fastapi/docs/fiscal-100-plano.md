# Plano: NF-e completa para quem vende para o Brasil todo

Escrito em 04/11/2026, na branch `feat/cfop-na-nota` (`ca25e40a`). Nada deste plano
foi implementado ainda.

**O problema:** o motor fiscal calcula ST, CFOP por UF e DIFAL, mas falta a parte que
o coloca em uso. O caso real é a marcenaria do Junior: 247 notas válidas de 2021 a
2026, das quais 161 (65%) são para empresas com IE de outros estados.

**Como foi levantado:** leitura do código e do banco antigo do Junior. Nenhuma nota de
teste foi emitida. As fases abaixo confirmam cada ponto com teste antes de corrigir.

**Regra de ouro:** nada novo muda a nota de quem já emite. Mudança de comportamento
nasce desligada, com uma opção da empresa.

---

## 0. O que "pronto" significa

| # | Critério de aceite |
|---|---|
| A1 | Criar e editar perfil tributário pela tela, sem mexer no banco |
| A2 | Vincular perfil a um produto, a vários de uma vez e pela planilha |
| A3 | Venda enviada para outro estado nunca sai como interna por falta de resposta |
| A4 | CE contribuinte, CE consumidor, UF com ST, UF sem ST e CPF de fora saem com CFOP, CSOSN e valores conferidos em homologação |
| A5 | Falta de CEST ou de alíquota de crédito é avisada antes de reservar número |
| A6 | A pré-visualização mostra CFOP, CSOSN, ST e total antes de emitir |
| A7 | Quem não ligou nada novo emite exatamente a mesma nota de antes (teste comparando o payload) |

---

## 1. Dados externos (F0): não é programação

**O que as notas antigas já responderam, sem precisar perguntar:** NCM dos móveis
(94036000, 94033000 e 94034000), para quais estados ele vende e quem compra.

**O que elas não respondem:** nenhuma nota traz ST calculada, CEST ou crédito do
Simples, e o contador já disse que a combinação usada estava errada. Copiar repetiria
o erro. Falta:

| # | Pergunta para o contador | Usado em |
|---|---|---|
| C1 | Qual alíquota de crédito do Simples (pCredSN) usar hoje? | Tributação padrão |
| C2 | Venda de móvel dentro do CE tem ST (5401 + 201) ou é 5101 + 101? | CFOP do produto |
| C3 | Para PI, MA, SP, MG, PE, BA, PR, PB e RN: tem ST para móvel? Qual MVA, alíquota interestadual e alíquota interna? | Regras do perfil |
| C4 | Qual CEST para cada NCM de móvel? (agregador indica 28.061.00, sem fonte oficial) | Regra por NCM |
| C5 | Esses estados cobram FCP sobre a ST de móvel? | Fase F4 |
| C6 | Materiais revendidos: CSOSN 102 ou 500? | Tributação padrão |
| C7 | Posso usar a série 2 enquanto a série 1 continua no sistema antigo? | Transição |

Antes de levar C3, C4 e C5, pesquisar no CONFAZ e nos regulamentos estaduais, para o
contador só conferir em vez de levantar tudo.

---

## 2. Tela de perfil tributário (F1): a trava principal

**Já existe no backend, com testes:** CRUD em `/fiscal/perfis-tributarios`, regras por
UF com fallback e `perfil_tributario_id` em `PUT /produtos/{id}/fiscal`.
**Não existe:** nenhuma referência a perfil no frontend.

1. **Fiscal › Configurações:** card e modal de perfil, no padrão do
   `FiscalTributacaoModal`, em linguagem de operador.
2. **Regras:** tabela com UF, tem ST, MVA, alíquota interestadual e alíquota interna.
   Campos técnicos (base dupla, FCP, exceção por NCM) ficam em "avançado".
3. **Regra obrigatória "demais estados":** é o fallback que o backend já exige. Sem
   dado do contador, a regra deve recusar a nota em vez de chutar. **Conferir:** hoje o
   schema exige alíquotas nela, e isso pode pedir um campo "não vender sem regra".
4. **Produto:** seletor de perfil no `DadosFiscaisSection`.
5. **Vínculo em lote (endpoint novo):** escolher por categoria ou NCM, ver quantos
   produtos serão afetados e confirmar, numa transação só.
6. **Planilha:** coluna opcional `PERFIL` em `importacao_planilha.py`, pelo nome. Nome
   desconhecido vira erro na linha.
7. **Erro da venda:** trocar "não possui perfil tributário" por uma mensagem com o
   caminho para resolver.

---

## 3. Venda para outro estado (F2): risco de nota errada

**Achado no código:** `_operacao_presencial` trata venda sem resposta como presencial,
e presencial é sempre interna (`tax_engine/resolver.py`). Venda para cliente do PI sem
essa resposta sai interna, com 5101 e sem ST, sem cair na trava do perfil. **Confirmar
com teste** o que o fechamento e a emissão enviam hoje.

A presencial continua válida: o comprador de fora que retira no balcão é venda interna.

1. **Opção da empresa, desligada por padrão:** "Vendo e envio para outros estados".
2. **Ligada:** NF-e de cliente de outra UF, sem resposta, vira pendência com uma
   pergunta: "A mercadoria vai para o cliente ou ele retira aqui?".
3. **Desligada:** nada muda.

---

## 4. Conferência antes de emitir (F3)

Hoje a conferência olha o CSOSN do cadastro (101), mas o motor o troca para 201 depois.
As travas certas só existem em `nfe_marcenaria.py`.

1. Mover `_pendencia_credito_simples` e `_pendencias_cest_da_st` para um módulo comum
   e usar também em `nfe_venda.py`, depois do cálculo e antes de reservar o número.
2. **ST sem CEST:** bloqueia para todos, se o teste em homologação confirmar a rejeição.
3. **101 sem alíquota:** bloqueia só com a opção da F2 ligada; nas demais lojas, vira
   aviso, porque hoje essa nota é emitida.
4. **Emissão em lote e botão direto:** conferir se passam pela mesma regra.
5. **Pré-visualização:** mostrar CFOP, CSOSN, base e valor da ST e total, com aviso
   claro quando a nota tiver ST.

---

## 5. FCP sobre a ST (F4): só se C5 confirmar

1. Migration com `percentual_fcp_st` na regra, seguindo a nota de migrations sem
   bifurcação e testando em banco antigo.
2. `icms_st.py`, consolidador, `itens.py` e `totais.py` calculam e enviam base,
   percentual e valor. Percentual zero não pode ser enviado: a SEFAZ rejeita.
3. Conferir os nomes dos campos em campos.focusnfe.com.br e o repasse na plataforma.

---

## 6. Dados de transporte (F5): baixa prioridade

Só 3 notas usaram transportadora e 2 usaram volumes. Entra depois da homologação:
transportadora, volumes e frete por conta do destinatário na NF-e. Nota de remessa
(5949, 6949, 6912) não entra: foram 4 itens em 5 anos.

---

## 7. IBS e CBS (F6): plano separado, atinge todos os clientes

Os campos existem no cadastro, mas não vão no payload da NF-e. Para o Simples, a LC
214/2025 dispensa o destaque em 2026 e a obrigação começa em 2027. A rejeição 1115
ficou sem data na NT 2025.002 v1.51, segundo fontes secundárias: confirmar no Portal
Nacional da NF-e. **Clientes do regime normal já têm a obrigação legal: verificar quem
emite hoje e tratar antes de 01/2027.** Não bloqueia a instalação do Junior.

---

## 8. Homologação e virada (F7)

Emitir em homologação e conferir o XML de cada caso:

| Caso | Esperado |
|---|---|
| CE, empresa com IE | C2 decide: 5101 + 101 ou 5401 + 201 |
| CE, consumidor | 5101 + 101 |
| Outro estado com ST, empresa com IE | 6401 + 201, com CEST e ST no total |
| Outro estado sem ST, empresa com IE | 6101 + 101 |
| Outro estado, CPF | 6107 + 101 |
| Material, dentro e fora | 5102 e 6102 |
| Cliente de fora retirando no balcão | Interna, com resposta explícita |
| Loja sem a opção ligada | Payload idêntico ao de antes |

**Virada:**
1. Rodar a suíte, regerar o sidecar e o instalador.
2. Backup do banco e instalação primeiro na loja canário.
3. No Junior: fiscal, perfil, vínculo em lote e 3 notas reais conferidas pelo contador.
4. Passar a NF-e para o nosso sistema e desligar o antigo. O contador deve avaliar as
   notas antigas, que usaram CFOP de ST sem ST calculada.

---

## 9. Ordem

| Ordem | Fase | Depende de |
|---|---|---|
| 1 | F2: teste que confirma o achado da venda presencial | Nada |
| 2 | F1: tela e vínculo do perfil | Nada |
| 3 | F2 e F3: opção da empresa e travas | F1 |
| 4 | F0: dados do contador | Pode correr em paralelo |
| 5 | F4: FCP sobre a ST | C5 |
| 6 | F7: homologação e virada | F0 a F4 |
| 7 | F5 e F6: transporte; IBS/CBS em plano próprio | Depois; F6 tem prazo próprio |
