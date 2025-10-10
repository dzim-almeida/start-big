# # Testes para as rotas de produtos
# from app.main import app

# # Payload de dados de teste
# produto_payload = {
#     "nome": "Iphone 17 PRO",
#     "preco": 1699.99,
#     "codigo_barras": "0000000001"
# }

# # Tentar cadastrar um produto
# def test_criar_produto_status_code_201():
#     # Requisição POST ao endpoint com o payload de teste
#     response = client.post("/api/v1/produtos/", json=produto_payload)

#     # Afirmativa: Verifica se o status HTTP é o esperado para criação
#     assert response.status_code == 201