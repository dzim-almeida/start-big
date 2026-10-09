# ---------------------------------------------------------------------------
# ARQUIVO: app/services/ordem_servico_ganchos.py
# DESCRICAO: Pontos onde outros modulos reagem ao ciclo de vida da OS, sem o
#            servico da OS conhece-los (Spec 09A da marcenaria, secao 6.1).
# ---------------------------------------------------------------------------
"""
Hoje so a marcenaria se registra aqui (conta a pagar do RT do arquiteto), mas
o servico da OS nao sabe disso: ele so "dispara" as listas nos tres momentos.

- Cada gancho roda DENTRO da transacao da OS: se ele falhar, a finalizacao (ou
  a reabertura, ou o cancelamento) inteira e desfeita.
- Lista vazia = comportamento de sempre. E o caso de toda loja que nao tem um
  modulo que se registre.

Assinatura de um gancho: (db, os, usuario_token, contexto). `contexto` leva o
que so o chamador sabe; hoje, no cancelamento, {"status_anterior": "FINALIZADA"}.
"""

from typing import Any, Callable, Optional

# (db, os, usuario_token, contexto) -> nada. Tipos genericos de proposito: este
# modulo nao importa nada da OS (nem de quem se registra).
GanchoOS = Callable[[Any, Any, Optional[dict], dict], None]

ao_finalizar: list[GanchoOS] = []      # depois de a OS virar FINALIZADA
ao_reabrir: list[GanchoOS] = []        # depois de a OS sair de FINALIZADA
ao_cancelar: list[GanchoOS] = []       # depois de a OS virar CANCELADA (contexto["status_anterior"])


def registrar(lista: list[GanchoOS], gancho: GanchoOS) -> None:
    """Acrescenta o gancho uma vez so (importar o modulo de novo nao duplica)."""
    if gancho not in lista:
        lista.append(gancho)


def disparar(ganchos: list[GanchoOS], db, os_, usuario_token: Optional[dict], contexto: Optional[dict] = None) -> None:
    """Chama cada gancho na ordem em que foi registrado; `contexto` vazio por padrao."""
    for gancho in ganchos:
        gancho(db, os_, usuario_token, contexto or {})
