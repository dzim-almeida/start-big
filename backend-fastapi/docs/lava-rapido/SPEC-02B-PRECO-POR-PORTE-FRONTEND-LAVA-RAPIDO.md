# Spec 02B — Preço por Porte (Frontend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (roteiro manual pendente)                   |
| Camada       | Frontend (Vue 3 + TypeScript) ⚠️ cadastro de serviço, Configurações    |
| Dependências | Spec 02A                                                              |
| Bloqueia     | Spec 03B (comanda)                                                    |
| Referência   | SPEC-00: P1, P2a, P5, U1, PR1                                          |

---

## 1. Objetivo

O dono ajusta os portes da loja e preenche, em cada serviço, o preço e a duração de cada porte.

## 2. O que muda na tela (só no lava-rápido)

- **Configurações › Lava-Rápido** (nova): portes por tipo de veículo (botões Carro / Moto / Caminhão / Bicicleta / Outros). Renomear, subir/descer, desativar/reativar e adicionar. Salva na hora, sem botão "Salvar".
- **Cadastro de serviço**: seção nova **Preço por porte**, abaixo de "Dados do Serviço". Os tipos aparecem em abas; cada porte tem preço (vazio = valor base) e duração em minutos. A grade é gravada junto com o serviço.

## 3. Arquivos

| Arquivo | Mudança |
|---|---|
| `modules/lava-rapido/shared/` (novo) | schema, serviço de API e queries de portes (`usePortes.ts`) |
| `modules/lava-rapido/precos/` (novo) | `PrecosPorPorteSection.vue` e `usePrecosPorPorteForm.ts` |
| `configuracoes/.../sections/lava-rapido/components/LavaRapido.vue` (novo) | seção de portes |
| `configuracoes/components/ConfiguracoesModal.vue`, `types/configuracoes.types.ts` | seção nova, visível por capacidade, em `secoesAutoSave` |
| `order-service/servicos/composables/useServicoForm.ts` | gancho `aoSalvar(servicoId)` |
| `order-service/servicos/components/ServicoFormModal.vue` | monta a seção por capacidade |
| `order-service/shared/segmento/segmentDefinition.type.ts`, `useCapacidades.ts` | `preco_por_porte`, `temPrecoPorPorte`, fallback do lava |

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Tudo liga pela capacidade `preco_por_porte`; as queries têm `enabled` por ela | PR1: nos outros segmentos nada aparece e nenhuma chamada é feita (as rotas dariam 404) |
| D2 | O formulário de serviço ganha um gancho genérico `aoSalvar`, e a grade se registra nele | Serviço novo só tem id depois do POST; o formulário não precisa conhecer o lava-rápido |
| D3 | Falha da grade vira **aviso** e o modal fecha mesmo assim | O serviço já está salvo; modal aberto num cadastro novo convidaria a criar um duplicado |
| D4 | Preço vazio = sem linha (volta ao valor base); **zero é preço** | Lavagem de cortesia existe; ausência e zero não podem se confundir |
| D5 | Duração sem preço não é gravada | A linha da grade é a do preço (Spec 02A); evita linha "meio cadastrada" |
| D6 | Seção de portes salva campo a campo (`secoesAutoSave`), como as Formas de recebimento | Cada porte é um registro independente; sem botão "Salvar" que não salva nada |
| D7 | Reordenar troca a posição com o vizinho reescrevendo a `ordem` dos dois pela posição na lista | A ordem gravada pode ter empates (porte novo entra com máx+1) |

## 5. Casos de teste

`modules/lava-rapido/precos/__tests__/usePrecosPorPorteForm.spec.ts`: minutos (inteiro, vazio, zero, lixo, teto de 24 h); grade → PUT (reais → centavos, sem preço fica de fora, `null` do MoneyInput, zero é preço).

### Roteiro manual
1. Configurações › Lava-Rápido: renomear "Picape" para "Caminhonete", subir "SUV", desativar "Van", adicionar "SUV 7 lugares".
2. Serviços › novo "Lavagem completa" R$ 50: Hatch R$ 40 / 30 min, SUV R$ 60 / 45 min. Salvar, abrir de novo e conferir.
3. Oficina ou informática: nenhuma seção nova em Configurações nem no serviço.
