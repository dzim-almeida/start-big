# ---------------------------------------------------------------------------
# ARQUIVO: services/venda/itens.py
# DESCRICAO: Venda - incluir, editar e remover item.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.schemas.vendas import ProdutoVendaCreate, ProdutoVendaUpdate
from app.services import produto as produto_service
from app.services.produto import embalagem as embalagem_service
from app.services import quantidade_venda
from app.services import regras_preco as regras_preco_service
from app.db.crud import venda as venda_crud
from app.db.crud.configuracao import produtos as config_produtos_crud
from app.db.crud.configuracao import vendas as config_vendas_crud
from app.db.crud.configuracao import seguranca as config_seg_crud
from app.core.enum import VendaStatus, TipoProdutoVenda
from app.core.security import verify_password
from app.helpers.exceptions import BadRequestException, NotFoundException
from app.services.venda.calculo import _recalc_total_sale
from app.services.venda.consultas import get_sale_by_id
from app.services.venda.guarda_fiscal import _assert_sem_documento_fiscal_ativo


def add_item_to_sale(db: Session, sale_id: int, item_data: ProdutoVendaCreate) -> tuple[Venda, ProdutoVenda]:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Venda não pode ser editada")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "adicionar itens")
    
    quantidade = item_data.quantidade
    valor_unitario = item_data.valor_unitario
    desconto = item_data.desconto

    product_data = ProdutoVenda(
        **item_data.model_dump(exclude={"valor_unitario", "embalagem_id"}),
        venda_id=sale_id,
    )

    if item_data.embalagem_id is not None and item_data.tipo_produto != TipoProdutoVenda.CADASTRADO:
        raise BadRequestException(detail="Só produto cadastrado é vendido por embalagem")

    if item_data.produto_id:
        if item_data.tipo_produto == TipoProdutoVenda.AVULSO:
            raise BadRequestException(detail="Um produto avulso não pode estar cadastrado")

        product_in_db = produto_service.get_produto_by_id(db, produto_id=item_data.produto_id)
        empresa_id = sale_in_db.funcionario.empresa_id

        # Preço da linha: o da embalagem (2 FD a R$ 51,00) ou o da unidade.
        # Sem embalagem, é o `valor_varejo` de sempre (plano de embalagens, D6).
        valor_unitario = embalagem_service.aplicar_embalagem_na_linha(
            db, product_data, product_in_db, item_data.embalagem_id, empresa_id
        )

        # 3,5 só em KG/G/L/ML/M/M2/M3, nunca em embalagem (venda fracionada D1/D5).
        quantidade_venda.exigir_quantidade_permitida(quantidade, product_in_db, product_data.fator_embalagem)

        # O estoque é em unidade: compara `quantidade × fator` (G2).
        estoque_disponivel = product_in_db.estoque.quantidade
        if product_data.quantidade_base > estoque_disponivel:
            config = config_produtos_crud.get_configuracao_produtos(db, empresa_id=empresa_id)
            permitir = config.permitir_venda_estoque_zerado if config else False
            if not permitir:
                raise BadRequestException(detail=f"Quantidade em estoque insuficiente para o produto {product_in_db.nome}")

    if item_data.tipo_produto == TipoProdutoVenda.AVULSO and item_data.descricao_avulsa is None:
        raise BadRequestException(detail="Um produto avulso deve ter descrição")
    if item_data.tipo_produto == TipoProdutoVenda.AVULSO:
        quantidade_venda.exigir_quantidade_permitida(quantidade, None)

    # Centavos inteiros: 3,5 kg × R$ 10,01 = R$ 35,04 (igual a q × v quando inteira).
    subtotal = quantidade_venda.subtotal_da_linha(quantidade, valor_unitario)

    if desconto > subtotal:
        raise BadRequestException(detail="O desconto não pode ser maior que o total do produto")

    product_data.valor_unitario = valor_unitario
    product_data.subtotal = subtotal

    product_in_db = venda_crud.add_product_to_sale(db, product_data)

    sale_in_db = _recalc_total_sale(db, sale_in_db)

    return sale_in_db, product_in_db


def update_item_in_sale(db: Session, sale_id: int, item_id: int, item_update: ProdutoVendaUpdate) -> tuple[Venda, ProdutoVenda]:

    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Venda não pode ser editada")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "editar itens")
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise NotFoundException(detail="Produto não encontrado")
    
    if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO:
        if item_update.descricao_avulsa:
            raise BadRequestException(detail="Um produto cadastrado não pode ter descrição avulsa")
        if item_update.valor_unitario:
            empresa_id = sale_in_db.funcionario.empresa_id
            config_seg = config_seg_crud.get_configuracao_seguranca(db, empresa_id=empresa_id)
            pin_configurado = bool(config_seg and config_seg.pin_gerente)
            permite_com_pin = config_seg and config_seg.requer_pin_alterar_preco_venda and pin_configurado
            if not permite_com_pin:
                raise BadRequestException(detail="Um produto cadastrado não pode ter valor unitário definido manualmente")
            codigo = item_update.codigo_gerente
            if not codigo:
                raise BadRequestException(detail="REQUER_APROVACAO_GERENTE")
            if not verify_password(codigo, config_seg.pin_gerente):
                raise BadRequestException(detail="PIN_GERENTE_INVALIDO")

    if item_update.desconto and item_in_db.regra_preco in regras_preco_service.calc.REGRAS:
        config_vendas = config_vendas_crud.get_configuracao_vendas(db, empresa_id=sale_in_db.funcionario.empresa_id)
        if config_vendas and config_vendas.bloquear_desconto_com_regra:
            raise BadRequestException(
                detail="Item com regra de preço não aceita desconto manual (Configurações › Regras de Vendas)"
            )

    quantidade = item_update.quantidade or (item_in_db.quantidade or 0)
    if item_update.quantidade is not None:
        quantidade_venda.exigir_quantidade_permitida(
            quantidade,
            item_in_db.produto if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO else None,
            item_in_db.fator_embalagem,
        )

    # Linha de fardo: 3 FD de 12 pedem 36 un do estoque (G2).
    if item_in_db.produto.estoque.quantidade < quantidade * (item_in_db.fator_embalagem or 1):
        empresa_id = sale_in_db.funcionario.empresa_id
        config = config_produtos_crud.get_configuracao_produtos(db, empresa_id=empresa_id)
        permitir = config.permitir_venda_estoque_zerado if config else False
        if not permitir:
            raise BadRequestException(detail=f"Quantidade em estoque insuficiente para o produto {item_in_db.nome}")
    
    preco_unitario = item_update.valor_unitario or (item_in_db.valor_unitario or 0)
    
    desconto = item_in_db.desconto or 0
    if item_update.desconto is not None:
        desconto = item_update.desconto
    
    subtotal = quantidade_venda.subtotal_da_linha(quantidade, preco_unitario)

    if subtotal < desconto:
        raise BadRequestException(detail="O desconto não pode ser maior que o valor total do produto")
        
    item_in_db.descricao_avulsa = item_update.descricao_avulsa or item_in_db.descricao_avulsa
    item_in_db.quantidade = quantidade
    if item_update.valor_unitario and item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO:
        # Preço trocado pelo gerente: a regra de preço sai e não volta nesta
        # linha — o gerente decidiu o preço (§6.1).
        item_in_db.regra_preco = regras_preco_service.MANUAL
        item_in_db.regra_descricao = None
        item_in_db.valor_unitario_tabela = None
        item_in_db.desconto_regra = 0
    item_in_db.valor_unitario = preco_unitario
    # Custo interno só existe no avulso. No cadastrado o custo vem do livro de
    # estoque, e aceitar um valor aqui criaria dois números divergentes para a
    # mesma peça — com o relatório somando os dois.
    if item_update.custo_unitario is not None:
        if item_in_db.tipo_produto == TipoProdutoVenda.CADASTRADO:
            raise BadRequestException(
                detail="Produto cadastrado tem o custo vindo do estoque; não informe custo manual"
            )
        item_in_db.custo_unitario = item_update.custo_unitario
    item_in_db.desconto = desconto
    item_in_db.subtotal = subtotal

    item_in_db = venda_crud.update_product_in_sale(db, item_in_db)
    
    sale_in_db = _recalc_total_sale(db, sale_in_db)

    return sale_in_db, item_in_db


    
def remove_item_from_sale(db: Session, sale_id: int, item_id: int) -> None:
    sale_in_db = get_sale_by_id(db, sale_id=sale_id)
    if sale_in_db.status != VendaStatus.ATIVA:
        raise BadRequestException(detail="Venda não pode ser editada")

    _assert_sem_documento_fiscal_ativo(db, sale_in_db, "remover itens")
    
    item_in_db = venda_crud.get_product_by_id(db, item_id=item_id)
    if not item_in_db or item_in_db.venda_id != sale_id:
        raise NotFoundException(detail="Produto não encontrado")

    venda_crud.remove_product_from_sale(db, item_in_db)
    
    return _recalc_total_sale(db, sale_in_db)
