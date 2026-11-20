# Spec que muda algo compartilhado esquece quem o consome

- **Data:** 2026-11-20
- **Módulo:** licenca (vale para qualquer módulo)
- **Spec relacionada:** LIC-04 (modal sem `v-html`), LIC-08 (envio para a nuvem)
- **Tipo:** armadilha

## Contexto
A LIC-04 dizia que só 2 telas mandavam HTML ao `BaseConfirmModal`; havia mais 11, em 6 módulos, pela `descricao` do `useConfirmacao` (e duas punham texto digitado sem escapar). A LIC-08 contava com o `codigoBloqueio` do ciclo de envio, mas o `sync.py` o descartava e o `except Exception` do loop engolia o `CloudSyncError`.

## Aprendizado
A tabela "Arquivos afetados" de uma spec é escrita olhando o arquivo que muda, não quem depende dele. Mudança em componente de `shared/`, em formato de prop ou em retorno de função tem consumidores que a spec não lista, e o defeito aparece longe (tags na tela de outro módulo, aviso que nunca chega).

## Como aplicar
Antes de mudar um componente, composable ou função compartilhada, liste os consumidores: `grep -rn "<NomeDoComponente>\|<funcao>(" frontend/src backend-fastapi/app`, e para props de texto procure também o formato do valor (`grep -rn "descricao:.*<strong>"`). Consumidor fora da lista é divergência: pergunte antes de editar.
