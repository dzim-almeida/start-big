# Spec 10A — Lavadores e Comissão Dividir/Inteira (Backend)

| Campo        | Valor                                                                   |
|--------------|-------------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026                                               |
| Camada       | Backend ⚠️ relatório de comissão (todas as lojas), cargos, funcionários  |
| Dependências | Spec 01A                                                                |
| Bloqueia     | Specs 03B, 04A, 10B                                                     |
| Referência   | SPEC-00: O7a, O7c (Revisão 2), PR1, PR8                                  |

---

## 1. Objetivo

A OS registra **quem lavou** (1 ou 2 lavadores; a tabela aceita até 5), além do responsável que a abriu. A comissão de serviço vai para os lavadores, **dividida** ou **inteira** conforme o dono configurou no cargo ou no funcionário.

## 2. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Tabela genérica **`ordem_servico_executores`** (OS, funcionário; único por par; `CASCADE` na OS) | O7a. O nome não fala de lavagem: outro segmento pode usar |
| D2 | Capacidade **`executores_os`** (só o lava declara) guarda as rotas | PR1 |
| D3 | Coluna **`comissao_divisao`** (`dividir` \| `inteira`, nula) em `cargos` e `funcionarios`, em cascata funcionário → cargo → `dividir`, igual ao `comissao_modo` | O7c ("cada lava-rápido paga de um jeito, quem decide é o dono"). Colunas nulas aditivas (exceção a F5, registrada no SPEC-00) |
| D4 | **Comissão:** OS **sem** executor → responsável, com a **mesma expressão de sempre**. OS **com** executores → cada executor recebe a mão de obra ÷ n (`dividir`) ou inteira (`inteira`), arredondada ao centavo por item. O responsável não recebe pela OS que tem lavadores | "Quem lava é quem ganha por lavagem" (O7b/O7c). O ramo sem executor é o de toda OS de todo segmento hoje |
| D5 | O **extrato** do funcionário usa a mesma regra (responsável sem executores OU executor) e mostra "(dividido por N)" | O extrato tem que bater com o ranking (regra de 05/09/2026) |
| D6 | Rotas `GET/PUT /lava-rapido/os/{numero}/lavadores` (lista inteira, sem repetir, na ordem; vazia = sem lavador). A comanda chama depois de criar a OS; `OrdemServicoCreate` não muda | Nenhum schema da OS mexido (PR1) |
| D7 | OS finalizada ou cancelada não troca lavador (422) | Já entrou na folha; trocar mudaria comissão paga sem ninguém ver |
| D8 | Lavador precisa existir e estar ativo (422); no máximo 5 | Evita lixo e a OS com o mesmo funcionário dobrado |

## 3. Arquivos

`db/models/ordem_servico_executor.py` (novo), `cargo.py`/`funcionario.py` (coluna), `schemas/funcionario/` (`ComissaoDivisao`), migração `l4v4ex3c0002`, capacidade, `schemas/lava_rapido/lavador.py`, `services/lava_rapido/lavadores.py`, rotas em `endpoints/lava_rapido.py`, `db/crud/relatorio/equipe.py` (base e extrato), `services/relatorio/equipe.py` (parte no extrato).

## 4. Prova de não regressão

- Suítes de comissão, relatório, funcionário e caixa: **459 passando** com a mudança (`test_comissao_config`, `test_comissao_sobre_lucro`, `test_relatorio*`, `test_funcionario`, `test_caixa`, `test/core`).
- Migração num banco antigo real (cópia do backup da marcenaria): sobe `l4v4p0r7e001 → l4v4ex3c0002` sem erro; teste confere que a comissão já configurada não muda.

## 5. Casos de teste

`test/api/v1/test_lava_rapido_lavadores.py` (11): definir/ler (sem repetir, ordem, lista vazia) · inexistente, limite, OS inexistente · OS finalizada 422 · 404 fora do segmento · sem lavador = responsável como sempre · dois dividem por padrão (e o responsável não recebe) · `inteira` no cargo · funcionário sobrescreve o cargo · um lavador recebe tudo · extrato bate com o ranking e mostra "dividido por 2" · cargo aceita/devolve e recusa valor inválido.
`test/db/test_migracao_lavadores_lava_rapido.py` (3).
