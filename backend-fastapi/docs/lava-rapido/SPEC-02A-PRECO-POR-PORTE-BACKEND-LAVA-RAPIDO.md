# Spec 02A — Preço por Porte (Backend)

| Campo        | Valor                                                                  |
|--------------|------------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026                                              |
| Camada       | Backend (FastAPI + SQLAlchemy + Alembic)                               |
| Dependências | Spec 01A                                                               |
| Bloqueia     | Specs 02B, 03B                                                         |
| Referência   | SPEC-00: P1, P2a, P5, U2, U5, PR1, PR3, PR8                             |

---

## 1. Objetivo

Cada loja tem a **sua** lista de portes por tipo de veículo, e cada serviço tem um **preço e uma duração por porte**. A comanda (Spec 03B) pergunta "quais serviços e quanto custam para um SUV?" e recebe a resposta pronta.

A tabela `servicos` **não muda**: sem preço para o porte, vale o `servicos.valor` de sempre.

## 2. Escopo

**Dentro**
- Capacidade nova `preco_por_porte` (declarada só pelo lava-rápido).
- Tipo **Bicicleta** no registry (SPEC-00 U5), porque a lista inicial de portes sai dos tipos.
- Tabelas `portes_veiculo` e `servico_precos_porte` + migração `l4v4p0r7e001`.
- Rotas em `/api/v1/lava-rapido`.

**Fora**
- Tela de portes e grade no cadastro de serviço → 02B.
- Previsão de entrega: a comanda soma as durações e grava `data_previsao` (03B). Não há regra de backend.
- O preço não é imposto na OS. O atendente pode alterar (C1a); a OS continua recebendo o valor do item como hoje.

## 3. Arquivos

| Arquivo | Mudança |
|---|---|
| `app/core/segmentos/capacidades.py`, `__init__.py` | `CAP_PRECO_POR_PORTE` |
| `app/core/segmentos/definicoes/lava_rapido.py` | `PORTES_BICICLETA`, tipo `bicicleta`, capacidade |
| `app/db/models/lava_rapido/` (novo) | `PorteVeiculo`, `ServicoPrecoPorte` |
| `app/db/models/__init__.py` | registro dos models |
| `alembic/versions/l4v4p0r7e001_lava_rapido_portes.py` | migração |
| `app/schemas/lava_rapido/porte.py` (novo) | contrato |
| `app/db/crud/lava_rapido/porte.py` (novo) | consultas |
| `app/services/lava_rapido/portes.py` (novo) | regra |
| `app/api/v1/endpoints/lava_rapido.py` (novo) + `api.py` | rotas |

## 4. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | A lista inicial é lida do campo `porte` de cada tipo no registry, e gravada na **primeira leitura** de `/portes`, uma vez só (tabela com qualquer linha, mesmo inativa, é da loja) | Uma fonte só para a lista; o padrão get-or-create da configuração da marcenaria |
| D2 | Porte nunca é apagado, só desativado | Os preços e os veículos que já o usam continuam legíveis |
| D3 | Nome único por tipo, sem diferença de maiúsculas (409) | Dois "SUV" deixariam o preço ambíguo |
| D4 | A grade de preços é gravada **inteira** (PUT): porte fora da lista volta ao preço padrão | A tela edita a grade toda; sem PATCH linha a linha |
| D5 | `GET /portes/{id}/servicos` devolve **todo** serviço ativo, com o preço do porte ou o padrão (`preco_do_porte` diz qual) | O balcão nunca fica sem o serviço só porque o dono não preencheu a grade |
| D6 | Permissão: a mesma do cadastro de serviço (`servico`) | Portes e preços são parte do cadastro |
| D7 | Fora do segmento com `preco_por_porte`, todas as rotas respondem 404 | PR1: para as outras lojas a funcionalidade não existe |
| D8 | O porte do veículo continua gravado como **texto** em `objetos_servico.dados_adicionais.porte` (01A); a comanda acha o porte por tipo + nome | Sem migração em `objetos_servico`. Renomear um porte faz o veículo antigo perguntar o porte de novo (limitação, §7) |
| D9 | Migração decide pela ausência de **cada** tabela; FKs com `ondelete=CASCADE` | PR8; o `create_all` do startup costuma criar antes |

## 5. Rotas (`/api/v1/lava-rapido`)

| Método | Rota | Resposta |
|---|---|---|
| GET | `/portes?tipo_veiculo=&incluir_inativos=` | `PorteRead[]` (grava a lista inicial na 1ª vez) |
| POST | `/portes` `{tipo_veiculo, nome}` | 201 `PorteRead` (entra no fim da ordem) · 409 nome repetido · 422 tipo desconhecido |
| PUT | `/portes/{id}` `{nome?, ordem?, ativo?}` | `PorteRead` |
| GET | `/portes/{id}/servicos` | `ServicoDoPorte[]` = `{servico_id, descricao, valor, duracao_minutos, preco_do_porte}` |
| GET | `/servicos/{id}/precos` | `PrecoPorteRead[]` = `{porte_id, valor, duracao_minutos}` |
| PUT | `/servicos/{id}/precos` `{precos: [...]}` | grade gravada · 422 porte repetido ou valor negativo · 404 porte inexistente |

## 6. Prova de não regressão (PR1)

- `servicos` intacta (teste da migração confere colunas e linhas).
- Oficina: rotas 404 (`test_fora_do_lava_rapido_as_rotas_nao_existem`).
- Guard do registry: só o lava declara `preco_por_porte`; ids dos tipos são contrato.
- Suíte inteira do backend ao fim do Marco 2.

## 7. Limitações

- Renomear um porte não atualiza o texto gravado nos veículos (D8): na próxima visita, o atendente escolhe o porte de novo.

## 8. Casos de teste

`test/api/v1/test_lava_rapido_portes.py` (10) e `test/db/test_migracao_portes_lava_rapido.py` (3):
lista inicial e não duplica · não renasce depois de editada · criar/renomear/reordenar/desativar · nome repetido (com e sem caixa; outro tipo pode) · tipo desconhecido · grade inteira e volta ao padrão · porte repetido, inexistente, valor negativo · comanda com preço do porte e padrão · serviço desativado some · 404 fora do segmento · migração: tabelas novas e `servicos` intacta, `create_all` antes, downgrade e upgrade.
