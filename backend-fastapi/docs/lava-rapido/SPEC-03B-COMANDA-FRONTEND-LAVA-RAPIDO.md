# Spec 03B — Comanda "Nova entrada" (Frontend)

| Campo        | Valor                                                                 |
|--------------|-----------------------------------------------------------------------|
| Status       | Implementada em 12/11/2026 (aguardando o usuário olhar as telas)       |
| Camada       | Frontend ⚠️ página de Serviços, abertura de OS                         |
| Dependências | Specs 02A/02B, 03A, 10A                                               |
| Referência   | SPEC-00 Revisão 4: U1, U2, U4, U5, U6 · PR10                           |

---

## 1. Objetivo

Abrir uma lavagem numa **tela só**, na ordem do balcão, em ≤ 30 s para quem já veio:

**placa** → veículo e dono aparecem → **tipo** → **porte** → **serviços** com o preço do porte → **lavador** → **avarias** e fotos → **Entrar no pátio**.

## 2. Tela (`modules/lava-rapido/comanda/components/ComandaModal.vue`)

| Bloco | Como funciona |
|---|---|
| Placa | Normalizada (maiúscula, sem hífen). Com 7+ caracteres procura o veículo (`/ordens-servico/objeto/buscar`); achou → "Já veio aqui", preenche modelo, marca, cor, dono, tipo e porte. Bicicleta/Outros: "Placa (se tiver)" |
| Cliente | Achado pela placa, ou busca por nome/telefone/CPF, ou **Cliente novo** (nome + celular, criado ao entrar) |
| Veículo | Botões de tipo e de porte (portes ativos da loja); modelo obrigatório, marca opcional, cor |
| Serviços | Botões com o preço do porte (02A); escolher troca o total; trocar o porte reaplica os preços |
| Lavador | Até 2, em botões; o **1º é o responsável** da OS |
| Avarias | Checklist do tipo (03A) + fotos (câmera no celular) |
| Observação | Vira `pertences` e o texto do pedido |
| Resumo | Itens, total e "Pronto às HH:MM" (soma das durações) |

## 3. Decisões

| # | Decisão | Por quê |
|---|---|---|
| D1 | Abre pela rota de OS de **sempre**, com payload próprio (`comanda.service.ts`), sem o schema do formulário de OS | Aquele exige técnico; a comanda pode abrir sem responsável |
| D2 | Ordem: cliente novo → OS → lavadores → fotos. Lavador ou foto que falhar **não desfaz** a OS (já está no pátio): vira aviso | Nunca deixar o atendente sem saber se o carro entrou |
| D3 | `defeito_relatado` (obrigatório) = observação, senão os nomes dos serviços | O campo continua útil na via e no histórico |
| D4 | 1º lavador = responsável (`funcionario_id`) | Na loja pequena, quem abre é quem lava (cliente, 12/11) |
| D5 | Na aba **Ordens de Serviço** do lava-rápido, "Nova OS" também abre a comanda; a OS de abas fica para "Ver detalhes" | SPEC-00 U6 |
| D6 | "Entrar e imprimir" fica para depois: o primeiro cliente não imprime; a via sai pelo "Ver detalhes" | Menos código no piloto; a impressão já existe na OS |

## 4. Casos de teste

`comanda/__tests__/comanda.service.spec.ts` (5) e `shared/__tests__/lavaRapido.spec.ts` (11): payload da OS (itens do catálogo, tipo, avarias, previsão, porte novo sem perder o resto, sem responsável, observação), texto do pedido, placa, WhatsApp, previsão, tempo no pátio.
`views/__tests__/OrdemServicoView.abas.spec.ts`: Pátio primeiro com "Nova entrada"; na lista de OS também; outros segmentos sem Pátio.

### Roteiro manual
1. Nova entrada com placa nova → cliente novo → Carro → SUV → Lavagem + Cera → lavador → 1 avaria → Entrar. Ver no pátio.
2. Nova entrada com a mesma placa → "Já veio aqui", dono e porte preenchidos.
3. Bicicleta sem placa → entra com `VEI-…`.
