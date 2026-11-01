# CFOP na hora da nota + o que falta nas "Notas desta OS" — plano (01/11/2026)

Origem: conversa com o Alan em 01/11. Na marcenaria, o sistema antigo do
cliente pede só o CFOP na hora de emitir; aqui o CFOP mora no cadastro do
produto, e trocar numa nota exige mexer no cadastro e lembrar de voltar. Junto
vieram os pendentes da OS levantados desde a M5 (`nfse-melhorias-plano.md`).

Regras de sempre:
- tudo aditivo: **sem o campo novo, a emissão é idêntica à de hoje**;
- o pior desfecho é a nota **aceita e errada** — cada atalho recusa ou avisa,
  nunca chuta (a regra de `services/fiscal/derivacao/__init__.py`);
- cada fase com testes, `vue-tsc` e o sidecar regerado; instalador sai da
  branch; canário antes de espalhar.

---

## Decisões do Alan (01/11)

| # | Decisão |
|---|---|
| D1 | Um CFOP **para a nota toda**, com pesquisa (número ou nome) |
| D1a | Nota que mistura grupos (peça sem ST 5102 + peça com ST 5405, comum na oficina): **um campo por grupo**, nunca um por item. Um CFOP só por cima de tudo levaria a peça com ST ao CSOSN 102 |
| D2 | O CSOSN/CST e a natureza da operação **acompanham** o CFOP escolhido, sozinhos |
| D3 | Vale em **toda NF-e de venda e de OS** |
| D3a | Marcenaria: o CFOP de cada papel (5922 simples faturamento, 5116/5117 remessa) **continua fixado por padrão**, mas "se precisar editar, facilita" — onde houver opção na mesma família (5116↔5117), dá para trocar |
| D4 | A troca vale **só para aquela nota**; caixinha "usar como padrão" grava no cadastro |

---

## Como está hoje (código, 01/11)

- `EmissaoNFeRequest` (`schemas/fiscal/emissao.py:13`) recebe só `venda_id` ou
  `numero_os` — não há como informar CFOP.
- O CFOP sai do `cfop_padrao` do produto; fora do estado o resolver troca o 5
  pelo 6 (`tax_engine/resolver.py:242`, `derivar_cfop_operacao`).
- A prévia (`preview_nfe` em `endpoints/fiscal_emissao.py`) já devolve
  `cfop` e `cst_csosn` por item (`EmissaoPreviewItem`) — só não deixa editar.
  Tela: `modules/fiscal/components/emitir/FiscalEmitirNFeModal.vue`.
- `NATUREZA_POR_CFOP` (derivacao/cfop.py) já liga CFOP → natureza.
- "Notas desta OS" (`OSNotasCard.vue` + `services/fiscal/os_notas.py`) é a
  mesma tela em todos os segmentos com OS (Assistência, Oficina, Serigrafia,
  Eletricista, Outros). Peças → NF-e, mão de obra → NFS-e, desconto dividido
  na proporção. Marcenaria: móveis pela aba Entrega; instalação pela NFS-e (G5).
- Cancelar já existe nos dois lados (`eventos/consulta_cancelamento.py` para
  NF-e; `POST /fiscal/nfse/documentos/{id}/cancelar`), **só não pela OS**.
- Enviar ao cliente: não existe. Padrão de WhatsApp a copiar:
  `compras/pedidos/components/PedidoDetalheModal.vue`.

---

## Branch

`feat/cfop-na-nota`, saída da `feat/nfse-melhorias` (571976c2) **+ cherry-pick
do 8d98ffaa** (fix da NFS-e: CEP do tomador e DANFSe do S3), deixando de fora
o 37a0e7ed (CFOP ST interestadual, espera o contador).

⚠️ O 37a0e7ed mexe em `derivacao/cfop.py` e `tax_engine/resolver.py`, os mesmos
arquivos da fase C1. Quando o contador responder, juntar com cuidado (rebase,
rodar `test_derivacao_interestadual.py` e `test_resolver_interestadual.py`).

---

## Fases

### C1 — Backend: CFOP escolhido na emissão ✅ (01/11)
- **Regras puras** em `derivacao/troca_cfop.py`: só se troca dentro da mesma
  FAMÍLIA (interna 5101/5102/5103/5104/5405; fora contribuinte 6101–6104; fora
  não contribuinte 6107/6108; entrega futura x116/x117). O resto fica travado:
  5922, ST como substituto (6401/6403/6404 — decide o perfil e a tabela ainda
  espera o contador), 5933. Família diferente por construção também garante o
  1º dígito certo (o destino continua decisão do motor).
- **D2**: entrar no 5405 ou sair dele muda a situação junto (102↔500 no
  Simples, 00↔60 no normal); a natureza segue o CFOP quando a nota fica com
  um CFOP só.
- **Request**: `EmissaoNFeRequest.trocar_cfop` (`{"5102": "5101"}`, pelo CFOP
  SUGERIDO) e `cfop_como_padrao`. Vale na prévia e na emissão, venda e OS.
  Ausente = a nota de sempre (teste: payload igual).
- Aplicada no resolver (`resolver_aliquotas_venda`), DEPOIS de toda a
  derivação. Troca de um CFOP que a nota não tem é recusada (a conferência
  ficou velha).
- **Prévia** ganha `grupos_cfop` (um por CFOP sugerido, com as opções da
  família). Não precisou de rota `GET /fiscal/cfops`: as opções de cada grupo
  são no máximo 5 e já vêm ali.
- **Rastro**: coluna `documento_fiscal.cfop_trocado` (JSON trocas + usuário),
  migration `c1cf0p7r0c01` (nova head; testada numa cópia do banco antigo).
  A **reemissão** de nota recusada repete a troca.
- **D4** só grava no cadastro PRÓPRIO do produto e só CFOP de venda.
- **Achado/corrigido**: a prévia da NF-e da OS (`POST /fiscal/preview/nfe`
  com `numero_os`) devolvia os itens do payload e a rota dava 500 — ninguém a
  chamava. Agora tem o formato da prévia da venda.
- NFC-e: a prévia volta com `grupos_cfop` vazio (o cupom não troca CFOP).

### C2 — Tela: campo de CFOP na conferência ✅ (01/11)
- `CfopDaNotaCampo.vue`: "CFOP desta nota" (BaseSelect com pesquisa); nota
  mista → um campo por grupo ("Itens 1, 3 (sugerido 5102)"); CFOP travado
  aparece com cadeado; aviso amarelo + caixinha D4.
- Centro Fiscal (`FiscalEmitirNFeModal`): o campo na conferência; trocou → a
  prévia recarrega; recusa → volta ao CFOP da prévia na tela.
- OS: o botão "Emitir NF-e das peças" do `OSNotasCard` transmitia direto, sem
  conferência. Agora confere pendências (`useEmitirFiscal().conferirOS`) e
  abre `ConferenciaNFeOSModal` (itens, valor, campo de CFOP, confirmar).
- **Fica de fora**: o botão "Emitir NF-e" do modal da VENDA
  (`sales/.../NotaFiscalSection.vue`) continua emitindo direto, sem
  conferência — para trocar CFOP de venda, pelo Centro Fiscal.

### C3 — Marcenaria (D3a) ✅ (01/11)
`trocar_cfop` na NF-e dos móveis (`nfe_marcenaria.py`, aba Entrega): venda
(5101/5102) troca na família interna; remessa 5116↔5117; 5922 travado (é o
papel da nota). O resolver já aplica a troca depois do `cfop_sufixo_forcado`,
então falta só o request da marcenaria e a tela da Entrega.

### O1 — Cancelar pela OS ✅ (01/11)
Feito: `os_notas.py` devolve `pode_cancelar` e `cancelar_ate` (NF-e: 24 h pela
mesma régua do cancelamento; NFS-e sem prazo nosso). O cartão mostra
"Cancelar" e "Dá para cancelar até…"; NF-e pelo `FiscalCancelarModal`, NFS-e
pelo `NfseCancelarModal`. **Achado**: o "Cancelar" da gaveta da NFS-e aberta
pela OS só fechava a gaveta — agora abre o cancelamento.

Plano original:
1. Botão "Cancelar nota" no cartão de peças e no de serviço do `OSNotasCard`,
   só com nota AUTORIZADA e dentro da janela.
2. Reaproveita as rotas que já existem (justificativa de 15+ caracteres).
3. `os_notas.py` devolve `pode_cancelar` + o prazo que resta, para a tela
   não decidir sozinha.
4. Depois de cancelada, o cartão volta a "Não emitida" e a nota pode sair de novo.

### O2 — Enviar a nota ao cliente ✅ WhatsApp (01/11)
Feito: `GET /ordens-servico/{n}/notas-fiscais/{id}/whatsapp` monta o texto
(número, OS, valor; NF-e com a chave de acesso e o portal; NFS-e com o link do
DANFSe quando ele é público e o código de verificação) e o celular com 55
(`telefone_whatsapp` de Compras). O cartão ganha "WhatsApp"; sem celular,
copia o texto. **Nunca** vai link de `api.startbig.com.br`: o PDF da NF-e
exige o token da loja e o cliente cairia num login. E-mail ficou de fora: o
contrato da plataforma não tem envio de e-mail.

Plano original:
1. **WhatsApp**: botão no cartão abre o `wa.me` com o telefone do cliente da
   OS e uma mensagem com número, valor e o link do PDF (no padrão do
   `PedidoDetalheModal`).
2. **E-mail**: conferir antes no contrato da plataforma
   (`contrato-api-fiscal-plataforma.md`) se a Focus manda o e-mail sozinha
   quando recebe o destinatário — se sim, é só preencher; se não, fica de fora
   desta rodada (SMTP próprio é outro projeto).
3. ⚠️ Conferir com `curl` se o link do PDF abre sem login antes de mandá-lo
   ao cliente.

### O3 — Saúde Fiscal sabe se a NFS-e está ligada na Focus ✅ (01/11, falta deploy)
Feito:
- **Plataforma** (`feat/nfse-habilitacao-erp`, 88e6332, **sem push/deploy**):
  `GET /erp/fiscal/nfse/habilitacao` devolve o item `nfse` do painel do
  suporte (rota, cidade e habilitação lidas na Focus) como `{estado, detalhe,
  rota}`. Testes: 217.
- **ERP**: `consultar_habilitacao_nfse` no cliente; a Saúde da NFS-e ganha
  "Ligada na emissora" (ok/atenção = pronta; problema = pendência com "fale
  com o suporte" e o detalhe técnico em letra pequena). Sem resposta (plataforma
  velha, rede fora, mock): o item não aparece — nunca vermelho.
- **Ordem de deploy**: plataforma antes do ERP (ERP novo com plataforma velha só
  não mostra o item).

Plano original:
O caso da OS-158 (29/10: "Empresa não habilitada para emissão de NFSe").
1. **Plataforma primeiro**: rota que devolve se a empresa está habilitada na
   Focus para NFS-e e em qual ambiente.
2. ERP: novo item em `nfse/saude.py`, com a dica "admin › Passar para Nacional".
3. ERP novo com plataforma velha: o item fica "não dá para saber", nunca vermelho.

### O4 — Substituição da NFS-e (retificar) ✅ (01/11, falta homologar)
Feito (`nfse/substituicao.py`, `POST /fiscal/nfse/documentos/{id}/substituir`):
- "Substituir NFS-e (corrigir)" na gaveta da NFS-e autorizada da OS (rota
  Nacional, com chave gravada): motivo (01–05, 99) e o porquê (15–255) → a
  emissão da OS de novo, com os três campos na DPS e `tentativa_anterior_id`
  na antiga. A gaveta passa para a nota nova.
- A antiga vira CANCELADA ("Substituída pela NFS-e nº X") só quando a nova é
  AUTORIZADA — no ato ou numa consulta depois (gancho no espelho da NFS-e).
- Substituta recusada: a antiga continua valendo, o cartão da OS continua
  nela, e substitui-se de novo pela antiga (o "Tentar de novo" da recusada
  manda para lá: `NFSE_ERA_SUBSTITUICAO`).
- Recusas: não autorizada, avulsa, instalação da marcenaria, rota municipal,
  sem chave ("use Consultar").
- De carona: o WhatsApp da NFS-e manda o link de consulta no portal (abre sem
  login, não expira) antes do PDF da emissora.

**Ainda a confirmar na 1ª homologação** (o código não depende disso, mas a
leitura sim): a nota 26 tem `chave_acesso`; a Focus devolve a antiga como
"cancelado" numa consulta; o prazo da substituição.

Pesquisa (01/11):
**O que a Focus tem** (campos da DPS Nacional,
campos.focusnfe.com.br/nfse_nacional/EmissaoDPSXml.html):
- `chave_nfse_substituida` (tag `chSubstda`, até 50): chave da NFS-e substituída;
- `codigo_justificativa_substituicao` (`cMotivo`): 01 desenquadramento do
  Simples, 02 enquadramento no Simples, 03 inclusão retroativa de
  imunidade/isenção, 04 exclusão retroativa, 05 rejeição pelo tomador (ou
  intermediário responsável), 99 outros;
- `motivo_substituicao` (`xMotivo`, 15–255 caracteres).
- Não há rota própria: a substituição é uma **emissão nova** (`POST /v2/nfsen`)
  com esses campos. A consulta não tem status "substituída".
- **Municipal**: nada de substituição na doc da Focus (e algumas prefeituras
  nem cancelam por webservice). Fica fora.

**Do nosso lado:**
- A plataforma não precisa mudar: o payload da NFS-e é `looseObject` e os
  campos extras passam para a Focus; e ela já traduz `chave_nfse` →
  `chave_acesso`, que o ERP grava no documento.

**Falta confirmar antes de codar (homologação):**
1. A nota 26 (OS-158) tem `chave_acesso` gravada? Sem a chave, não há como
   substituir.
2. A NFS-e antiga vira "cancelada" sozinha (evento de cancelamento por
   substituição do Sistema Nacional) ou fica autorizada? Decide se o ERP marca
   a antiga ao autorizar a nova.
3. Prazo da substituição (a doc não diz).

**Desenho proposto** (quando confirmar): botão "Substituir" na gaveta da
NFS-e autorizada → escolher o motivo (lista acima) e escrever o porquê → abre
a emissão da OS já preenchida, para corrigir; a nova nota leva os três campos
e aponta a antiga (`tentativa_anterior_id`).

Plano original:
Começa por **pesquisa**: como a Nacional e a Focus fazem a substituição (DPS
nova apontando a chave da anterior?), e o que a plataforma precisa expor.
Só vira código depois dessa resposta — fase separada.

### H — Homologação e entrega
1. OS **mista** (peça + serviço) do começo ao fim: NF-e + NFS-e, cancelar uma,
   emitir de novo, mandar por WhatsApp.
2. Nota com CFOP trocado e nota mista com dois grupos.
3. Sidecar + instalador da branch; canário (oficina do Alan) antes dos clientes.

---

## Ordem sugerida

C1 → C2 → O1 → (C3) → O2 → O3 → H. O4 corre em paralelo como pesquisa.

## Fora deste plano (anotado)
- `prefeitura_senha` em texto puro em `empresa_fiscal_settings`.
- G9a (homologação NFS-e da licença do Alan) — `nfse-fase2-plano.md`.
- CFOP ST interestadual (37a0e7ed) — aguarda contador.
