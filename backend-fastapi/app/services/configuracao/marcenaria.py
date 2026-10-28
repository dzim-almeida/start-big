# ---------------------------------------------------------------------------
# ARQUIVO: services/configuracao/marcenaria.py (era services/configuracao_marcenaria.py ate 13/10/2026)
# DESCRICAO: Parametros padrao do orcamento de marcenaria (Spec 04A).
#
#            So existe para segmento que declara a capacidade
#            `orcamento_tecnico` (hoje, a marcenaria). A regra le a CAPACIDADE
#            no registry, nunca o nome do segmento (D1).
# ---------------------------------------------------------------------------

from enum import Enum

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import segmentos as reg
from app.db.crud.configuracao.marcenaria import (
    create_configuracao_marcenaria,
    get_configuracao_marcenaria,
    update_configuracao_marcenaria,
)
from app.db.models.configuracao_marcenaria import ConfiguracaoMarcenaria
from app.schemas.configuracao.marcenaria import ConfiguracaoMarcenariaUpdate
from app.services.sistema.segmentos import get_segmento_atual


def _exigir_orcamento_tecnico(db: Session) -> None:
    """404 fora de segmento com orcamento tecnico (D1): para os outros, a rota nao existe."""
    if not reg.segmento_tem_capacidade(get_segmento_atual(db), reg.CAP_ORCAMENTO_TECNICO):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parâmetros de marcenaria não disponíveis para este segmento.",
        )


def obter_configuracao(db: Session, empresa_id: int) -> ConfiguracaoMarcenaria:
    """A configuracao da empresa; criada com os padroes na primeira chamada.

    E tambem o ponto que o orcamento (Spec 06A) usa para COPIAR os padroes.
    """
    _exigir_orcamento_tecnico(db)
    config = get_configuracao_marcenaria(db, empresa_id)       # ja existe?
    if config is None:
        config = create_configuracao_marcenaria(db, empresa_id)  # get-or-create
    return config


def atualizar_configuracao(
    db: Session,
    empresa_id: int,
    dados: ConfiguracaoMarcenariaUpdate,
) -> ConfiguracaoMarcenaria:
    """PUT parcial: so os campos enviados mudam."""
    config = obter_configuracao(db, empresa_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():   # so o que veio
        # O enum do RT vira o texto gravado no banco ("MARGEM"/"PRECO").
        setattr(config, campo, valor.value if isinstance(valor, Enum) else valor)
    _conferir_faturamento(db, config)
    return update_configuracao_marcenaria(db, config)


# ===========================================================================
# FATURAMENTO DOS MOVEIS (docs/marcenaria-faturamento-plano.md, F1)
# ===========================================================================

def _produto_ativo(db: Session, produto_id: int | None, rotulo: str):
    """O produto acabado, ou 422 se nao existe ou foi desativado."""
    from app.db.models.produto import Produto

    if produto_id is None:
        return None
    produto = db.get(Produto, produto_id)
    if produto is None or not produto.ativo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{rotulo}: produto não encontrado ou desativado.",
        )
    return produto


def _conferir_faturamento(db: Session, config: ConfiguracaoMarcenaria) -> None:
    """Ligar o faturamento exige o produto acabado de producao propria.

    O cadastro fiscal do produto NAO e exigido aqui: o contador pode preenche-lo
    depois. Quem barra nota sem NCM e a emissao; aqui a tela so recebe o aviso
    (`pendencias_faturamento`).
    """
    _produto_ativo(db, config.produto_acabado_padrao_id, "Produto do móvel fabricado")
    _produto_ativo(db, config.produto_acabado_revenda_id, "Produto do móvel comprado pronto")
    if config.faturamento_modo != "DESLIGADO" and config.produto_acabado_padrao_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Para faturar os móveis, escolha o produto do móvel fabricado.",
        )
    if config.instalacao_modo == "NFSE":
        from app.db.models.servico import Servico

        servico = db.get(Servico, config.servico_instalacao_id) if config.servico_instalacao_id else None
        if servico is None or not getattr(servico, "ativo", True):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Para emitir a NFS-e da instalação, escolha o serviço da instalação.",
            )


def pendencias_faturamento(db: Session, config: ConfiguracaoMarcenaria, empresa_id: int) -> list[str]:
    """O que falta no cadastro fiscal dos produtos acabados, em texto para a tela.

    Desligado, nao ha o que avisar. Usa a MESMA conferencia do gate da emissao
    (`verificar_produto_fiscal`), entao o aviso e a recusa nunca divergem.
    """
    if config.faturamento_modo == "DESLIGADO":
        return []
    from app.db.models.empresa import Empresa
    from app.db.models.produto import Produto
    from app.services.fiscal.completude.validators import verificar_produto_fiscal
    from app.services.fiscal.helpers import obter_crt, usa_csosn

    empresa = db.get(Empresa, empresa_id)
    simples = usa_csosn(obter_crt(empresa)) if empresa is not None else False
    avisos: list[str] = []
    for produto_id in (config.produto_acabado_padrao_id, config.produto_acabado_revenda_id):
        produto = db.get(Produto, produto_id) if produto_id else None
        if produto is None:
            continue
        pendencias: list = []
        verificar_produto_fiscal(db, produto, pendencias, simples)
        avisos.extend(f"{produto.nome}: {p.mensagem}" for p in pendencias)
    if config.instalacao_modo == "NFSE" and config.servico_instalacao_id:
        from app.db.crud import fiscal as fiscal_crud

        fiscal = fiscal_crud.get_servico_fiscal(db, config.servico_instalacao_id)
        if not fiscal or not fiscal.codigo_tributacao_nacional or not fiscal.codigo_nbs:
            avisos.append("Serviço da instalação: falta o código de tributação nacional ou o NBS (cadastro do serviço).")
    return avisos


# Os produtos acabados que o sistema cria quando a loja pede (D2). O codigo e
# fixo: pedir de novo reaproveita o que ja existe em vez de duplicar.
# O CFOP ja vem sugerido (5101 = producao do estabelecimento; 5102 = revenda,
# o movel comprado pronto da central, D4); NCM e CST/CSOSN ficam para o contador.
PRODUTOS_ACABADOS_SUGERIDOS = (
    ("produto_acabado_padrao_id", "MOVEL-PLANEJADO", "Móvel planejado", "5101"),
    ("produto_acabado_revenda_id", "MOVEL-PLANEJADO-REV", "Móvel planejado (revenda)", "5102"),
)


def criar_produtos_acabados(db: Session, empresa_id: int, usuario_token: dict) -> ConfiguracaoMarcenaria:
    """Cria (ou reaproveita) os dois produtos acabados e os liga a configuracao.

    Nascem sem preco, sem estoque e com o fiscal em branco: o NCM e o CST sao do
    contador. Os vinculos que a loja ja escolheu nao sao trocados.
    """
    from app.db.crud.produto.consultas import get_produto_by_code
    from app.schemas.fiscal.produto import ProdutoFiscalUpdate
    from app.schemas.produto.cadastro import ProdutoCreateComFiscal
    from app.schemas.produto.estoque import EstoqueCreate
    from app.services.produto.cadastro import create_produto

    config = obter_configuracao(db, empresa_id)
    for campo, codigo, nome, cfop in PRODUTOS_ACABADOS_SUGERIDOS:
        if getattr(config, campo) is not None:
            continue
        produto = get_produto_by_code(db, codigo)
        if produto is None:
            produto = create_produto(
                db,
                ProdutoCreateComFiscal(
                    nome=nome,
                    codigo_produto=codigo,
                    unidade_medida="UN",
                    categoria="Móveis planejados",
                    observacao="Produto acabado da marcenaria: é o que sai na NF-e do móvel.",
                    estoque=EstoqueCreate(valor_varejo=0, quantidade=0),
                    fiscal=ProdutoFiscalUpdate(cfop_padrao=cfop, origem_mercadoria=0, unidade_tributavel="UN"),
                ),
                usuario_token,
            )
        setattr(config, campo, produto.id)
    return update_configuracao_marcenaria(db, config)
