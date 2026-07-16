# Segmento: assistência técnica (informática)

Pasta intencionalmente vazia — é o **destino** dos campos de TI que hoje ainda
moram hardcoded dentro do núcleo, em `ordens/components/form/OSObjetoTab.vue`
(IMEI, senha do aparelho, acessórios, condições físicas).

## Por que ela existe vazia

Hoje esses campos são renderizados por negação: `v-if="!isOficinaMecanica"`.
Ou seja, a regra efetiva não é "assistência técnica mostra IMEI", e sim
"todo mundo que não é oficina mostra IMEI". Quando um terceiro segmento for
ligado (mercado, marcenaria...), ele vai herdar a tela de TI sem ninguém pedir.

A oficina já é dirigida por metadados: lê `GET /ordens-servico/definicao-campos`
e renderiza sozinha (ver `segmentos/oficina/` e `shared/segmento/`). A assistência
técnica ainda não — o registry do backend (`app/core/segmentos.py`, `_ASSISTENCIA`)
até **descreve** os campos dela, mas ninguém consome; é documentação, não contrato.

## O que falta

Extrair os campos de TI daqui para um componente próprio, dirigido pelo mesmo
contrato que a oficina usa. Aí `OSObjetoTab` deixa de conhecer segmento algum e
a negação desaparece — cada segmento passa a declarar o que mostra.

Isso mexe em código de produção (informática é o primeiro cliente em uso), por
isso foi deliberadamente separado do commit que criou estas pastas.
