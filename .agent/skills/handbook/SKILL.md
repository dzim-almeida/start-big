---
name: handbook
description: Documenta um módulo implementado do StartBig para pessoas (dono da loja, suporte, implantação, QA e engenharia) em três artefatos complementares — Visão Geral, Especificação de Negócio e Documentação Técnica — escritos a partir do repositório e entregues como Markdown em .agent/docs/{módulo}/handbook/. Use sob demanda ou quando a skill doc §7.4 sugerir.
---

# Skill `handbook` — os três artefatos de um módulo

> Caminhos com `@/` são relativos a `.agent/`. Os modelos ficam em `@/skills/handbook/templates/`.
>
> Esta skill **não altera código**. A saída são três arquivos Markdown em `@/docs/{módulo}/handbook/`. Quando roda sozinha, a tarefa é da **trilha leve** (`@/AGENT.md` §3.2).

## 0. Princípios

- **Três artefatos, três públicos, um entendimento.** Cada um responde a uma pergunta. Juntos, descrevem o módulo inteiro:

  | Artefato | Pergunta | Público | Modelo |
  |----------|----------|---------|--------|
  | 🧭 **Visão Geral** | O quê e para quê, sem jargão | Donos, gerentes, suporte, implantação | `templates/visao-geral.md` |
  | 📐 **Especificação de Negócio** | Quais regras o sistema **precisa** cumprir | Produto, QA, engenharia, implantação | `templates/negocio.md` |
  | ⚙️ **Documentação Técnica** | Como foi construído | Engenharia, revisores técnicos, auditoria | `templates/tecnico.md` |

- **Cada informação tem um dono só.** As regras numeradas vivem na Especificação de Negócio. A Visão Geral explica as regras em linguagem simples e aponta para lá. A Técnica cita os IDs (`RN-CLIENTE-07`) em vez de reescrever a regra. Uma regra que pertence a outro módulo aponta para o documento desse módulo.
- **Tudo vem do repositório.** Cada fato tem uma fonte (spec, ADR, código, teste). Se um fato não tem fonte, é suposição: confira no código ou pergunte. Nunca invente ator, regra, prazo, alíquota ou mensagem.
- **O código vence a spec.** Specs concluídas podem ter notas de revisão e o código pode ter evoluído depois delas. Documente o que **está** implementado. Se a spec e o código divergem, registre no relatório (§6) e pergunte qual vale. Não "corrija" nenhum dos dois.
- **Idioma:** os três documentos ficam em PT-BR. Os identificadores de código aparecem como estão no código, só na Técnica e entre crases.
- **Sem segredos:** nunca leia `.env`, `system-config.json` real, certificados nem o banco de um cliente. Nos exemplos, use pessoas, CPF/CNPJ e e-mails fictícios (`@example.com`).
- **Mostrar antes de publicar.** Os rascunhos são mostrados ao usuário. Publicar em outro lugar (wiki, drive, ferramenta de tarefas) é decisão dele e só acontece depois da aprovação (§5).

## 1. Entradas

Leia na ordem, só o que o módulo tiver:

| Fonte | Alimenta |
|-------|----------|
| Linha do módulo no `@/AGENT.md` §1 | Onde o código vive (pastas de frontend e backend do domínio) |
| `@/docs/{módulo}/SUMMARY.md` e `CHANGELOG.md` | O que está pronto, arquivos principais, pendências, data da última mudança |
| `@/docs/{módulo}/README.md` (seções que tocam o artefato) | Conceito, arquitetura e fluxos |
| `@/docs/{módulo}/ACORDO.md` e `adr/` | Decisões de negócio, consequências aceitas, como reverter |
| `@/specs/{módulo}/README.md` e `completed/` | Histórico de construção, critérios de aceite (regras), textos de tela, casos alternativos |
| `@/docs/{módulo}/learn/README.md` | Limitações e armadilhas que viram "Limitações conhecidas" |
| Backend (`app/api/v1/endpoints/`, `app/services/{domínio}/`, `app/schemas/{domínio}/`, `app/db/models/`) | Rotas e status, regras, campos e validações, tabelas e constraints |
| Frontend (`frontend/src/modules/{módulo}/`) | `routes.ts` (rotas e permissões), `views/` e `components/` (telas e textos), `schemas/` (validação) |
| Migrações (`backend-fastapi/alembic/versions/`) | Revisões do módulo |
| Testes (`backend-fastapi/test/`, `*.spec.ts`) | Arquivos e contagem real (§3.2) |
| `SUMMARY.md` dos módulos vizinhos | A coluna "não é dono de" e os links entre módulos |

## 2. Preparar

1. **Módulo e nome.** Identifique o módulo do Harness e o nome em PT-BR para título. Na dúvida, pergunte.
2. **Escopo dos artefatos.** Módulos de infraestrutura sem regra de negócio própria (`mainLayout`, `network-config`, `shared`) normalmente têm só a Documentação Técnica. Confirme com o usuário antes de pular algum artefato.
3. **Modo: criar ou atualizar.** Procure os arquivos em `@/docs/{módulo}/handbook/` (`visao-geral.md`, `negocio.md`, `tecnico.md`).
   - Se existirem, use o **modo atualizar**: leia os três por inteiro antes de escrever. Eles definem os IDs já publicados (§4.3) e os trechos escritos à mão que precisam ser preservados.
   - Se não existirem, use o **modo criar** (crie a pasta `handbook/`).
4. **Prefixo dos IDs.** Use o prefixo dos arquivos já existentes. No modo criar, use o nome do módulo em maiúsculas (`CLIENTE`, `VENDA`, `FISCAL`) e confirme com o usuário.

## 3. Levantar os fatos

### 3.1. Tabela de fatos (rascunho de trabalho, no scratchpad)

Antes de redigir, monte a lista de fatos com a fonte de cada um:

```markdown
| # | Fato | Fonte | Artefatos |
|---|------|-------|-----------|
| 1 | CPF duplicado na mesma empresa é recusado | `services/cliente/cadastro.py` · Spec 03 §4 | N, V, T |
| 2 | A lista mostra 20 clientes por página | `schemas/comum/paginacao.py` · `useCustomers.ts` | N, T |
```

Os fatos de negócio vêm das specs, do acordo e das ADRs. Os valores (prazos, limites, mensagens, códigos) são conferidos no código: o número e o texto do documento são os do código.

### 3.2. Números medidos, não lembrados

Contagens e listas saem de comandos, nunca da memória ou de uma spec antiga:

```bash
# Quantos testes existem do domínio (backend-fastapi/, venv ativa)
python -m pytest test/ -k "cliente" --collect-only -q | tail -1
```
```bash
# Testes do módulo no frontend (frontend/)
npx vitest run src/modules/customers
```
```bash
# Revisões de migração (backend-fastapi/, banco descartável via DATABASE_URL)
alembic history
```

Se um comando falhar por ambiente, escreva o número com "aproximadamente", a partir de `grep -c "def test_"`, e registre no relatório como "não verificado".

### 3.3. Lacunas

Algumas informações não estão no repositório: atores externos, avisos de lançamento, o "Para quem é" da Visão Geral. Junte as lacunas e pergunte **em um único lote**, com uma recomendação para cada. Não preencha lacunas por dedução.

## 4. Redigir

Escreva os três rascunhos em Markdown em `@/docs/{módulo}/handbook/` (`negocio.md`, `tecnico.md`, `visao-geral.md`) a partir dos modelos. Ordem: **Negócio → Técnica → Visão Geral**. A Negócio define os IDs que as outras citam, e a Visão Geral resume as duas.

### 4.1. Cabeçalho comum

- **Títulos:** `📐 Especificação de Negócio · <Módulo>`, `🧭 Visão Geral · <Módulo>`, `⚙️ Documentação Técnica · <Módulo>`.
- **Aviso de abertura** (citação `>`): diz em qual artefato a pessoa está, para que ele serve, e traz o link dos outros dois (caminhos relativos entre os arquivos de `handbook/`, e para o `handbook/` do módulo vizinho).
- **Metadados:** módulo (com o nome do código), situação, público e "Atualizado em" (data de hoje, `DD/MM/AAAA`).
- **Seção que não se aplica ao módulo é removida, nunca deixada vazia.** A numeração é refeita no modo criar e mantida no modo atualizar.

### 4.2. Regras de escrita por artefato

**Visão Geral**
- Sem jargão técnico: nada de token, endpoint, tabela ou nome de arquivo. Os nomes de tela e de botão ficam entre aspas, como aparecem na interface.
- "Em 30 segundos" abre com uma comparação do dia a dia da loja ou da oficina (ex.: "o caixa da loja", "a ficha de serviço").
- As jornadas são numeradas e escritas do ponto de vista de quem usa, com dicas práticas.
- As perguntas rápidas respondem às dúvidas reais de suporte, em uma ou duas frases cada.
- Cabe em 2 a 3 páginas. O detalhe fica nos outros artefatos, com link.

**Especificação de Negócio**
- Sem termos de implementação (JWT, HTTP, tabela, nomes de classe). A regra diz **o que** acontece, não como.
- Cada regra é atômica, verificável por QA e tem ID `RN-<PREFIXO>-NN`. Os casos de uso usam `UC-<PREFIXO>-NN` e citam as regras pelo ID.
- "Responsabilidades" tem duas colunas: do que o módulo é dono e do que não é, com link para o módulo dono.
- "Mensagens ao usuário" traz o texto **exato** da interface ou da API.
- Os prazos e limites são os valores do código, com a unidade.
- As decisões de negócio resumem cada ADR (contexto, decisão, consequências aceitas, como reverter) com a data de aceite.
- **Regra fiscal ou financeira** cita a origem (norma, documento do usuário); sem origem, vai para "Lacunas".

**Documentação Técnica**
- Os identificadores são copiados do código (rotas, colunas, constraints, mensagens de erro, variáveis de ambiente, nomes de teste).
- Estrutura de pastas e padrões gerais pertencem às `rules/`. Descreva só o que o módulo usa ou acrescenta e aponte para o resto.
- Os fluxos são passos numerados ou diagramas ASCII (blocos de código), com o status de cada desvio.
- A tabela de erros traz status, quando ocorre e a mensagem ao usuário, conferidos no código.
- "Configuração" lista nome, padrão e regra de cada variável, a partir do `core/config.py`. Nunca traz valores reais.
- "Histórico de construção" tem uma linha por spec concluída, na ordem do índice de specs.

### 4.3. IDs estáveis

- Um ID publicado nunca muda de número nem é reaproveitado.
- Regra removida: fica riscada (`~~RN-CLIENTE-12~~`) com o motivo e a data.
- Regra nova: recebe o próximo número livre e entra no grupo certo, mesmo fora da ordem numérica.
- Regra alterada: mantém o ID e ganha a data da mudança na própria linha (`(alterada em DD/MM/AAAA)`).

### 4.4. Checklist antes de mostrar

- [ ] Todo fato da tabela do §3.1 tem fonte, e toda RN é rastreável a uma spec, ADR ou trecho de código.
- [ ] As mensagens, prazos, limites e rotas batem com o código (conferidos por `grep`, não de memória).
- [ ] As contagens de testes e as revisões de migração saíram de comandos (§3.2) ou estão marcadas como aproximadas.
- [ ] Nenhuma regra está redigida em dois artefatos. A Visão Geral e a Técnica citam ou linkam a Negócio.
- [ ] "Fora do escopo" e "Limitações" dizem a mesma coisa nos três artefatos.
- [ ] A situação e as specs batem com o `SUMMARY.md` do módulo, e a data de "Atualizado em" é a de hoje.
- [ ] A Visão Geral não tem jargão, e a Negócio não tem termos de implementação.
- [ ] Nenhum segredo, valor de `.env`, caminho de banco de cliente ou dado pessoal real.
- [ ] No modo atualizar: nenhum ID renumerado, e os trechos escritos à mão foram preservados ou a remoção foi listada no relatório.

## 5. Revisar e entregar

### 5.1. Revisão do usuário

Entregue os três rascunhos como arquivos e o relatório (§6). No modo atualizar, mostre também o que muda em cada arquivo (seções novas, regras alteradas ou removidas). Espere a aprovação. Pedidos de ajuste voltam ao §4.

### 5.2. Publicação externa (opcional, só se o usuário pedir)

Os arquivos em `@/docs/{módulo}/handbook/` já são a entrega. Se o usuário quiser publicar em outra ferramenta (wiki, drive, gerenciador de tarefas), faça só depois da aprovação, **uma vez**, e confira o resultado aberto. Se o conector falhar duas vezes com o mesmo sintoma, pare (`@/AGENT.md` §7) e deixe os arquivos como entrega.

## 6. Relatório ao usuário

- Módulo, modo (criar ou atualizar) e artefatos produzidos.
- Caminho dos arquivos gerados.
- No modo atualizar: regras novas, alteradas e removidas, por ID.
- Fontes principais lidas.
- Divergências entre spec e código encontradas, com a decisão do usuário.
- O que ficou "não verificado" (contagens aproximadas, links de módulos sem handbook) e por quê.
- Lacunas que dependem do usuário ou do cliente.
