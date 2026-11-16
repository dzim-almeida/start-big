# ---------------------------------------------------------------------------
# ARQUIVO: app/services/marcenaria/erros.py
# DESCRICAO: Os erros do orcamento de marcenaria, num lugar so (Spec 06A, §6.9).
# ---------------------------------------------------------------------------
"""
Dois formatos, como a §6.9 pede:

- `409` e o `422` do motor respondem `detail` como OBJETO
  `{"codigo": ..., "mensagem": ..., "campo"?: ...}`. A tela decide pelo
  `codigo` (recarregar? mostrar a faixa?) e poe o erro do motor embaixo do
  `campo` certo. O `getErrorMessage` do frontend ja entende esse formato
  (o fiscal usa).
- Os outros `422` (envio incompleto, limites, anexos) e o `404` seguem o
  formato de sempre: `detail` e a frase.
"""

from typing import NoReturn, Optional

from fastapi import HTTPException, status

# Codigos dos 409 e do 422 do motor (a tela compara com estes textos).
REVISAO_DESATUALIZADA = "REVISAO_DESATUALIZADA"
STATUS_NAO_EDITAVEL = "STATUS_NAO_EDITAVEL"
TRANSICAO_INVALIDA = "TRANSICAO_INVALIDA"
EXCLUSAO_NAO_PERMITIDA = "EXCLUSAO_NAO_PERMITIDA"
CALCULO_INVALIDO = "CALCULO_INVALIDO"

# 422 escrito como numero: o nome da constante mudou entre versoes do
# Starlette (UNPROCESSABLE_ENTITY -> UNPROCESSABLE_CONTENT) e o antigo avisa
# "deprecated" a cada uso.
HTTP_422 = 422

MSG_NAO_ENCONTRADO = "Orçamento não encontrado."
MSG_REVISAO = "Este orçamento foi alterado em outro computador. Recarregue para ver a versão atual."
MSG_NAO_EDITAVEL = "Só é possível editar orçamentos em rascunho."
MSG_EXCLUSAO = "Só é possível excluir um orçamento em rascunho que nunca foi enviado."

# Como cada status entra na frase "Ação não permitida para um orçamento ___."
STATUS_NA_FRASE = {
    "RASCUNHO": "em rascunho",
    "ENVIADO": "enviado",
    "APROVADO": "aprovado",
    "RECUSADO": "recusado",
    "VENCIDO": "vencido",
    "SUBSTITUIDO": "substituído",
}


def nao_encontrado(mensagem: str = MSG_NAO_ENCONTRADO) -> NoReturn:
    """404 com a frase (tambem para o segmento sem a capacidade, D26)."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=mensagem)


def conflito(codigo: str, mensagem: str) -> NoReturn:
    """409 com `detail` = {codigo, mensagem}."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"codigo": codigo, "mensagem": mensagem},
    )


def transicao_invalida(status_atual: str) -> NoReturn:
    """409 TRANSICAO_INVALIDA com o status atual na frase."""
    conflito(
        TRANSICAO_INVALIDA,
        f"Ação não permitida para um orçamento {STATUS_NA_FRASE.get(status_atual, status_atual.lower())}.",
    )


def invalido(mensagem: str) -> NoReturn:
    """422 no formato de sempre (detail = frase)."""
    raise HTTPException(status_code=HTTP_422, detail=mensagem)


def calculo_invalido(mensagem: str, campo: Optional[str]) -> NoReturn:
    """422 do motor: {codigo: CALCULO_INVALIDO, campo, mensagem} (Revisao 1)."""
    raise HTTPException(
        status_code=HTTP_422,
        detail={"codigo": CALCULO_INVALIDO, "campo": campo, "mensagem": mensagem},
    )


def sem_permissao(chave: str) -> NoReturn:
    """403 com a mesma frase do `check_permission` (D24)."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Permissão negada. Requer: '{chave}'",
    )


def limite_atingido(quantidade: int, itens: str) -> NoReturn:
    """422 dos limites da secao 5.1 ("Limite de 300 móveis atingido.")."""
    invalido(f"Limite de {quantidade} {itens} atingido.")
