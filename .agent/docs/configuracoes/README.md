# Configurações (`configuracoes`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

O **modal de Configurações** do sistema (aberto pelo menu de configurações do `mainLayout`, **sem rota própria**). Reúne em seções as preferências de cada área: backup, cadastro de clientes, formatos de exibição, gestão financeira, impressão, integrações, regras de vendas, produtos e estoque, ordens de serviço, segurança, licença, rede, terminais, suporte, e as seções dos segmentos (Lava-rápido e Marcenaria).

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Frontend | `frontend/src/modules/configuracoes/` — `components/ConfiguracoesModal.vue`, `PinGerenteModal.vue`, `components/sections/<seção>/components/*.vue` |
| Dados | `composables/queries/` e `composables/mutates/` (uma consulta/gravação por área) · `services/configuracoes.service.ts`, `backup.service.ts`, `configuracaoMarcenaria.service.ts` · `schemas/` |
| Estado global | `frontend/src/shared/stores/configuracoes.store.ts` |
| Backend (endpoints) | `configuracao.py` (`/api/v1/configuracoes`, 14 rotas) · `backup.py` (`/api/v1/backup`, 9 rotas) |
| Backend (regras) | `app/services/configuracao/` (`vendas`, `clientes`, `produtos`, `ordem_servico`, `seguranca`, `backup`, `marcenaria`) · `app/services/backup/` (local) e `app/services/cloud/` (nuvem) |
| Backend (banco) | `models/configuracao_vendas.py`, `configuracao_clientes.py`, `configuracao_produtos.py`, `configuracao_os.py`, `configuracao_seguranca.py`, `configuracao_backup.py`, `configuracao_marcenaria.py`, `configuracao_licenca.py` |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **Seção** | Uma área do modal (ex.: "Regras de vendas"), com formulário e botão de salvar próprios. |
| **PIN do gerente** | Senha curta pedida para ações sensíveis (`PinGerenteModal`). |
| **Backup local / em nuvem** | Cópia do banco: local em `services/backup`; nuvem em `services/cloud` (envio, histórico, restauração). |
| **Terminais** | Máquinas conectadas à instalação. |

## 4. Fluxos principais

1. Abrir o modal → cada seção carrega a sua configuração (`useConfiguracoes*Query`) → editar → `useSalvarConfiguracoes*Mutation`.
2. **Backup:** criar manualmente, agendar, listar histórico, restaurar.
3. **Segurança:** configurações que exigem PIN do gerente.

## 5. Decisões de arquitetura

- **Uma tabela de configuração por área** (`configuracao_*`), em vez de um único "saco" de opções.
- Seções de **segmento** (Lava-rápido, Marcenaria) só fazem sentido para aquele segmento.
- Restaurar backup substitui o banco: ação destrutiva, sempre com confirmação e **nunca** deve ser exercitada contra o banco de uma loja real em desenvolvimento.
- O backend precisa ser regerado no sidecar quando uma nova configuração é adicionada (`npm run build:sidecar`).

## 6. Integração com outros módulos

- Praticamente todos os módulos **leem** as suas configurações aqui (vendas, clientes, produtos/estoque, OS, financeiro).
- **`network-config`** e **`license`:** as seções "Rede" e "Licença" mostram o estado dessas áreas.

## 7. Referências

- `backend-fastapi/docs/backup-nuvem-plano.md` · `backup-nuvem-relatorio-fases.md` · `diagnostico-plano.md`
- `CLAUDE.md` — seções sobre banco e papel da máquina.
