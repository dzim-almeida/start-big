# Respostas reais da API do orçamento (cenário B da Spec 05)

Estes JSON foram **gerados pela API da Spec 06A** (TestClient, banco em memória),
não escritos à mão: o cenário B montado pelos ajudantes de
`backend-fastapi/test/apoio_orcamento_marcenaria.py` (`montar_cenario_b`), lido
como master (`*-com-custos`) e como vendedor sem `view_custos_marcenaria`
(`*-sem-custos`).

Servem para os testes do frontend conferirem os schemas zod contra o que o
backend DE VERDADE devolve (`orcamentoDetalhe.schema.spec.ts`). Se o contrato
da API mudar, gere de novo (mesmo cenário) em vez de editar à mão.
