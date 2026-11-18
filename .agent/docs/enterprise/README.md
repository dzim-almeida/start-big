# Dados da Empresa (`enterprise`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

A tela **Dados da Empresa** (`/empresa`, nome `enterprise`): cadastro da própria empresa dona do sistema — identificação, endereço, contato, dados tributários e as configurações que o **fiscal** usa para emitir notas (emissão, NFS-e, certificado).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/enterprise/` (`views/EmpresaView.vue`, `components/EmpresaForm.vue`) |
| Seções do formulário | `components/form/` (`IdentificationSection`, `AddressSection`, `ContactSection`, `TaxDataSection`, `FiscalSettingsSection`, `EmissaoSection`, `EmissaoStatusSection`, `NfseSection`) |
| Apoio | `composables/` (`useEmpresaQuery`, `useEmpresaFormProvider`, `useConsultaCNPJ`, `useIbgeCityLookup`) · `services/empresa.service.ts` · `schemas/empresa.schema.ts` |
| Backend (endpoint) | `backend-fastapi/app/api/v1/endpoints/empresa.py` (`/api/v1/empresas`, 8 rotas) |
| Backend (regras) | `app/services/empresa/` (`cadastro.py`, `fiscal.py`, `certificado.py`) · `app/schemas/empresa/` · `app/db/crud/empresa/` |
| Backend (banco) | `app/db/models/empresa.py` · `empresa_fiscal_settings.py` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Empresa (tenant)** | Dona dos dados; toda tabela de negócio tem `empresa_id`. |
| **Regime tributário** | Enquadramento fiscal (ex.: MEI, Simples) que muda como a nota é calculada. |
| **Certificado digital** | Arquivo (`*.pfx`) usado para assinar notas; guardado criptografado (a chave de criptografia fica no `data_dir`, junto do banco). |
| **Inscrição municipal / RPS** | Dados usados na NFS-e (nota de serviço). |

## 4. Fluxos principais

1. **Abrir:** `useEmpresaQuery` carrega a empresa; o formulário é dividido em seções com um provider compartilhado (`useEmpresaFormProvider`).
2. **Consultar CNPJ e cidade:** preenche campos a partir do CNPJ (`useConsultaCNPJ`) e lista os municípios de uma UF na API pública do IBGE (`useIbgeCityLookup`).
3. **Salvar:** `PUT /empresas/` grava os dados; a parte fiscal é tratada por `services/empresa/fiscal.py`. Outras rotas do prefixo: `/imagem` (logo), `/tema`, `/logo-base64`.
4. **Certificado:** o backend lista os certificados instalados no Windows (`GET /empresas/certificados-windows`) e guarda a escolha (`POST /empresas/certificado-windows`, `services/empresa/certificado.py`). Nunca exibir nem logar o conteúdo.

## 5. Decisões de arquitetura

- O item de menu e as seções fiscais só aparecem quando a licença traz os módulos fiscais (`NFE`, `NFCE`, `NFSE`), que **negam por padrão** (ver `license`).
- **Segredos** (certificado, senha de prefeitura/token) nunca vão para log, docs ou testes.
- **Pendência `PEND-001`:** o CNPJ alfanumérico não é aceito aqui (máscara e validação) — ver `backend-fastapi/docs/pendencias-sistema.md`.

## 6. Integração com outros módulos

- **`fiscal`:** lê emitente, regime e numeração desta empresa.
- **`sign-in`:** cria a empresa no primeiro acesso.
- **`sales`, `order-service`, `reports`:** imprimem o nome e os dados da empresa em recibos e relatórios.

## 7. Referências

- `backend-fastapi/docs/fiscal-onboarding-plano.md`, `nfse-plano.md`
- `backend-fastapi/docs/pendencias-sistema.md`
