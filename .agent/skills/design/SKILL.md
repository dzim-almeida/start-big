---
name: design
description: Implementa telas e componentes do StartBig com máxima fidelidade a um design de referência (protótipo, imagem ou tela já existente), usando os tokens do tema, os componentes Base* de shared/components/ui e os scripts check:* do projeto. Termina com verificação visual e relatório de fidelidade. Use ao criar ou ajustar telas e componentes visuais.
---

# Skill `design` — fidelidade ao design de referência

> Caminhos com `@/` são relativos a `.agent/`. Comandos de frontend rodam em `frontend/`.

## 0. Fontes, em ordem de autoridade

1. **Instrução do usuário** na conversa (ex.: "igual à tela X", "troque a cor do botão").
2. **O design de referência** que o usuário forneceu: imagem, PDF, protótipo ou link. Ele manda em **estrutura, textos, espaçamento e hierarquia**.
3. **Os tokens e componentes do projeto**: o design se traduz para o que já existe, em vez de criar valores novos.
   - Tokens (cores, raios, sombras, fontes): `frontend/src/shared/theme/` e `frontend/src/shared/assets/styles/`.
   - Componentes: `frontend/src/shared/components/ui/` (`BaseButton`, `BaseInput`, `BaseSelect`, `BaseMoneyInput`, `BaseStatusPill`, `BaseTab`...), `form/`, `layout/`, `commons/`.
4. **Telas já prontas parecidas** (outros módulos) como exemplo de composição.

Se a referência e os tokens divergirem (a cor do design não existe no tema), **não invente valor**: use o token mais próximo e registre na §4, ou pergunte.

Sem design de referência (pedido só em palavras): descreva em 3–5 linhas o que vai construir, mostre ao usuário **antes** de codar telas novas e siga os padrões das telas existentes do módulo.

---

## 1. Entender o design antes de codar

### 1.1. Achar a referência

- Peça (ou localize) o arquivo/imagem. Se vier PDF/imagem, abra e leia cada região.
- Se a tela já existe parcialmente, abra **o `.vue` atual** e a rota (`modules/{módulo}/routes.ts`) para saber o que muda.

### 1.2. Montar o inventário

Antes de escrever código, liste em uma tabela o que a tela tem:

| Região | Elemento | Componente do projeto | Observação |
|--------|----------|-----------------------|------------|
| Cabeçalho | Título + botão "Novo" | `BaseButton` (variante primária) | texto exato da referência |
| Corpo | Tabela de itens | tabela do módulo | colunas, ordem, alinhamento |
| Rodapé | Totais | componente novo? | |

Inclua **todos os estados**: carregando, vazio, erro, com dados, desabilitado, foco, modal aberto.

---

## 2. Implementar

1. **Estrutura primeiro** (`views/` monta, `components/` desenha, `composables/` pensa; ver `@/rules/frontend-architecture.md`).
2. **Componentes `Base*`** em vez de HTML cru. Precisa de variação nova → proponha ajustar o `Base*`.
3. **Tokens, não valores soltos:** nada de `#3b82f6`, `margin: 13px` ou `font-size: 15px` no componente. Classe do Tailwind ligada ao tema (`bg-brand-primary`, `text-neutral-700`...). Valor arbitrário (`w-[437px]`) só quando o design exige medida exata e **com comentário dizendo por quê**.
4. **Textos exatamente** como na referência (acentuação, maiúsculas, pontuação). Texto vem de constante quando se repete.
5. **Responsivo e janela do app:** o app roda numa janela Tauri redimensionável. Confira a largura mínima suportada e o que acontece abaixo dela (quebra de linha, rolagem horizontal da tabela).
6. **Impressão:** tela/etiqueta/recibo que imprime precisa funcionar em **preto e branco** (`npm run check:print-bw`). Não dependa de cor para transmitir informação impressa.
7. **Acessibilidade mínima:** `label` ligado ao campo, foco visível, botão de ícone com `aria-label`, contraste legível.
8. **Comente o código** de forma simples: o que cada bloco do template e do `<script setup>` faz.

### 2.1. Tailwind 4: cores e cursor

- No Tailwind 4, a classe `bg-brand-x` só existe se `--color-brand-x` estiver declarada no `@theme`. Se a variável não existe, **a classe some em silêncio** (o elemento fica sem fundo). O `npm run check:tokens` pega isso no build: rode-o depois de usar um token novo.
- `check:paleta` confere a paleta permitida. Rode se mexeu em cores.
- Botão e item clicável precisam de `cursor-pointer` explícito (o preflight do Tailwind 4 não coloca).

---

## 3. Verificação visual (obrigatória)

1. Suba o frontend (`npm run dev`, porta **1420**) e o backend de dev (porta **8000**, ver `CLAUDE.md` e skill `verify` §1).
2. Abra a tela e compare **lado a lado** com a referência: estrutura, alinhamento, espaçamento, tamanhos de texto, cores, bordas, sombras.
3. Percorra os **estados** do inventário (vazio, erro, carregando, desabilitado, foco, modal).
4. Teste a largura mínima da janela e uma largura grande.
5. Rode: `npm run check:tokens`, `npm run check:paleta`, `npm run check:print-bw` (se aplicável), `npx vue-tsc --noEmit` e `npm run lint:check`.
6. Componente novo em `shared/components/ui/` → story em `*.stories.ts` e conferência no `npm run storybook` (porta 6006).
7. Se não conseguiu ver a tela (painel do navegador/Tauri sem resposta), registre como **"não verificado"** no relatório; não declare fidelidade sem ter olhado.

---

## 4. Divergências

Registre toda diferença entre a referência e o resultado, com o motivo:

- token mais próximo usado no lugar de cor inexistente;
- componente `Base*` que não suporta a variação pedida;
- elemento do design sem dado no backend (campo ainda não existe → vira pendência ou spec nova, **não** inventar dado).

Divergência que exige mexer em `shared/`, tema ou backend é **divergência de escopo** (`AGENT.md` §7): pergunte antes.

---

## 5. Relatório final

```markdown
### Fidelidade — <Tela ou componente>
- Referência usada: <arquivo/imagem/link>
- Componentes reaproveitados: BaseButton, BaseInput, ...
- Estados conferidos: vazio ✅ · erro ✅ · carregando ✅ · modal ✅
- Verificações: check:tokens ✅ · check:paleta ✅ · vue-tsc ✅ · lint ✅
- Divergências: <lista com motivo> | nenhuma
- Não verificado: <o que e por quê> | nada
```
