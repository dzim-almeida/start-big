# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/fila.py
# DESCRICAO: Venda - enviar ao caixa e devolver para a montagem (modo balcao).
# ---------------------------------------------------------------------------

from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.db.crud import venda as venda_crud
from app.db.crud.configuracao import vendas as config_vendas_crud
from app.core.enum import VendaStatus
from app.helpers.exceptions import BadRequestException
from app.services.venda.consultas import get_sale_by_id


def enviar_ao_caixa(db: Session, sale_id: int) -> Venda:
    """O atendente entrega a venda ao caixa.

    Nao muda o status: a venda continua ATIVA. O que muda e o carimbo que a
    lista usa para separar "pronta, esperando o caixa" de "ainda sendo montada".

    IDEMPOTENTE de proposito. Reenviar mantem o carimbo original -- senao um
    clique repetido mandaria o atendente para o fim da fila sem que ninguem
    tivesse feito nada de errado.
    """
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)

    # A fila e opcional. A tela ja esconde o botao quando a chave esta desligada,
    # mas quem garante que nao entra venda na fila de uma loja que nao usa fila e
    # esta checagem -- o frontend pode estar mais novo que a configuracao, e foi
    # exatamente assim que a chave do PIN pareceu quebrada num teste na loja.
    empresa_id = sale_in_db.funcionario.empresa_id
    config = config_vendas_crud.get_configuracao_vendas(db, empresa_id=empresa_id)
    if not (config and config.usar_fila_do_caixa):
        raise BadRequestException(
            detail="A fila do caixa não está ligada em Configurações > Regras de Vendas"
        )

    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Só uma venda em aberto pode ir para o caixa")

    # Carrinho vazio na fila e ruido: o caixa abre e nao ha o que cobrar.
    if not sale_in_db.itens:
        raise BadRequestException(detail="Adicione ao menos um item antes de enviar ao caixa")

    if sale_in_db.enviada_ao_caixa_em is None:
        sale_in_db.enviada_ao_caixa_em = datetime.utcnow()

    return venda_crud.update_sale(db, sale_in_db)


def devolver_para_montagem(db: Session, sale_id: int) -> Venda:
    """Tira a venda da fila do caixa, sem mexer em mais nada.

    Qualquer operador pode: o atendente que se arrependeu e o caixa que viu
    problema. Como a coluna e so sinal de lista, nao ha nada a desfazer alem
    dela -- nenhum dinheiro foi movido para entrar na fila.

    NAO checa `usar_fila_do_caixa`, ao contrario do enviar. Se o dono desligar a
    chave com vendas ainda na fila, elas precisam poder sair -- recusar aqui as
    deixaria carimbadas para sempre, sem tela nenhuma para desfazer.
    """
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)

    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Só uma venda em aberto pode voltar para montagem")

    sale_in_db.enviada_ao_caixa_em = None
    return venda_crud.update_sale(db, sale_in_db)
