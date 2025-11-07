from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


from app.schemas.estoque import EstoqueCreate, EstoqueRead, EstoqueUpdate
# Importe a classe de Enumeração para a Unidade de Medida, se existir
# from app.core.enum import UnidadeMedida 

class ProdutoCreate(BaseModel):
    """
    Schema para validar os dados de ENTRADA ao criar um novo Produto.
    Os campos correspondem diretamente ao diagrama de Produto.
    """
    
    # 1. Identificação Principal
    nome: str = Field(
        ..., 
        max_length=255, 
        description="Nome comercial do produto (obrigatório)."
    )

    codigo_produto: str = Field(
        ..., 
        max_length=50, 
        description="Código interno ou SKU do produto."
    )
    
    # 2. Atributos de Controle e Medida
    unidade_medida: Optional[str] = Field(
        None, 
        max_length=10, 
        description="Unidade de medida (Ex: UN, KG, LT)."
    )
    
    observacao: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Observações internas sobre o produto."
    )
    
    # 3. Atributos de Classificação
    nota_fiscal: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Referência de nota fiscal ou NCM."
    )
    
    categoria: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Categoria de classificação do produto."
    )
    
    marca: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Marca do produto."
    )

    # 4. Relacionamento (Chave Estrangeira - FK)
    # Assumimos que o ID do fornecedor é um inteiro.
    id_fornecedor: Optional[int] = Field(
        None, 
        description="ID do fornecedor (Chave Estrangeira)."
    )

    estoque: EstoqueCreate = Field(
        ...,
        description="Dados de estoque associados ao produto (obrigatório na criação)"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            # Exemplo de payload atualizado
            "example": {
                "nome": "Café Gourmet Moído 500g",
                "codigo_produto": "CFG-001",
                "unidade_medida": "UN",
                "observacao": "Armazenar em local seco.",
                "nota_fiscal": "1004.22.99",
                "categoria": "Bebidas",
                "marca": "Fazenda Boa Vista",
                "id_fornecedor": 1,
                # Objeto de estoque aninhado
                "estoque": {
                    "valor_varejo": 2999,
                    "quantidade": 100,
                    "valor_entrada": 1500,
                    "valor_atacado": 2500,
                    "quantidade_minima": 20
                }
            }
        }
    )


class ProdutoRead(ProdutoCreate):
    id: int = Field(
        ...,
        description="ID do produto"
    )

    estoque: EstoqueRead = Field(
        ...,
        description="Dados de estoque associados ao produto"
    )

class ProdutoUpdate(BaseModel):
    """
    Schema para ATUALIZAR um Produto existente.
    Todos os campos, incluindo o estoque, são opcionais.
    """
    
    # 1. Identificação Principal
    nome: Optional[str] = Field(
        None, 
        max_length=255, 
        description="Novo nome comercial do produto."
    )
    codigo_produto: Optional[str] = Field(
        None, 
        max_length=50, 
        description="Novo código interno ou SKU."
    )
    
    # 2. Atributos de Controle e Medida
    unidade_medida: Optional[str] = Field(
        None, 
        max_length=10, 
        description="Nova unidade de medida."
    )
    
    observacao: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Nova observação interna."
    )
    
    # 3. Atributos de Classificação
    nota_fiscal: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Nova referência de nota fiscal ou NCM."
    )
    categoria: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Nova categoria."
    )
    marca: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Nova marca."
    )

    # 4. Relacionamento (Chave Estrangeira - FK)
    id_fornecedor: Optional[int] = Field(
        None, 
        description="Novo ID do fornecedor."
    )

    # 5. DADOS DE ESTOQUE (ANINHADOS E OPCIONAIS)
    # Na atualização, o estoque é opcional e usa o schema EstoqueUpdate
    estoque: Optional[EstoqueUpdate] = Field(
        None,
        description="Novos dados de estoque para atualizar (parcial)."
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            # Exemplo de payload de atualização parcial
            "example": {
                "nome": "Café Super Gourmet Torrado 1kg",
                "observacao": "Revisar preço de atacado.",
                "estoque": {
                    "valor_varejo": 3999,
                    "quantidade_minima": 10
                }
                # Apenas os campos a serem alterados são enviados
            }
        }
    )