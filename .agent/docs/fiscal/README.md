# Centro Fiscal (`fiscal`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

O **Centro Fiscal** (`/fiscal/*`): configuração fiscal da loja e emissão e acompanhamento de **NF-e** (nota de produto), **NFC-e** (cupom do consumidor) e **NFS-e** (nota de serviço). Tem quatro abas: **Configurações**, **NF-e**, **NFC-e** e **NFS-e**, listagem de documentos, cancelamento, carta de correção, inutilização de numeração e devolução.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/fiscal/` — `views/` (`FiscalLayout`, `FiscalConfiguracoesView`, `FiscalNFeView`, `FiscalNFCeView`, `FiscalNFSeView`), `components/` (`configuracoes`, `listagem`, `detalhes`, `emitir`, `nfse`, `shared`), `composables/` (consultas e mutations por operação), `services/fiscal.service.ts` e `nfse.service.ts`, `utils/` |
| Backend (endpoints) | `fiscal.py` (agrega, exige `NFE`), `fiscal_config.py`, `fiscal_documentos.py`, `fiscal_emissao.py` (NFC-e), `fiscal_eventos.py`, `fiscal_nfse.py` (`/fiscal/nfse`), `fiscal_produto.py`, `fiscal_franquia.py` |
| Backend (regras) | `app/services/fiscal/` — `emissao`, `emissoes`, `payload`, `tax_engine` (cálculo de impostos), `derivacao`, `completude`, `configuracao`, `cadastro`, `documentos`, `eventos`, `nfse`, `os_notas.py`, `http` |
| Backend (banco) | `documento_fiscal.py`, `documento_fiscal_item.py`, `inutilizacao_fiscal.py`, `carta_correcao_fiscal.py`, `perfil_tributario.py`, `regra_perfil_tributario.py`, `produto_fiscal.py`, `servico_fiscal.py`, `tributacao.py`, `ncm.py`, `nfse_tabelas.py`, `aliquota_uf.py`, `empresa_fiscal_settings.py`, `venda_nota_fiscal.py`, `ordem_servico_nota_fiscal.py` |
| Dados de apoio | `backend-fastapi/app/data/` (`ncm`, `nbs`, `municipios_ibge`, tabelas da NFS-e) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **NF-e / NFC-e / NFS-e** | Nota de produto (modelo 55), cupom fiscal do consumidor (modelo 65) e nota de serviço. |
| **Emissão incerta** | Quando não se sabe se a SEFAZ autorizou (rede caiu); o sistema consulta antes de reemitir (`useEmissaoIncerta`). |
| **Inutilização** | Descartar um intervalo de numeração não usado. |
| **Carta de correção** | Evento para corrigir campos de uma NF-e já autorizada. |
| **Perfil tributário / NCM / CFOP / CST** | Dados que definem o imposto de cada produto/serviço. |
| **Plataforma** | Servidor web da StartBig que recebe o pedido do ERP e emite via provedor fiscal. |

## 4. Fluxos principais

1. **Configurar:** dados fiscais da empresa, certificado e numeração (aba Configurações).
2. **Emitir:** a venda/OS monta o payload (`payload_builder`), o ERP envia para a plataforma e acompanha o status; a nota autorizada fica salva em `documento_fiscal`.
3. **Eventos:** cancelar, carta de correção, inutilizar, devolver.
4. **NFS-e:** emissão por município, com tabelas de serviço/NBS e RPS.

## 5. Decisões de arquitetura

- **Arquitetura de emissão:** `ERP → api.startbig.com.br → provedor fiscal → SEFAZ`, autenticada com o JWT da licença (ver `contrato-api-fiscal-plataforma.md`).
- **Módulos separados e que negam por padrão:** `NFE`, `NFCE` e `NFSE` estão em `MODULOS_NEGADOS_SEM_RESPOSTA` (`app/core/modulos.py`). Liberar por engano emitiria nota em nome da loja; "não sei" significa **não**. Cada aba do menu carrega o seu módulo.
- **Gate fiscal:** a trava que impede emitir não se destrava sozinha (`test/core/test_gate_fiscal_nao_se_destranca.py`).
- **Um motor de impostos único** (`tax_engine`) e **payload montado no backend**; o frontend só orquestra e mostra o resultado.
- Cuidado com **campos que somem no caminho** entre ERP e plataforma (ver `fiscal-campos-perdidos-plano.md`).
- **Pendência `PEND-001`:** CNPJ alfanumérico bloqueia a emissão para destinatário com o formato novo.

## 6. Integração com outros módulos

- **`enterprise`:** emitente, regime, certificado, numeração.
- **`products` / `order-service` (serviços):** dados fiscais do produto e do serviço.
- **`sales` e `order-service`:** disparam a emissão (`venda_nota_fiscal`, `ordem_servico_nota_fiscal`).
- **`license`:** módulos `NFE`, `NFCE`, `NFSE` e franquia de notas (`fiscal_franquia`).

## 7. Referências

- `backend-fastapi/docs/` — `fiscal-refatoracao-plano.md`, `fiscal-onboarding-plano.md`, `fiscal-conclusao-plano.md`, `fiscal-100-plano.md`, `contrato-api-fiscal-plataforma.md`, `nfse-plano.md`, `nfse-fase2-plano.md`, `nfse-melhorias-plano.md`, `nfe-cfop-e-notas-da-os-plano.md`, `pdv-fiscal-e-nao-fiscal-plano.md`
