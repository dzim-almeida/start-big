# 📐 Especificação de Negócio · <Módulo>

> **Você está na Especificação de Negócio.** Aqui estão as regras que o sistema **precisa** cumprir, numeradas para QA, produto e implantação.
> Em linguagem simples: [Visão Geral](./visao-geral.md) · Como foi construído: [Documentação Técnica](./tecnico.md)

| | |
|---|---|
| **Módulo** | <Módulo> (`<módulo>`) |
| **Situação** | <Implementado> (<Specs NN a NN>) |
| **Público** | Produto, QA, engenharia e implantação |
| **Atualizado em** | <DD/MM/AAAA> |

---

## 1. Objetivo

<O problema de negócio que o módulo resolve, em 3 a 5 linhas.>

---

## 2. Responsabilidades

| ✅ <Módulo> é dono de | 🚫 Não é dono de (fica com [<Outro módulo>](../../<outro-módulo>/handbook/negocio.md)) |
|---|---|
| <Responsabilidade> | <Responsabilidade do outro módulo> |

---

## 3. Atores

| Ator | Quem é | O que faz neste módulo |
|------|--------|------------------------|
| **<Ator>** | <Quem é na loja/oficina> | <Ações neste módulo> |

---

## 4. Entidades de negócio

| Entidade | Definição |
|----------|-----------|
| **<Entidade>** | <Definição sem termos técnicos> |

---

## 5. Regras de negócio

### 5.1. <Grupo de regras>

| ID | Regra |
|----|-------|
| **RN-<PREFIXO>-01** | <Regra atômica e verificável, com os pontos-chave em **negrito**> |

---

## 6. Casos de uso

### UC-<PREFIXO>-01 · <Nome>

- **Ator:** <ator>
- **Pré-condição:** <o que precisa ser verdade antes>
- **Fluxo principal:** 1. <passo> 2. <passo> 3. <resultado>
- **Fluxos alternativos:** <situação> → <o que acontece> (RN-<PREFIXO>-NN)

---

## 7. Ciclo de vida

<Estados do registro e as transições permitidas (ex.: Aberto → Em andamento → Concluído). Use uma tabela ou um diagrama em texto.>

---

## 8. Mensagens ao usuário

| Situação | Mensagem |
|----------|----------|
| <Situação> | "<Texto exato da interface ou da API>" |

---

## 9. Campos de <formulário>

| Campo | Obrigatório | Regra |
|-------|-------------|-------|
| <Campo como aparece na tela> | <Sim/Não> | <Regra ou RN-<PREFIXO>-NN> |

---

## 10. Prazos e limites

| Item | Valor |
|------|-------|
| <Item> | <Valor com unidade> |

---

## 11. Decisões de negócio

### ADR-<NNN> · <Título>

- **Aceita em:** <DD/MM/AAAA>
- **Contexto:** <por que a decisão foi necessária>
- **Decisão:** <o que foi decidido>
- **Consequências aceitas:** <o que o negócio aceita conviver>
- **Como reverter:** <caminho, se houver>

---

## 12. Fora do escopo atual

- <Item> — <onde está registrado / quando pode entrar>
