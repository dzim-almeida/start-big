# Casca do app (`mainLayout`) — Visão geral

> Descreve **o que existe hoje** no código (levantado em 2026-11-18). Mantido pelo time: o agente só propõe mudanças.

## 1. O que é

É a **moldura** de toda a área autenticada: menu lateral (sidebar), cabeçalho, cartão da empresa e do usuário, notificações, atalhos rápidos e o menu de configurações. Também é o arquivo onde **todas as rotas da área logada são declaradas** (`mainLayout/routes.ts`), em vez de cada módulo ter o seu.

## 2. Onde está o código

| Camada | Caminho |
|--------|---------|
| Layout | `frontend/src/modules/mainLayout/views/MainLayout.vue` |
| Menu e cabeçalho | `components/layout/` (`BaseHeader`, `sidebar/BaseSidebar`, `SidebarItem`, `SidebarItemGroup`) |
| Peças de interface | `components/ui/` (`CompanyCard`, `UserCard`, `NotificacoesPanel`, `QuickActions`, `SettingsMenu`, `LicencaStatusBadge`) |
| Itens do menu | `constants/layout.constants.ts` |
| Estado do layout | `store/layout.store.ts` |
| Permissões do menu | `composables/useCheckPermission.ts` |
| Comunicados (notificações) | `services/comunicado.service.ts` ↔ backend `/api/v1/comunicados` |
| Rotas da área logada | `routes.ts` (desta pasta) |

## 3. Conceitos e vocabulário

| Termo | Significado |
|-------|-------------|
| **`meta` da rota** | Informações extras da rota: `title`, `subtitle`, `tabId` (qual item do menu acende), `requiresAuth`, `telaCheia`. |
| **`exigeModulo`** | A rota só abre se a licença traz aquele módulo contratado (ver `license`). |
| **`exigeOrdemServico`** | A rota só abre em segmento que tem Ordem de Serviço (o `pdv` não tem). |
| **`requiredModule` (menu)** | O item do menu some quando o módulo não está contratado. |

## 4. Fluxos principais

1. Toda rota filha de `MainLayout` herda `requiresAuth: true`; o guard de `router/index.ts` redireciona para `/login` se não houver sessão.
2. O menu é montado a partir de `layout.constants.ts`, filtrando por permissão (`shared/constants/permissions.constants.ts`) e por módulo contratado (`modulos.store`).
3. Rotas "de verdade" por área: `/` (Início), `/vendas`, `/servicos`, `/orcamentos...`, `/clientes`, `/produtos`, `/equipes`, `/empresa`, `/relatorios`, e os grupos com filhas `/financeiro/*`, `/compras/*`, `/fiscal/*`.

## 5. Decisões de arquitetura

- **Esconder item do menu não basta:** a trava real fica no `meta` da rota (`exigeModulo`, `exigeOrdemServico`) lido pelo guard, e no backend (`requer_modulo`).
- **Orçamentos** (`/orcamentos`) redireciona para a aba "Orçamentos" de Serviços; o editor (`/orcamentos/novo` e `/orcamentos/:id`) abre em tela cheia (`telaCheia`).
- **Atenção a conferir:** o caminho `/vendas` e o nome `sales` aparecem **duas vezes** em `routes.ts` (a primeira apontando para `HomeView`, a segunda para `SalesView`). O Vue Router mantém um só; confirme qual vale antes de mexer nessas rotas.

## 6. Integração com outros módulos

- Importa as telas de **todos** os módulos (carregamento preguiçoso) e lê as stores globais (`auth`, `modulos`, `licenca`, `configuracoes`).
- `home`, `sales`, `customers`, `products`, `employees`, `enterprise`, `reports`, `order-service`, `financeiro`, `compras` e `fiscal` são as telas que ele hospeda.

## 7. Referências

- `frontend/src/router/index.ts` (guard global).
- `frontend/src/shared/constants/modulos.constants.ts` (chaves dos módulos contratáveis).
