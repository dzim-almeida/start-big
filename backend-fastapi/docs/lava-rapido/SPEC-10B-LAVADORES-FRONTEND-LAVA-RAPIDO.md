# Spec 10B — Lavadores e Comissão Dividir/Inteira (Frontend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (aguardando o usuário olhar as telas)       |
| Camada       | Frontend ⚠️ cadastro de cargo e de funcionário                         |
| Dependências | Spec 10A                                                              |
| Referência   | SPEC-00: O7a, O7c                                                      |

---

## O que muda (só com a capacidade `executores_os`)

- **Comanda e pátio:** escolha de até 2 lavadores em botões (`SeletorLavadores.vue`); no pátio, clicar nos lavadores do cartão troca.
- **Cargo:** "Quando a lavagem tiver mais de um lavador" → **Dividir** (padrão) ou **Inteira**.
- **Funcionário:** o mesmo, com **Herdar do cargo** (cascata, como o modo de comissão).
- Formulários de cargo e funcionário levam `comissao_divisao` exatamente onde já levam `comissao_modo` (valores iniciais, carga, envio, schema e tipos).

## Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Seletor compartilhado `SeletorDivisaoComissao.vue` no módulo do lava | Uma tela só para os dois cadastros |
| D2 | No cargo, vazio aparece como Dividir (o padrão do backend) | O dono não precisa escolher para valer o comum |
| D3 | Nos outros segmentos o bloco não aparece; o campo vai `null` | PR1 |
