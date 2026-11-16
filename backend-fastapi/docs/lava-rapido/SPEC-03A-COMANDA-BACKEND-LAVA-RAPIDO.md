# Spec 03A — Comanda (Backend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026                                             |
| Camada       | Backend ⚠️ registry e criação de OS (por chave declarada)              |
| Dependências | Specs 01A, 02A                                                        |
| Bloqueia     | Specs 03B, 04A                                                        |
| Referência   | SPEC-00 Revisão 4: U1, U2, U3, U4, U5 · PR1, PR10                       |

---

## 1. Objetivo

Deixar o backend pronto para a **comanda de uma tela** (03B): checklist de avarias por tipo de veículo, rótulos do pátio, a capacidade que liga o módulo e a marca opcional.

**Nenhuma rota nova:** a comanda abre a OS pelo `POST /ordens-servico` de sempre e cria o cliente novo pelo `POST /clientes/cliente_pf` (nome + celular; CPF já é opcional).

## 2. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Capacidade nova **`operacao_patio`**, declarada só pelo lava-rápido | Liga o módulo `modules/lava-rapido/` (U1) e guarda a rota do pátio (04A) |
| D2 | Cada tipo declara **`avarias`**: lista simples de textos (`tipo_de_trabalho(..., avarias=[...])`). A comanda grava as marcadas em `ordens_servico.dados_adicionais.avarias` (lista) | U4: "não dá para padronizar". Checklist de marcar é o que o ramo usa; a vistoria item a item com estado continua na OS de detalhes |
| D3 | Rótulos do pátio: ABERTA → **Aguardando**, EM_ANDAMENTO → **Lavando**, AGUARDANDO_RETIRADA → **Pronto** | U3. Só texto; o enum gravado é o de sempre |
| D4 | Chave nova **`colunas_opcionais: ["marca"]`**: a abertura de OS dispensa a marca, e vazia vira `""` (coluna NOT NULL). O campo `marca` do lava perde o asterisco | U2: na comanda, "Gol prata" no modelo basta. **Explícita, e não deduzida dos campos**: a oficina desenha a marca sem asterisco e o backend sempre a exigiu — deduzir mudaria uma loja em produção |
| D5 | Bicicleta entrou na 02A (tipo próprio, sem placa); aqui ganha a sua lista de avarias | U5 |

## 3. Avarias por tipo

| Tipo | Itens |
|---|---|
| Carro | Riscos na pintura, Amassados, Para-brisa / vidros trincados, Faróis / lanternas, Rodas / calotas, Retrovisores, Para-choques, Adesivos / envelopamento, Bancos / estofado, Painel, Tapetes / assoalho |
| Moto | Riscos na carenagem, Tanque, Banco, Escapamento, Guidão / manetes, Retrovisores, Faróis / piscas, Rodas |
| Caminhão / ônibus | Riscos na pintura, Amassados, Para-brisa / vidros trincados, Faróis / lanternas, Rodas, Retrovisores, Para-choques, Carroceria / baú, Lona / sider, Cabine (interior) |
| Bicicleta | Quadro / pintura, Rodas / aros, Câmbio / corrente, Selim, Guidão, Freios |
| Outros | Riscos, Amassados, Peças soltas / quebradas, Estofado / interior |

## 4. Prova de não regressão

- Guard: só o lava declara `colunas_opcionais` e `avarias`; rótulos de status por segmento ditos em voz alta.
- API: `test_oficina_continua_exigindo_a_marca`; `test_os_identificador_gerado.py` (serigrafia, marcenaria, informática) intacto.

## 5. Casos de teste

- `test/core/test_registry_segmentos.py`: rótulos do lava (3); capacidades (+`operacao_patio`); todo tipo com checklist sem repetição; só o lava declara as chaves novas; marca sem asterisco e modelo com.
- `test/api/v1/test_segmento_lava_rapido.py`: modelo exigido, marca não (e grava `""`); oficina continua exigindo a marca.
