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

### O1 — Cancelar pela OS
1. Botão "Cancelar nota" no cartão de peças e no de serviço do `OSNotasCard`,
   só com nota AUTORIZADA e dentro da janela.
2. Reaproveita as rotas que já existem (justificativa de 15+ caracteres).
3. `os_notas.py` devolve `pode_cancelar` + o prazo que resta, para a tela
   não decidir sozinha.
4. Depois de cancelada, o cartão volta a "Não emitida" e a nota pode sair de novo.

### O2 — Enviar a nota ao cliente
1. **WhatsApp**: botão no cartão abre o `wa.me` com o telefone do cliente da
   OS e uma mensagem com número, valor e o link do PDF (no padrão do
   `PedidoDetalheModal`).
2. **E-mail**: conferir antes no contrato da plataforma
   (`contrato-api-fiscal-plataforma.md`) se a Focus manda o e-mail sozinha
   quando recebe o destinatário — se sim, é só preencher; se não, fica de fora
   desta rodada (SMTP próprio é outro projeto).
3. ⚠️ Conferir com `curl` se o link do PDF abre sem login antes de mandá-lo
   ao cliente.

### O3 — Saúde Fiscal sabe se a NFS-e está ligada na Focus
O caso da OS-158 (29/10: "Empresa não habilitada para emissão de NFSe").
1. **Plataforma primeiro**: rota que devolve se a empresa está habilitada na
   Focus para NFS-e e em qual ambiente.
2. ERP: novo item em `nfse/saude.py`, com a dica "admin › Passar para Nacional".
3. ERP novo com plataforma velha: o item fica "não dá para saber", nunca vermelho.

### O4 — Substituição da NFS-e (retificar)
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
