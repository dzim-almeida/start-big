# NFS-e — plano de melhoria das telas (revisão do Alan, 29/10/2026)

Origem: o Alan percorreu as telas da NFS-e no app instalado (instalador de
29/10, `feat/nfse` + G8) e anotou o que confunde. Este plano junta as anotações,
o que o código mostrou e a nota real dele (DANFSe nº 23, MEI, Iguatu/CE).

Regras de sempre: nada muda para quem não tem o módulo NFSE; NF-e e NFC-e não
são tocadas; colunas do banco não saem (só deixam de aparecer na tela); cada
fase com testes e `vue-tsc`, e o instalador sai da branch da fase.

---

## O que foi visto (resumo)

| # | Tela | Problema | Origem |
|---|---|---|---|
| A | Emitir NFS-e | Só acha a OS pelo número inteiro (`OS-2026-000158`); "158" não acha | Alan |
| B | Editar serviço › Dados fiscais | Campos demais; não explica o que é cada um; IBS/CBS confunde | Alan |
| C | Editar serviço | **CFOP, CST ICMS e Unidade tributável não são lidos por nota nenhuma** (campos de produto) | código |
| D | Editar serviço | LC 116 é digitado à parte, mas está dentro do código nacional (01.07.01 → 01.07) | código |
| E | Novo serviço | Dado fiscal só depois de salvar o serviço | Alan |
| F | Novo serviço | Serviços parecidos repetem os mesmos dados fiscais à mão | Alan |
| G | Lista de serviços | Clicar no serviço abre **Detalhes** com tudo bloqueado; editar só pelo lápis pequeno da linha. O Alan nem chegou a testar a busca por palavra | Alan + código |
| H | Centro Fiscal | Cartão "Emissão Municipal (NFS-e)" ainda diz **Em breve** | Alan |
| I | — | Ver como outros sistemas fazem o cadastro de serviço e a busca de códigos | Alan |

Achados da DANFSe real (servem ao G9a): **IBS/CBS vazio** (não é obrigatório
para MEI em 2026); **série da DPS 70000**, nº 23; ISS sem alíquota/base, não
retido; "Optante MEI"; tomador de outra cidade, prestação em Iguatu — tudo
igual ao que a nossa DPS manda.

---

## Fase M0 — Tirar as dúvidas (sem código) · ~meio dia

1. **Busca por palavra (G).** O Alan não chegou a testar: a linha da lista
   abre o serviço em modo leitura (`useServicoModal` → `view`). O servidor acha
   "suporte tecnico informatica" (teste passa) e o campo tem teste próprio;
   conferir no app, em **Editar**, se a lista aparece digitando palavras. Se
   não aparecer, a correção entra na M1. Perguntar também onde apareceu o
   aviso: era o **CNAE** (o Alan corrigiu a sigla) — ver M1.7.
2. **Pesquisa de mercado (I).** Emissor público (nfse.gov.br), e 3–4 ERPs que
   emitem NFS-e (ex.: Bling, Omie, Conta Azul, eNotas): como é o cadastro do
   serviço, que campos aparecem, como sugerem código/NBS, se têm "modelo
   fiscal". Saída: uma página com prints/links e o que vale copiar.
3. **Série 70000 (G9a).** Ver na Focus qual série a NFS-e Nacional dela usa
   (`proximo_numero_nfsen_*`/série no cadastro da empresa) para não colidir
   com a numeração que o Alan já tem no portal (DPS 70000, nº 23).

### Resultado da M0.2 — pesquisa (29/10/2026)

| Sistema | Onde mora o fiscal | Escolha dos códigos | Reaproveitar |
|---|---|---|---|
| Emissor do governo | formulário por nota | lista LC 116 com busca por prefixo ("pint" acha pintura) | não confirmado (guia em PDF não lido) |
| Omie | cadastro do serviço, em abas; Reforma só libera com código válido | digitado; tabela da Sefin como consulta à parte | o cadastro do serviço alimenta OS/contratos; validador em lote na migração para a Nacional |
| Conta Azul | cadastro do serviço; **serviço vence a configuração da empresa** | NBS/cClassTrib com bloco **"Mais usados neste serviço"** a partir do LC 116 + catálogo completo; avisa que a sugestão não valida nada | "replicar impostos" entre cadastros (só título lido) |
| eNotas | **na empresa** (dados municipais); campos mudam pelo porte — **MEI não vê alíquota ISS nem campos do Simples** | digitado | o padrão da empresa vale para tudo |
| NFE.io | API: só o código de serviço; o resto é calculado | — | — |
| Bling | ajuda bloqueada (403) | — | — |

O que confirma o plano: padrão na empresa + serviço sobrescreve (decisão 2,
igual Conta Azul/eNotas); esconder pelo porte (M1.3, igual eNotas); sugestão a
partir do código, sem travar (o nosso "NBS sugeridos" já é o "mais usados" da
Conta Azul); ordem guiada (código nacional primeiro, depois NBS e IBS/CBS).
Ideia nova: busca por **prefixo de palavra** ("manut" acha manutenção), como no
gov.br — conferir se o nosso motor já faz (M0.1).

Série (M0.3, indício): o eNotas informa faixas de série da DPS por tipo de
emissor (1–49.999 com certificado A1; 80.000–89.999 com usuário e senha). A
do Alan (emissor público) é 70.000 — a emissão pela Focus, com certificado,
cai noutra faixa. Confirmar na homologação.

## Fase M1 — Cadastro do serviço mais simples · ~1 dia · risco baixo

1. **Tirar da tela** CFOP, CST ICMS e Unidade tributável do serviço (C). As
   colunas ficam no banco; nenhuma nota lê esses campos do serviço.
2. **LC 116 automático** a partir do código nacional (D): escolheu 01.07.01,
   o campo vira 01.07 (editável, para a rota municipal que pedir outro).
3. **Mostrar só o que a nota da empresa precisa**, pela rota do G6
   (`GET /erp/fiscal/nfse/municipio`, já em produção):
   - Nacional (MEI): Código nacional + NBS — e só;
   - Municipal: + Código tributário municipal e CNAE **quando a cidade exige**;
   - Alíquota ISS: só regime normal (MEI/Simples não informa);
   - IBS/CBS: recolhido em "Avançado — opcional em 2026", com o texto "a sua
     nota de MEI sai sem isso".
4. **Ajuda em português simples**, campo a campo, apontando onde o dado
   aparece na nota que o lojista já emite ("na sua nota: Código de Tributação
   Nacional 14.01.01").
5. **Abrir para editar (G):** clicar no serviço abre direto a edição (ou o
   "Detalhes" ganha um botão **Editar** visível). Hoje só o lápis da linha edita.
6. Se a M0.1 achar defeito na busca, a correção entra aqui.
7. **Aviso do topo errado:** "Os campos Código LC 116 e CNAE são os mais
   importantes" — para MEI/Nacional os que importam são **Código nacional + NBS**;
   CNAE só vale na rota municipal quando a cidade exige. O aviso passa a dizer o
   que a rota da empresa pede (mesma regra do item 3).

## Fase M2 — Cadastrar uma vez, reaproveitar · ~1–2 dias · risco baixo

1. **Dados fiscais já no "Novo Serviço"** (E), quando o módulo NFSE está
   ligado: salva o serviço e o fiscal na mesma ação (o front encadeia o
   cadastro e o `PUT /servicos/{id}/fiscal`; sem migração).
2. **Reaproveitar** (F):
   - "Copiar dados fiscais de…" (escolhe outro serviço);
   - **Padrão fiscal da loja** na Configuração da NFS-e (código nacional, NBS,
     ISS): serviço novo já nasce com ele, e a pessoa só troca o que muda.
3. **Sugerir o código pela descrição** (se a M0.1 confirmar): ao sair do campo
   Descrição ("Visita técnica com instalação"), mostrar 2–3 códigos prováveis
   com a mesma busca do código nacional; um clique preenche código e NBS.

## Fase M3 — Achar a OS na emissão · ~1 dia · risco baixo

1. Campo da OS aceita **só o número** ("158") e completa o resto; aceita
   também nome do cliente.
2. Melhor ainda: **lista das OS finalizadas sem NFS-e** para clicar, com
   cliente, data e valor dos serviços — ninguém precisa digitar.
3. Conferir antes qual busca de OS já existe no backend (reaproveitar).

## Fase M4 — Centro Fiscal · ~meio dia · risco baixo

1. Cartão "Emissão Municipal (NFS-e)" (H) deixa de ser "Em breve": mostra a
   situação real — módulo, rota (Nacional/Municipal/esperando o suporte),
   cidade — e o botão leva à Configuração da NFS-e / aba NFS-e.

---

## Ordem sugerida

M0 → M1 → M4 → M2 → M3. M1 e M4 tiram a confusão que o Alan viu primeiro e
são as menores; M2 e M3 mudam o fluxo e merecem a pesquisa da M0.2 antes.
O G9a (homologação real) pode correr em paralelo assim que o módulo NFSE
estiver na licença do Alan.

## Decisões do Alan (29/10/2026)

1. CFOP, CST ICMS e Unidade tributável do serviço: **tirar de vez** da tela
   (colunas ficam no banco).
2. Reaproveitamento: **um padrão fiscal da loja + "Copiar de outro serviço"**.
3. Emitir NFS-e: **lista das OS finalizadas sem NFS-e para clicar** (aceitando
   também "158" e nome do cliente) já na primeira versão.
4. Pesquisa: **emissor do governo (nfse.gov.br), Bling, Omie, Conta Azul,
   eNotas, NFE.io**.
