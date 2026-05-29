from app.db.session import SessionLocal

# Importa todos os modelos para que o SQLAlchemy resolva os relacionamentos
from app.db.models.usuario import Usuario
from app.db.models.funcionario import Funcionario
from app.db.models.cliente import Cliente, ClientePF, ClientePJ
from app.db.models.endereco import Endereco
from app.db.models.token import TokenBlocklist
from app.db.models.produto import Produto
from app.db.models.estoque import Estoque
from app.db.models.fornecedor import Fornecedor
from app.db.models.servico import Servico
from app.db.models.produto_fotos import ProdutoFoto
from app.db.models.empresa import Empresa
from app.db.models.cargo import Cargo
from app.db.models.ordem_servico import OrdemServico
from app.db.models.ordem_servico_equipamento import OrdemServicoEquipamento
from app.db.models.ordem_servico_item import OrdemServicoItem
from app.db.models.ordem_servico_pagamento import OrdemServicoPagamento
from app.db.models.ordem_servico_foto import OrdemServicoFoto
from app.db.models.forma_pagamento import FormaPagamento
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings
from app.db.models.sessao_caixa import SessaoCaixa
from app.db.models.venda import Venda
from app.db.models.venda_produto import ProdutoVenda
from app.db.models.venda_pagamento import PagamentoVenda
from app.db.models.log_produto import LogProduto
from app.db.models.movimentacao_estoque import MovimentacaoEstoque

formas = [
    "Dinheiro",
    "PIX",
    "Cartão de Crédito",
    "Cartão de Débito",
    "Transferência Bancária",
    "Boleto",
]

if __name__ == "__main__":
    db = SessionLocal()
    try:
        for nome in formas:
            existe = db.query(FormaPagamento).filter(FormaPagamento.nome == nome).first()
            if not existe:
                db.add(FormaPagamento(nome=nome, ativo=True))
                print(f"Adicionado: {nome}")
            else:
                print(f"Já existe: {nome}")
        db.commit()
        print("\nFormas de pagamento cadastradas com sucesso!")
    finally:
        db.close()
