# ---------------------------------------------------------------------------
# ARQUIVO: services/produto/cadastro.py
# DESCRICAO: Produtos - criar, buscar, editar (com historico), ativar/desativar.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Sequence
from app.schemas.produto import ProdutoCreate, ProdutoSimpleRead, ProdutoUpdate
from app.db.models.produto import Produto as ProdutoModel
from app.db.models.estoque import Estoque as EstoqueModel
from app.db.crud import produto as produto_crud
from app.services.fiscal.cadastro import produto as produto_fiscal_service
from app.core.enum import MovimentacaoTipo, MovimentacaoOrigem
from app.services.produto.embalagem import codigo_de_produto_livre, embalagens_ligadas
from app.services.produto.movimentacao import registrar_movimentacao


# Exceções reutilizáveis
conflict_codigo_produto_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "campo": "codigo_produto",
        "mensagem": "Código de produto já cadastrado no sistema"
    }
)


not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Produto não encontrado no sistema"
)


internal_error_exce = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Erro em cumprir a requisição. Tente novamente mais tarde."
)


_bad_request_exce = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Estoque insuficiente para a quantidade solicitada"
)


# ===========================================================================
# LÓGICA DE CRIAÇÃO (CREATE)
# ===========================================================================

def create_produto(db: Session, produto_to_add: ProdutoCreate, usuario_token: dict) -> ProdutoModel:
    """
    Orquestra a criação de um novo produto.

    1. Verifica unicidade do código.
    2. Separa dados de Produto, Estoque e Fiscal.
    3. Cria instâncias ORM e vincula.
    4. Persiste.
    5. Grava os dados fiscais, quando vierem, na MESMA transação.

    O passo 5 existe para o produto poder ser cadastrado e ter nota emitida
    sem passar pela edição: antes, o bloco fiscal só era aceito no update, e
    o lojista precisava salvar, reabrir e preencher de novo.
    """
    # Verifica duplicidade
    produto_in_db = produto_crud.get_produto_by_code(db, produto_to_add.codigo_produto)
    
    if produto_in_db and produto_in_db.ativo:
        raise conflict_codigo_produto_exce

    # O código do produto não pode ser o de uma embalagem (fardo/caixa) de
    # outro produto: o leitor do caixa não saberia qual dos dois lançar.
    for codigo in (produto_to_add.codigo_barras, produto_to_add.codigo_produto):
        codigo_de_produto_livre(db, codigo)

    # Prepara dados (separa estoque e fiscal do produto principal)
    produto_data = produto_to_add.model_dump(exclude={"estoque", "fiscal"})
    produto_to_db = ProdutoModel(**produto_data)

    estoque_data = produto_to_add.estoque.model_dump()
    quantidade_inicial = estoque_data.get("quantidade", 0) or 0

    # Nasce zerado: a quantidade inicial entra pelo livro, logo abaixo. Se ela
    # já viesse gravada aqui, a ENTRADA somaria em cima e o produto começaria
    # com o dobro do estoque.
    estoque_data["quantidade"] = 0
    # A média ponderada começa no custo informado no cadastro — é a única compra
    # conhecida deste produto até aqui.
    estoque_data["custo_medio"] = estoque_data.get("valor_entrada")
    estoque_for_produto = EstoqueModel(**estoque_data)

    # Vincula estoque ao produto (Relacionamento 1:1)
    produto_to_db.estoque = estoque_for_produto

    produto_in_db = produto_crud.create_produto(db, produto_to_add=produto_to_db)

    # Estoque inicial entra como qualquer outra compra: pelo registro central,
    # com o custo informado, para o livro nascer contando a verdade (0 → N).
    registrar_movimentacao(
        db,
        produto=produto_in_db,
        tipo=MovimentacaoTipo.ENTRADA,
        quantidade=quantidade_inicial,
        origem=MovimentacaoOrigem.CADASTRO,
        usuario_id=int(usuario_token["sub"]) if usuario_token.get("sub") else None,
        usuario_nome=usuario_token.get("nome", "Sistema"),
        observacao="Estoque inicial",
        custo_unitario=estoque_data.get("valor_entrada"),
    )

    # Dados fiscais, quando vierem. `flush` e não `commit`: quem fecha a
    # transação é o `_handle_db_transaction` do endpoint, então um NCM inválido
    # derruba o produto junto — que é o ponto de gravar os dois de uma vez.
    dados_fiscais = getattr(produto_to_add, "fiscal", None)
    if dados_fiscais is not None:
        # Mesma porta do PUT /{id}/fiscal: perfil tributário tem que ser desta
        # empresa (422 orientador, e não IntegrityError da FK).
        produto_fiscal_service.upsert_dados_fiscais(
            db, produto_in_db.id, usuario_token["empresa_id"], dados_fiscais,
        )

    return produto_in_db


# ===========================================================================
# LÓGICA DE LEITURA (READ)
# ===========================================================================

def get_produto_by_search(
    db: Session,
    produto_search: str | None,
    limite: int | None = None,
) -> Sequence[ProdutoModel]:
    """Intermediário para busca de produtos via CRUD."""
    return produto_crud.get_produto_by_search(db, search=produto_search, limite=limite)


def get_produto_simple_by_search(
    db: Session,
    search: str | None,
    limite: int | None = None,
    empresa_id: int | None = None,
) -> Sequence[ProdutoSimpleRead]:
    """Intermediário para busca rápida de produtos (o auto-complete do PDV).

    Com `usar_embalagens` ligado, o código do fardo também acha o produto e
    cada produto leva as embalagens vendáveis com o preço resolvido. Desligado,
    a busca é exatamente a de antes.
    """
    from app.core.embalagem import preco_da_embalagem

    com_embalagens = embalagens_ligadas(db, empresa_id)
    produtos = produto_crud.get_produto_simple_by_search(
        db, search=search, limite=limite, com_embalagens=com_embalagens
    )
    # Marcenaria: o produto acabado do movel so sai na nota da OS, nunca no
    # balcao (docs/marcenaria-faturamento-plano.md, D10). Fora dela, vazio.
    from app.services.marcenaria.faturamento import ids_produtos_acabados

    escondidos = ids_produtos_acabados(db, empresa_id)
    if escondidos:
        produtos = [p for p in produtos if p.id not in escondidos]
    if com_embalagens:
        for produto in produtos:
            preco_unidade = produto.estoque.valor_varejo if produto.estoque else 0
            # Atributo de passagem (não é coluna): o schema lê `embalagens_pdv`.
            produto.embalagens_pdv = [
                {
                    "id": e.id,
                    "sigla": e.sigla,
                    "descricao": e.descricao,
                    "fator": e.fator,
                    "codigo_barras": e.codigo_barras,
                    "preco": preco_da_embalagem(e.fator, e.preco, e.desconto_bp, preco_unidade),
                }
                for e in produto.embalagens
                if e.ativo and e.vende_no_pdv
            ]
    return produtos


# ===========================================================================
# LÓGICA DE ATUALIZAÇÃO (UPDATE)
# ===========================================================================

_CAMPO_LEGIVEL: dict[str, str] = {
    "nome": "Nome",
    "codigo_produto": "Código SKU",
    "codigo_barras": "Código de Barras",
    "unidade_medida": "Unidade de Medida",
    "categoria": "Categoria",
    "marca": "Marca",
    "fornecedor_id": "Fornecedor",
    "localizacao_estoque": "Localização",
    "observacao": "Descrição",
    "valor_varejo": "Preço Varejo",
    "valor_entrada": "Preço Custo",
    "valor_atacado": "Preço Atacado",
    "quantidade": "Quantidade",
    "quantidade_minima": "Qtd. Mínima",
    "quantidade_ideal": "Qtd. Ideal",
    # Marcenaria (Spec 04A): o histórico diz "Sofre perda alterado".
    "sofre_perda": "Sofre perda",
}


def _build_observacao_edicao(campos: list[str]) -> str:
    nomes = [_CAMPO_LEGIVEL.get(c, c) for c in campos]
    if len(nomes) == 1:
        return f"{nomes[0]} alterado"
    return f"Campos alterados: {', '.join(nomes)}"


def _registrar_edicao(db, produto, usuario_token: dict, observacao: str) -> None:
    registrar_movimentacao(
        db,
        produto=produto,
        tipo=MovimentacaoTipo.EDICAO_DADOS,
        quantidade=0,
        origem=MovimentacaoOrigem.CADASTRO,
        usuario_id=int(usuario_token["sub"]) if usuario_token.get("sub") else None,
        usuario_nome=usuario_token.get("nome", "Sistema"),
        observacao=observacao,
    )


def update_produto_by_id(db: Session, produto_id: int, produto_to_update: ProdutoUpdate, usuario_token: dict) -> ProdutoModel:
    """
    Atualiza produto e dados de estoque aninhados.
    """
    produto_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)

    if not produto_in_db:
        raise not_found_exce

    data_to_update = produto_to_update.model_dump(exclude_unset=True)
    for campo in ("codigo_barras", "codigo_produto"):
        if data_to_update.get(campo) and data_to_update[campo] != getattr(produto_in_db, campo):
            codigo_de_produto_livre(db, data_to_update[campo], produto_id)
    campos_alterados: list[str] = []
    # Quantidade não é um campo editável como os outros: ela precisa passar pelo
    # livro de estoque. Fica de fora do setattr e é aplicada depois, como AJUSTE.
    nova_quantidade: int | None = None

    # Tratamento para atualização de Estoque (Tabela Filha)
    if "estoque" in data_to_update:
        storage_data_to_update = produto_to_update.estoque.model_dump(exclude_unset=True)

        if "quantidade" in storage_data_to_update:
            nova_quantidade = storage_data_to_update.pop("quantidade")

        for key, value in storage_data_to_update.items():
            if getattr(produto_in_db.estoque, key, None) != value:
                campos_alterados.append(key)
            setattr(produto_in_db.estoque, key, value)

        del data_to_update["estoque"]

    # Atualiza atributos do Produto (Tabela Pai)
    for key, value in data_to_update.items():
        if getattr(produto_in_db, key, None) != value:
            campos_alterados.append(key)
        setattr(produto_in_db, key, value)

    produto_result = produto_crud.update_produto(db, produto_in_db)

    if campos_alterados:
        _registrar_edicao(db, produto_result, usuario_token, _build_observacao_edicao(campos_alterados))

    # Mudança de quantidade pela tela de cadastro é uma CONTAGEM, e vai para o
    # livro como AJUSTE. Antes ela era gravada direto no estoque e o histórico
    # só registrava "Quantidade alterado", com anterior e posterior iguais: as
    # unidades sumiam sem deixar rastro de quantas eram nem de quando foi.
    if nova_quantidade is not None and nova_quantidade != (produto_result.estoque.quantidade or 0):
        registrar_movimentacao(
            db,
            produto=produto_result,
            tipo=MovimentacaoTipo.AJUSTE,
            quantidade=nova_quantidade,
            origem=MovimentacaoOrigem.CADASTRO,
            usuario_id=int(usuario_token["sub"]) if usuario_token.get("sub") else None,
            usuario_nome=usuario_token.get("nome", "Sistema"),
            observacao="Quantidade corrigida no cadastro",
        )

    return produto_result


# ===========================================================================
# LÓGICA DE STATUS (TOGGLE)
# ===========================================================================

def toggle_active_disable_produto_by_id(db: Session, produto_id: int, new_produto_code: str | None, usuario_token: dict) -> ProdutoModel:
    """
    Alterna status Ativo/Inativo.
    Se estiver reativando, verifica conflito de código e permite atualização.
    """
    produto_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)
    
    if not produto_in_db:
        raise not_found_exce
    
    # Lógica de Reativação (Inativo -> Ativo)
    if not produto_in_db.ativo:
        
        # Define qual código validar (o novo sugerido ou o atual existente)
        codigo_to_verify = new_produto_code if new_produto_code else produto_in_db.codigo_produto
        
        # Busca conflitos
        produto_with_same_code_in_db = produto_crud.get_produto_by_code(db, produto_code=codigo_to_verify)

        # Se existe conflito e não é o mesmo produto
        if produto_with_same_code_in_db and produto_with_same_code_in_db.id != produto_in_db.id:
            conflict_codigo_produto_exce.detail["mensagem"] = f"Código '{codigo_to_verify}' já cadastrado. Envie um novo código."
            raise conflict_codigo_produto_exce
        
        # Se forneceu código novo e passou na validação, atualiza
        if new_produto_code:
            produto_in_db.codigo_produto = new_produto_code
                
    # Inverte o status
    produto_in_db.ativo = not produto_in_db.ativo

    produto_result = produto_crud.update_produto(db, produto_to_update=produto_in_db)

    observacao = "Produto reativado" if produto_result.ativo else "Produto desabilitado"
    _registrar_edicao(db, produto_result, usuario_token, observacao)

    return produto_result


def get_produto_by_id(db: Session, produto_id: int) -> ProdutoModel:
    product_in_db = produto_crud.get_produto_by_id(db, produto_id=produto_id)
    if not product_in_db:
        raise not_found_exce
    return product_in_db
