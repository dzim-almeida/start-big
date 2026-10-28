# NFS-e — plano (Brasil todo)

Escrito em 28/10/2026. Nada codado ainda. Canário: a empresa do Alan
(66.544.279, MEI, Iguatu/CE). Hoje ela emite pelo portal nfse.gov.br.

## 0. Onde estamos

**Plataforma** (`Plataforma_admin/meu-projeto-fullstack`):
- O módulo `MODULO_NFSE = 'NFSE'` existe em
  `packages/database/src/repositories/modulo.repository.ts`, mas nada o usa.
- `RecursoFocus` (`common/focus-nfe/focus-nfe.service.ts`) só tem `'nfe' | 'nfce'`.
  Não há rota `/erp/fiscal/nfse*` (curl de 24/10: 404).
- A ativação (F2 do fiscal, `fiscal-onboarding.service.ts`) já cria e atualiza a
  empresa na Focus e liga `habilita_nfe` e `habilita_nfce` por API.

**ERP**:
- `servico_fiscal`: `codigo_servico_lc116`, `cnae`, `aliquota_iss`,
  `codigo_tributacao_municipio`, `c_class_trib`, `cst_ibs_cbs` e alíquotas IBS/CBS.
- `empresa.inscricao_municipal`.
- `empresa_fiscal_settings`: `rps_serie`, `rps_ultimo_numero`,
  `regime_tributacao_iss`, `prefeitura_login`/`senha`/`token_api`.
- `ordem_servico_nota_fiscal`: `emitir_nfse`, `status_nfse`, `numero_nfse`,
  `codigo_verificacao_nfse`, `url_nfse` e `mensagem_nfse`.
- `documento_fiscal.tipo_documento` (`String(5)`) já comporta `'NFSE'`.
- `verificar_itens_os_nfse` (completude) valida o serviço da OS.
- O checkbox `emitir_nfse` da `NotaFiscalSection.vue` existe, mas não emite nada.

**Buracos encontrados**:
- **Código IBGE do município.** A tela da empresa **mostra** o código
  (`AddressSection.vue`), mas o calcula na hora, a partir de cidade + UF, consultando
  a API do IBGE. Ela o envia (`useEmpresaFormProvider.ts:359`), mas **o backend não tem
  coluna e descarta o valor**, e o banco das lojas não o guarda. Por isso parece que
  ele "já existe". A NF-e não sentia falta disso porque a Focus resolve município e UF. A NFS-e
  Nacional exige `codigo_municipio_emissora` e `codigo_municipio_prestacao`
  (7 dígitos).
- **Código de tributação nacional** (`codigo_tributacao_nacional_iss`, 6 dígitos:
  item + subitem + desdobro da LC 116). O `codigo_servico_lc116` atual tem 4 dígitos
  e não traz o desdobro.
- **NBS** (`codigo_nbs`, 9 dígitos): não existe no cadastro do serviço.

## 1. O que a Focus oferece (doc.focusnfe.com.br, conferido em 28/10)

| | NFS-e Nacional | NFS-e municipal |
|---|---|---|
| Emitir | `POST /v2/nfsen?ref=` (assíncrono, 202 `processando_autorizacao`) | `POST /v2/nfse?ref=` |
| Consultar | `GET /v2/nfsen/{ref}` | `GET /v2/nfse/{ref}` |
| Cancelar | `DELETE /v2/nfsen/{ref}` (síncrono; `cancelado` ou `erro_cancelamento`) | `DELETE /v2/nfse/{ref}` |
| Flag na empresa | `habilita_nfsen_homologacao`, `habilita_nfsen_producao` | `habilita_nfse` |
| Numeração | `serie_nfsen_*`, `proximo_numero_nfsen_*` (a Focus calcula) | `serie_nfse_*`, `proximo_numero_nfse_*` |

- `habilita_nfse` e `habilita_nfsen_producao` **não podem estar ligados juntos**.
  Cada empresa tem **uma** rota em produção.
- O "eu aceito" do painel (que apareceu para MEI em Iguatu) **não tem campo na API**.
  A API aceita a flag direto. Isso vira responsabilidade nossa: a regra da §2
  substitui o aviso.
- A prefeitura sem certificado pode pedir `login_responsavel` e `senha_responsavel`
  (rota municipal).
- Campos obrigatórios da DPS Nacional que merecem atenção:
  - `codigo_opcao_simples_nacional`: 1 = não optante, 2 = MEI, 3 = ME/EPP;
  - `regime_especial_tributacao`: 0–6 ou 9;
  - `tributacao_iss`: 1 = tributável, 2 = imunidade, 3 = exportação, 4 = não incidência;
  - `finalidade_emissao`: 0;
  - `consumidor_final`;
  - `indicador_destinatario`;
  - `ibs_cbs_situacao_tributaria` e `ibs_cbs_classificacao_tributaria` (reforma);
  - os dados do tomador.

  A alíquota de ISS é preenchida pelo próprio sistema nacional quando o município
  aderiu. Fora disso, nós temos que mandá-la.

Referência completa dos campos: https://campos.focusnfe.com.br/nfse_nacional/EmissaoDPSXml.html

## 1.1 Como o mercado faz (pesquisa de 28/10: Omie, Bling, Conta Azul)

| O que eles fazem | O que adotamos |
|---|---|
| Omie: o cliente escolhe à mão o "Modelo de integração" (municipal × NFS-e Nacional) na configuração da empresa. | A rota é escolhida **sozinha** (§2). Só o caso desconhecido vai para o suporte. |
| Omie: **validador** que diagnostica o que falta e corrige em lote (serviços, IM, RPS). | A completude que já temos vira um "Verificar NFS-e" na configuração fiscal, com correção em lote dos serviços (F1). |
| Omie e Bling: código de tributação e NBS ficam **no cadastro do serviço**. A Omie permite ajustar por item da OS, e alterar o serviço em lote atualiza OS e contratos abertos. | Padrão no `servico_fiscal`. O item da OS usa o do serviço; ajuste por item fica para depois, se alguém pedir. |
| Bling: o código nacional se consulta na lista de serviços do portal NFS-e. Contadores usam a **Tabela de Correlação LC 116 × NBS** da Receita. | Embarcar a lista nacional e a tabela de correlação: escolhido o código nacional, o sistema sugere o(s) NBS correspondente(s) (F1). |
| Omie: a **série da DPS** depende do município e se confirma emitindo uma nota pelo portal. | Igual à D3: confirmar no XML do Alan. |
| Omie: pré-requisito é a empresa ter feito o **primeiro acesso no Portal NFS-e Nacional** (gov.br, certificado ou CNPJ e senha). | Item da conferência da ativação e do texto de ajuda. |
| Omie e Conta Azul mantêm uma **lista própria de municípios integrados** e avisam que integrado ≠ obrigado a usar o nacional. | É a tabela de municípios da §2. |
| Fontes divergem sobre o NBS ser obrigatório (MEI opcional × obrigatório desde 01/2026). | Cobrar o NBS na completude, para todos. Mandar um campo a mais não rejeita; faltar pode rejeitar. |

## 2. A regra que cobre o Brasil todo

**A rota é decidida pelo regime + município, nunca só pelo município.**

1. **MEI → Nacional, sempre.** Obrigação federal desde 09/2023. A Focus inclusive
   bloqueia a rota municipal para MEI.
2. **Não MEI → depende do município.** Iguatu, por exemplo, "não usa o emissor
   nacional para todas as empresas". Nesses casos vai pela municipal.
3. A tabela de municípios fica **na plataforma**, não no ERP. Para cada código IBGE
   ela guarda: rota para não MEI (`NACIONAL` / `MUNICIPAL` / `DESCONHECIDA`), se exige
   login e senha da prefeitura, se exige código de tributação municipal, se tem
   homologação e se aceita cancelamento. Assim, uma prefeitura que mudar não exige
   instalador novo.
4. Município `DESCONHECIDO` para não MEI: a ativação **recusa com mensagem clara**
   ("ainda não emitimos NFS-e na sua cidade; fale com o suporte") e não liga nada às
   cegas.

A rota municipal entra **cidade por cidade, quando aparecer cliente**. A Nacional
entra primeiro porque cobre todo MEI do país e todo município aderente, e porque tem
homologação.

## 3. Regras que não mudam (para não quebrar quem usa)

| # | Regra |
|---|---|
| R1 | Tudo nasce **desligado**, atrás do módulo `NFSE` da licença. Sem o módulo, nenhuma tela nova aparece e a plataforma nega a emissão. |
| R2 | A NF-e e a NFC-e não passam pelo código novo. As fotografias de payload (F0 do fiscal) continuam idênticas. |
| R3 | ERP novo com plataforma velha (rota 404) mostra "NFS-e indisponível", e não erro 500. Plataforma nova com ERP velho não muda nada. |
| R4 | Migrations aditivas, uma por fase, em linha a partir de `f4t1m0v3l002` (ou do head do momento), decidindo pela presença do schema antigo. Testar em **banco copiado** de loja. |
| R5 | Arquivos `.py` abaixo de 64 KB (PyArmor trial). A NFS-e nasce em arquivos próprios (`emissoes/nfse_*.py`, `payload/nfse_*.py`). |
| R6 | Nota de teste só em **homologação**. Na empresa do Alan, produção é nota real. |

## 4. Decisões (para o Alan; as que dependem de contador estão marcadas)

| # | Proposta | A confirmar |
|---|---|---|
| D1 | Começar pela **NFS-e da OS** (mão de obra). Avulsa e venda de serviço no PDV ficam na F5. | Alan |
| D2 | **Uma NFS-e por OS**, somando todos os serviços aprovados (a DPS Nacional tem **um** serviço por nota). Com códigos de tributação diferentes na mesma OS, **uma nota por código**. | Alan / contador |
| D3 | **Numeração pela Focus** (`proximo_numero_nfsen_*`), sem `numero_dps` nosso. A série das notas do sistema precisa ser **diferente** da do portal, senão o número colide. Conferir no XML de uma nota do portal qual série ele usa. | XML do Alan |
| D4 | Desconto da OS rateado nos serviços (mesma regra da NF-e); o valor da nota = serviços − desconto. | contador |
| D5 | Retenção de ISS (`tipo_retencao_iss` = 2) só quando o tomador for PJ e o operador marcar. O padrão é "não retido". | contador |
| D6 | IBS/CBS em 2026: mandar `CST`/`cClassTrib` do cadastro do serviço, com padrão por regime (Simples/MEI). | contador |
| D7 | A **cota** da NFS-e é contada à parte da NF-e por licença (já é por módulo na `fiscal-cota.service.ts`). | Alan (limite do plano Focus) |
| D8 | NFS-e na **marcenaria**: terceiro modo da instalação (`instalacao_modo = NFSE`) + `servico_instalacao_id`. Fica para depois da F5. | Alan |

## 5. Fases

Cada fase fecha com pytest, vitest e `vue-tsc` verdes, as fotografias da NF-e
idênticas e um commit próprio, e não depende de ligar a anterior em produção.

### F0 — Levantamento (sem código de produto)
- XML/PDF de uma NFS-e real do Alan, emitida pelo portal: série, código de
  tributação, NBS, `opSimpNac`, alíquota.
- Testar em homologação, direto na Focus (curl com o token da empresa), uma DPS
  mínima do MEI. Isso valida o payload antes de escrever código.
- Fotografia (teste de ouro) do payload da NFS-e esperada, a partir do XML real.

### F1 — Dados que faltam (ERP)
- Código IBGE **sem migration**: calculado na hora de emitir, a partir de cidade + UF
  do endereço (que as lojas já têm), com uma tabela do IBGE embarcada (sem internet).
  Comparar nome sem acento e sem caixa. Se não achar a cidade, vira pendência na
  completude ("confira o nome da cidade no cadastro da empresa").
- `servico_fiscal` + `codigo_tributacao_nacional` (`VARCHAR(6)`) e `codigo_nbs`
  (`VARCHAR(9)`). A tela do serviço sugere o nacional a partir do LC 116, e o NBS vem
  de uma lista pesquisável. Os primeiros valores reais saem do XML do Alan (F0).
- Completude da NFS-e: IBGE da empresa, IM quando a rota exigir, código nacional e
  NBS no serviço, documento do tomador.
- Lista nacional de códigos de tributação + tabela de correlação LC 116 × NBS
  embarcadas (sugestão do NBS a partir do código escolhido).
- "Verificar NFS-e" na configuração fiscal: roda a completude da empresa e de todos
  os serviços, com correção em lote (padrão Omie).

### F2 — Plataforma: rota e ativação
- `RecursoFocus` ganha `'nfsen'` (e `'nfse'`, sem uso até a municipal).
- Rotas `POST /erp/fiscal/nfse/emitir`, `GET /consultar` e `POST /cancelar`, com
  `@RequerModulo(MODULO_NFSE)` e cota própria.
- A ativação liga `habilita_nfsen_homologacao` / `_producao` conforme a §2 (MEI →
  Nacional) e grava a rota na ficha fiscal.
- Tabela `MunicipioNfse` (seed vazio + Iguatu) e painel "Saúde fiscal" mostrando a
  rota da NFS-e.
- Testes na plataforma (`cd apps/server && npm test`).

### F3 — Emissão da NFS-e da OS (ERP)
- `payload/nfse_nacional.py` (montagem da DPS), `emissoes/nfse_os.py` (emitir, consultar
  e gravar em `documento_fiscal` com `tipo_documento='NFSE'` e em
  `ordem_servico_nota_fiscal.*_nfse`).
- O checkbox `emitir_nfse` passa a emitir de verdade. A OS mostra o status, o número
  e o link da DANFSe.
- Reconciliação de boot: consulta NFS-e `PROCESSANDO`, igual à NF-e.
- Diagnóstico das rejeições do sistema nacional (códigos `E…`) com mensagem em
  português, no estilo de `diagnostico_sefaz.py`.

### F4 — Cancelamento e documentos
- Cancelar (síncrono, com justificativa) a partir da OS e da lista de documentos.
- DANFSe/XML na lista de documentos e no ZIP do contador (passando pelo "Salvar
  como", d51ed867).

### F5 — Homologação e canário
- Ciclo completo em homologação na empresa do Alan: emitir, consultar e cancelar.
- Ligar produção **só** para a empresa do Alan, emitir **uma** NFS-e real de valor
  baixo e conferir no portal nfse.gov.br.
- Depois: NFS-e avulsa (sem OS), venda de serviço no PDV, rota municipal da primeira
  cidade que aparecer e a marcenaria (D8).

## 6. Pendências com o Alan

1. XML e PDF de uma NFS-e já emitida pelo portal (F0, D3).
2. Limite de notas por mês do plano Focus de R$ 80 e custo por CNPJ (D7).
3. Cidade/UF e regime de cada cliente que pode pedir NFS-e (para semear a tabela da §2).
4. Validade do certificado A1 da empresa 66.544.279 na Focus (a DPS Nacional por API
   é assinada com ele).
