# NFS-e — fase 2: deixar completa (plano de implementação)

Escrito em 28/10/2026, depois de F1–F4 (`docs/nfse-plano.md`). Branch do ERP:
`feat/nfse` (no GitHub até b71d4149). Plataforma: `main` (F2 + franquia, já no ar).

O que a fase 1 deixou de fora, e esta fase fecha:

| # | Bloco | ERP | Plataforma (server) | Plataforma (web/admin) |
|---|---|---|---|---|
| G1 | Saldo da franquia na tela | ✔ | — (rota já existe) | — |
| G2 | "Emitir mesmo assim" na NF-e e na NFC-e | ✔ | — (já aceita o cabeçalho) | — |
| G3 | Configuração da NFS-e (decisões do contador) | ✔ | — | — |
| G4 | NFS-e avulsa (sem OS) | ✔ | — | — |
| G5 | NFS-e na marcenaria (instalação, D8) | ✔ | — | — |
| G6 | Rota municipal (cidade por cidade) | ✔ | ✔ | ✔ |
| G7 | Saúde fiscal e suporte da NFS-e | — | ✔ | ✔ |
| G8 | ESLint (pendência à parte, `eslint-quebrado-pendente`) | ✔ | — | — |
| G9 | Homologação, canário e release | ✔ | ✔ | — |

Ordem proposta: **G9a (homologação da Nacional) primeiro**, porque valida o
payload da fase 1 antes de construir em cima dele. Depois G1 → G2 → G3 → G4 →
G5 → G6 → G7 → G8 → G9b (release). G1 e G2 são independentes da NFS-e e podem
ir antes, se a franquia começar a cobrar (1º/11) antes da homologação.

---

## 0. Regras de sempre (valem para todos os blocos)

| # | Regra |
|---|---|
| R1 | Tudo atrás do módulo da licença (NFSE para a nota de serviço; NFE/NFCE para o que for delas). Sem o módulo, a tela não muda. |
| R2 | Mudança aditiva. As fotografias de payload da NF-e/NFC-e (F0 do fiscal) continuam idênticas. |
| R3 | ERP novo com plataforma velha não quebra (rota 404 vira mensagem); plataforma nova com ERP velho não muda nada. |
| R4 | Migrations em linha a partir de `n5f0s3rv1c01`, decidindo pela presença do schema antigo, testadas em banco copiado. |
| R5 | `.py` < 64 KB (PyArmor trial). Código novo da NFS-e em `services/fiscal/nfse/`. |
| R6 | Nota de teste só em homologação. |
| R7 | Front no padrão do sistema: `Base*` de `shared/components/ui`, módulo `fiscal/` (components, composables, services, types), TanStack Query, Zod nos formulários. |

---

## G1 — Saldo da franquia na tela (todas as notas)

**Por quê:** a partir de 1º/11 a plataforma cobra R$ 1 por nota acima de 70 (cartão)
ou para na 70ª (PIX). O lojista precisa ver isso ANTES de emitir.

**Plataforma:** nada. `GET /erp/fiscal/franquia` já existe e não exige módulo
(`docs/integracao-erp-local.md` 13.4.1).

**ERP backend:**
- `client_startbig.consultar_franquia()` → dict (ou `{}` se a rota não existir:
  plataforma velha).
- `GET /fiscal/franquia` (sem trava de módulo, só usuário) repassando a resposta.
  Arquivo: `api/v1/endpoints/fiscal_franquia.py` (pequeno, não engorda `fiscal.py`).

**ERP front:**
- `fiscal/components/shared/FranquiaFiscalCard.vue`: "74 de 70 notas no mês ·
  4 extras (R$ 4,00 no dia 1º)"; com PIX, "restam 3 de 70". Barra no estilo da
  "Saúde Fiscal".
- No cabeçalho das abas NF-e, NFC-e e NFS-e (ao lado de "XMLs do período").
- Composable `useFranquiaFiscalQuery` (staleTime 1 min; invalida após emitir).
- Aviso no PDV quando `restantes <= 5` (só aviso, não trava: quem trava é a plataforma).

**Testes:** client sem a rota → `{}`; card com cartão/PIX/vigente=false.

---

## G2 — "Emitir mesmo assim" na NF-e e na NFC-e

**Por quê:** a plataforma devolve 409 `NOTA_DUPLICADA_SUSPEITA` também para NF-e
e NFC-e (com destinatário). Hoje o ERP (com a F4) já mostra a mensagem, mas o
documento fica NAO_TRANSMITIDA e não há como confirmar.

**ERP backend** (mesmo desenho da NFS-e, F4):
- `emitir_nfe` / `emitir_nfce` no client com `confirmar_duplicidade` (cabeçalho).
- `nfe_venda.py`, `nfe_os.py`, `nfce.py`: se `codigo == NOTA_DUPLICADA_SUSPEITA`
  → 409 sem gravar documento (o número reservado volta? **não**: a NF-e reserva
  número ANTES de enviar — ver abaixo).
- ⚠️ NF-e/NFC-e reservam numeração antes de transmitir. O 409 da plataforma
  acontece antes da SEFAZ, então o número NÃO foi usado: a reserva tem de ser
  desfeita no mesmo rollback (o `_handle_db_transaction` desfaz a reserva junto,
  porque ela é UPDATE na mesma transação — **conferir em teste**). Se não
  desfizer, sobra buraco a inutilizar.
- Rotas de emissão aceitam `confirmar_duplicidade` (query).

**ERP front:** o modal de emissão de NF-e (`FiscalEmitirNFeModal`), a venda
(`FiscalFechamentoSection`) e o PDV (NFC-e com CPF) tratam o 409 como o
`NfseEmitirModal`: aviso + "Emitir mesmo assim".

**Testes:** fotografias de payload intactas; 409 não deixa documento nem buraco
de numeração; confirmação manda o cabeçalho.

**Entrega G1 (28/10, 0c8506e7):** `consultar_franquia` + `GET /fiscal/franquia`;
`FranquiaFiscalCard` nas abas NF-e, NFC-e e NFS-e; emitir NF-e, lote e NFS-e
atualizam o saldo.

**Entrega G2 (28/10):**
- `nucleo.recusar_se_nota_repetida` + `except HTTPException: raise` em
  `nfe_venda`, `nfe_os` e `nfce`. Teste ponta a ponta: o contador **continua em
  10** depois da nota repetida (rollback desfaz a reserva) e nenhum documento
  fica. Confirmar reenvia com o MESMO número (11).
- `confirmar_duplicidade` nas rotas `/fiscal/emitir/nfe` e `/emitir/nfce` e nos
  clients (cabeçalho só quando confirmado).
- Front: `utils/notaRepetida.ts` (um lugar só, também usado pela NFS-e); aviso em
  toast com "Emitir mesmo assim" no modal do Centro Fiscal, no modal da venda e
  no PDV. Nenhuma tela mudou de layout.
- O lote (`emitir/nfe/batch`) não confirma: a venda repetida aparece no
  resultado como ERRO com a mensagem, sem número queimado.
- Fakes dos testes antigos ganharam o parâmetro novo (só assinatura).

---

## G3 — Configuração da NFS-e (as decisões do contador viram opção)

Em vez de esperar o contador de cada loja, as decisões viram configuração com o
padrão seguro, e o contador escolhe.

**ERP backend:**
- Migration `n5f0s3rv1c02`: em `empresa_fiscal_settings`:
  - `nfse_reter_iss_pj` BOOLEAN default 0 (D5: tomador PJ retém ISS?);
  - `nfse_uma_nota_por_codigo` BOOLEAN default 0 (D2: OS com códigos diferentes →
    uma nota por código em vez de pendência);
  - `nfse_ibs_cbs_padrao_cst` / `nfse_ibs_cbs_padrao_cclass` VARCHAR NULL (D6:
    padrão de IBS/CBS quando o serviço não tem).
  - (já existem: `regime_tributacao_iss`, `prefeitura_login/senha`).
- `payload.py`: usa as opções (retenção → `tipo_retencao_iss` 2 quando tomador
  PJ e a opção ligada; IBS/CBS padrão).
- D2 com a opção ligada: `emissao_os.py` emite uma DPS por código nacional, cada
  uma com `ref os-<n>-nfse-<codigo>`; a trava passa a ser por (OS, código).
- `GET/PUT /fiscal/nfse/configuracao` (módulo NFSE).

**ERP front:** seção "NFS-e" na configuração fiscal (ou um card na aba NFS-e):
regime especial, retenção, uma nota por código, IBS/CBS padrão — cada campo com
`ajuda` explicando e "pergunte ao seu contador".

**Testes:** payload com e sem cada opção; OS com 2 códigos vira 2 notas.

**Entrega G3 (28/10):**
- Migration `n5f0s3rv1c02`:
  - `empresa_fiscal_settings`: `nfse_reter_iss_pj`, `nfse_uma_nota_por_codigo`,
    `nfse_ibs_cbs_cst` e `nfse_ibs_cbs_cclass`, nascendo 0/NULL, ou seja, o
    comportamento da fase 1;
  - **`documento_fiscal.codigo_verificacao`**, porque com várias NFS-e na mesma
    OS o espelho da OS guardava uma só. `_aplicar_resultado` grava o campo quando
    vem.
- `payload.py`:
  - retenção `2` só quando a opção está ligada **e** o tomador é PJ;
  - `consumidor_final` passa a ser 0 para tomador PJ;
  - IBS/CBS do serviço, ou o padrão da configuração;
  - parâmetro `itens` para montar a nota de um grupo.
- `completude.py` devolve os **grupos por código**: sem a opção, códigos
  diferentes são pendência, como antes; com a opção, um grupo por nota.
- `emissao_os.py` passa a aceitar `codigo_nacional` (com vários grupos, sem ele →
  422 `NFSE_ESCOLHA_O_CODIGO`). Trava e tentativas por `papel="NFSE:<código>"`,
  `ref os-<n>-nfse-<código>`, desconto rateado por grupo. **OS de um código fica
  idêntica** (ref `os-<n>-nfse`).
- O preview devolve `notas[]` (com `ja_emitida`), e `dps` continua sendo a
  primeira.
- `GET/PUT /fiscal/nfse/configuracao` (módulo NFSE, permissão de serviço).
- Front:
  - "Configuração" na aba NFS-e (`NfseConfiguracaoModal`). O CST é digitado com
    3 dígitos, porque a lista `CST_IBS_CBS_OPTIONS` do sistema é provisória e usa
    2;
  - modal de emissão com "Emitir esta" por código;
  - a `NfseSection` da Empresa também nunca foi montada; a configuração ficou na
    aba NFS-e.

---

## G4 — NFS-e avulsa (sem OS)

**Por quê:** serviço que não passou por OS (consultoria, aula, o próprio MEI do
Alan que hoje emite pelo portal).

**ERP backend:**
- `nfse/avulsa.py`: `emitir_nfse_avulsa(dados)` — tomador (cliente cadastrado
  ou digitado), serviço do catálogo (com código nacional/NBS) ou código digitado,
  descrição, valor, desconto. Reusa `montar_dps` (extrair de `montar_dps_os` a
  parte que não depende da OS).
- `documento_fiscal.origem_tipo = "AVULSA"` (já é String(15)); `ref nfse-av-<uuid8>`.
- Rotas `POST /fiscal/nfse/avulsa/preview|emitir`.
- Completude própria (CNPJ/IBGE do prestador, código, valor, documento do
  tomador quando a cidade exigir — ver G6).

**ERP front:** na aba NFS-e, "Emitir NFS-e" passa a ter duas abas: "De uma OS" e
"Avulsa" (formulário com `ClienteBusca` existente, `CodigoFiscalBuscaInput` para
código e NBS, `BaseMoneyInput`).

**Testes:** payload avulso; tomador digitado; lista mostra a origem "Avulsa".

**Entrega G4 (28/10):**
- `payload.py`: a parte comum da DPS foi extraída para `_dps_comum`, e
  `montar_dps_os` e `montar_dps_avulsa` passaram a usá-la (a NFS-e da OS saiu
  igual: os 22 testes dela passam). Entrou `tomador_digitado` (CPF ou CNPJ pelo
  tamanho; sem documento, sem tomador).
- `nfse/avulsa.py`:
  - serviço do catálogo (`servico_id`), com códigos digitados que valem por cima;
  - pendências nomeadas;
  - `origem_tipo="AVULSA"`, `ref nfse-av-<8 hex>`, sem trava de origem (o clique
    duplo é segurado pela nota repetida da plataforma);
  - a nota repetida não grava documento.
- `POST /fiscal/nfse/avulsa/preview|emitir` (módulo NFSE).
- ZIP do contador rotula "Avulsa" (antes sairia "Venda None").
- Front: botão "NFS-e avulsa" na aba NFS-e (`NfseAvulsaModal`), com código e NBS
  pela busca, NBS sugerido, valor e desconto (em reais na tela, centavos na API),
  tomador opcional, conferir → emitir. A lista mostra "Avulsa" no lugar da OS.
- Não entrou a busca de cliente cadastrado: o componente da OS mistura cliente e
  objeto. O tomador é digitado.

---

## G5 — NFS-e na marcenaria (D8: a instalação como serviço)

**Hoje:** `instalacao_modo` = EMBUTIDA (no preço dos móveis da NF-e) ou FORA (fora
do sistema). A OS da marcenaria recusa NFS-e (`OS_DA_MARCENARIA`).

**ERP backend:**
- `instalacao_modo` ganha `NFSE` (só valor novo no enum Python; a coluna é
  String(10), sem migration) e `configuracoes_marcenaria.servico_instalacao_id`
  (migration `m4rc3n5f5e01`): o serviço do catálogo com o código nacional da
  instalação (o contador confirma; candidato: 14.06.01 / 07.xx).
- `nfse/marcenaria.py`: a NFS-e da instalação de UMA entrega (mesma unidade do
  faturamento dos móveis): valor = fatia da instalação daquela entrega (o mesmo
  rateio acumulado de `adaptador_marcenaria`), local da prestação = município
  da OBRA (endereço da obra do orçamento → `codigo_ibge`), não o da loja.
- Com `NFSE`, o adaptador da NF-e passa a tratar a instalação como FORA (não vai
  para o `vOutro`), para não cobrar duas vezes.
- Trava por entrega: tabela `marcenaria_moveis_faturamento` ganha
  `nfse_documento_id` (migration) — uma NFS-e de instalação por entrega.
- A recusa `OS_DA_MARCENARIA` fica só para quem não está em modo NFSE.

**ERP front:** Configurações › Marcenaria: terceira opção de instalação "Nota de
serviço (NFS-e)" (só aparece com o módulo NFSE) + escolha do serviço; aba Entrega
da OS: botão "Emitir NFS-e da instalação" ao lado da NF-e da entrega.

**Testes:** fotografia da NF-e da marcenaria **idêntica** nos modos EMBUTIDA/FORA;
em NFSE, NF-e sem a instalação e NFS-e com a fatia certa; soma das fatias =
instalação total.

---

## G6 — Rota municipal (cidade por cidade)

**Por quê:** empresa NÃO MEI numa cidade que não usa o emissor nacional para
todas (Iguatu é uma) emite pelo sistema da prefeitura. A Focus faz a ponte por
`/v2/nfse` — outro formato de JSON.

### Plataforma (server)
- **Prisma** (migration `db:push`):
  - `EmpresaFiscalConfig.nfseRota` String? — `NACIONAL` | `MUNICIPAL` | null.
  - Modelo novo `MunicipioNfse` (`codigoIbge` PK, `nome`, `uf`,
    `rotaNaoMei` `NACIONAL`|`MUNICIPAL`|`DESCONHECIDA`, `exigeLoginPrefeitura`
    Boolean, `observacao`, `atualizadoEm`, + cache dos campos da Focus abaixo).
- **Focus:** `consultarMunicipio(ibge)` → `GET /v2/municipios/{ibge}` (campos:
  `nfse_habilitada`, `status_nfse`, `provedor_nfse`, `requer_certificado_nfse`,
  `possui_ambiente_homologacao_nfse`, `possui_cancelamento_nfse`,
  `*_obrigatorio_nfse`). E `emitirNfse/consultarNfse/cancelarNfse` em `/v2/nfse`.
- **Ativação:** `rotaNfseDaAtivacao` passa a consultar `MunicipioNfse` para não
  MEI: `MUNICIPAL` → `habilita_nfse: true` (+ `login_responsavel`/
  `senha_responsavel` quando a cidade exige; vêm do ERP, nunca em log) e NUNCA
  `habilita_nfsen_producao`; `NACIONAL` → como MEI; `DESCONHECIDA` → continua
  `MUNICIPAL_PENDENTE`. Grava `nfseRota` na ficha.
- **Emissão:** `/erp/fiscal/nfse/emitir` escolhe pela `nfseRota` da ficha:
  NACIONAL → `/nfsen` (como hoje); MUNICIPAL → `/nfse`. O ERP manda o MESMO
  payload (DPS) e a plataforma TRADUZ para o formato municipal num
  `focus-nfse-municipal.mapper.ts` — mesma regra da NF-e: a tradução mora na
  fronteira com a Focus, e o ERP não precisa saber qual rota a cidade usa.
  Tabela de tradução (DPS → municipal): `cnpj_prestador`→`prestador.cnpj`,
  `inscricao_municipal_prestador`→`prestador.inscricao_municipal`,
  `codigo_municipio_emissora`→`prestador.codigo_municipio`, tomador `*_tomador`
  → `tomador{…, endereco{…}}`, `codigo_tributacao_nacional_iss`[0:4] →
  `servico.item_lista_servico`, `codigo_tributacao_municipal_iss` →
  `servico.codigo_tributario_municipio`, `descricao_servico`→`discriminacao`,
  `valor_servico`→`valor_servicos`, `tipo_retencao_iss`≠1 → `iss_retido`,
  `percentual_aliquota_relativa_municipio`/100 → `aliquota`,
  `codigo_opcao_simples_nacional`≠1 → `optante_simples_nacional`,
  `natureza_operacao` "1" (tributação no município).
  Resposta municipal → `ResultadoNfse` (mesmo contrato; `codigo_verificacao`,
  `numero`, `url`).
- **Exigências para o ERP:** `GET /erp/fiscal/nfse/municipio` → rota da ficha +
  os `*_obrigatorio_nfse` da cidade (cache em `MunicipioNfse`, renovado 1×/dia).
  O ERP usa na completude (CNAE obrigatório, código municipal obrigatório…).
- Testes: tradução (fotografia), escolha da rota, ativação MUNICIPAL nunca liga
  a Nacional, login/senha fora do log.

### Plataforma (web/admin) — telas novas
1. **"Municípios NFS-e"** (`apps/web/src/app/fiscal/municipios/`): lista das
   cidades dos clientes com NFSE, com o que a Focus diz (status, provedor,
   homologação, cancelamento, campos obrigatórios) e o que NÓS decidimos
   (`rotaNaoMei`, exige login, observação). Botão "Atualizar da Focus" por cidade.
   É onde o suporte registra "Iguatu: não MEI vai pela municipal".
2. **Perfil do cliente › Fiscal:** mostrar `nfseRota` e o motivo; permitir trocar
   a rota manualmente (com confirmação: troca reconfigura a empresa na Focus).

### ERP
- Configuração NFS-e (G3) ganha login/senha da prefeitura (campos já existem em
  `empresa_fiscal_settings`), enviados na ativação só quando a cidade exige.
- Completude lê `GET /erp/fiscal/nfse/municipio` (com cache local; sem
  resposta, cai nas regras da Nacional — não trava a loja por falta de internet
  na conferência).
- Cadastro do serviço: `codigo_tributacao_municipio` (já existe) passa a ser
  cobrado quando a cidade exigir; o `cnae` idem.

---

## G7 — Saúde fiscal e suporte (plataforma)

**Server:** `fiscal-saude.service.ts` inclui NFS-e: rota, última NFS-e,
rejeições do mês por `codigo_erro`, município sem `status_nfse = ativo`.
**Web:** painel "Saúde fiscal" do cliente mostra a linha da NFS-e; censo
(`npm run fiscal:censo`) conta NFS-e.
**ERP:** nada (o painel é do suporte).

---

## G8 — ESLint (pendência anotada, fora da NFS-e)

Migrar `frontend/.eslintrc.cjs` → `eslint.config.js` (flat config, ESLint 9 +
eslint-plugin-vue 10 + typescript-eslint), mantendo as regras e o override da
marcenaria (`no-restricted-html-elements`). Branch própria. A primeira execução
vai apontar avisos antigos: corrigir só erros reais; avisos ficam listados.

---

## G9 — Homologação, canário e release

**G9a (antes de G1–G6):**
1. Alan: módulo NFSE na licença; XML de uma NFS-e do portal (série, IBS/CBS MEI).
2. Ajustar o payload da Nacional pelo XML (fotografia nova).
3. Sidecar + instalador da `feat/nfse`; homologação: emitir, consultar, cancelar.
4. Uma NFS-e real de valor baixo, conferida no nfse.gov.br.

**G9b (no fim):** canário em uma loja que não usa NFS-e (prova de que nada mudou
para ela) + a do Alan; depois merge na branch de release (ver `exe-por-branch`).

---

## Pendências com o Alan / contador

1. XML de uma NFS-e do portal (G9a).
2. Contador: retenção de ISS, IBS/CBS padrão do MEI/Simples, código nacional da
   instalação de móveis (G3, G5).
3. Primeiro cliente não MEI que precise da rota municipal: cidade e provedor (G6).
