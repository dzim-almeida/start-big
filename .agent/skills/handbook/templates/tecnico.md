# ⚙️ Documentação Técnica · <Módulo>

> **Você está na Documentação Técnica.** Aqui está como o módulo foi construído, para quem mantém o código.
> Regras de negócio (IDs `RN-...`): [Especificação de Negócio](./negocio.md) · Em linguagem simples: [Visão Geral](./visao-geral.md)

| | |
|---|---|
| **Módulo** | <Módulo> (`<módulo>`) |
| **Situação** | <Implementado> |
| **Código** | `frontend/src/modules/<módulo>/` · `backend-fastapi/app/{endpoints,services,db/crud,schemas}/<domínio>` |
| **Atualizado em** | <DD/MM/AAAA> |

---

## 1. Escopo e responsabilidades

<O que o módulo faz e o que deixa para outros módulos (com link para a Documentação Técnica deles).>

---

## 2. Stack

| Camada | Tecnologia | Uso no módulo |
|--------|------------|---------------|
| <Camada> | <Tecnologia> | <Uso específico> |

---

## 3. Arquitetura

### 3.1. Backend

<Arquivos do módulo por camada: endpoint, service, crud, schema, model. Só o que é do módulo.>

### 3.2. Frontend

<Views, components, composables, services e schemas do módulo.>

---

## 4. Modelo de dados

### 4.1. Diagrama

```
<diagrama ASCII ou mermaid das tabelas e relações>
```

### 4.2. `<tabela>`: <papel>

| Coluna | Tipo | Regras |
|--------|------|--------|
| `<coluna>` | <TIPO> | <constraint, nome da constraint, RN relacionada> |

### 4.N. Migrações

| Revisão | Descrição |
|---------|-----------|
| `<hash>` | `<mensagem>`: <o que muda> |

---

## 5. <Mecanismos do domínio>

<Cálculos, algoritmos e integrações próprios do módulo (ex.: cálculo de preço, emissão fiscal).>

| Item | Valor | Origem |
|------|-------|--------|
| <Item> | <Valor> | `<constante ou variável>` |

---

## 6. API

### 6.1. Endpoints

| Método e rota | Permissão | Resposta de sucesso |
|---------------|-----------|---------------------|
| `<MÉTODO> /api/v1/<rota>` | `<permissão>` | `<status>` + `<Schema>` |

### 6.N. Erros

| Status | Quando | Mensagem ao usuário |
|--------|--------|---------------------|
| `<status>` | <condição> | "<texto exato>" |

---

## 7. Fluxos

### 7.1. <Fluxo>

1. <Passo>
2. <Passo>
3. <Desvio: condição → status/erro>

---

## 8. Autorização e isolamento entre empresas

<Como `empresa_id` é aplicado, qual permissão cada rota exige, como o `404` de outra empresa é garantido e qual teste prova.>

---

## 9. Contrato com outros módulos

<Funções de service, schemas compartilhados ou stores que outros módulos consomem.>

---

## 10. Frontend

### 10.1. Rotas

| Rota | Nome | Meta |
|------|------|------|
| `/<rota>` | `<name>` | <permissões> |

### 10.2. Telas

| Tela | Componentes | Detalhes |
|------|-------------|----------|
| <Tela> | `<View>`, `<Component>` | <comportamentos relevantes> |

---

## 11. Segurança: ameaças e mitigações

| Ameaça | Mitigação |
|--------|-----------|
| <Ameaça> | <Mitigação no módulo> |

---

## 12. Configuração

| Variável | Padrão | Regras |
|----------|--------|--------|
| `<VARIÁVEL>` | <padrão do `config.py`> | <validação> |

---

## 13. Observabilidade

<O que é registrado em log (e o que nunca é registrado), onde ver (`rede.log`, console do backend).>

---

## 14. Testes

### 14.1. Backend

| Arquivo | Cobertura |
|---------|-----------|
| `<test_x.py>` | <o que cobre> |

Total: <N> testes (conferido em <AAAA-MM-DD> com `python -m pytest --collect-only`).

### 14.2. Frontend

| Arquivo | Cobertura |
|---------|-----------|
| `<x.spec.ts>` | <o que cobre> |

---

## 15. Operação

<Impacto na instalação do cliente: migração aplicada no startup, necessidade de regerar o sidecar, passo manual de implantação.>

---

## 16. Limitações conhecidas e evolução

| Item | Situação |
|------|----------|
| <Item> | <Situação e caminho de evolução> |

---

## 17. Histórico de construção

| Spec | Entrega |
|------|---------|
| <NN> | <Entrega> |
