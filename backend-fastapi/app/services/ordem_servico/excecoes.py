# ---------------------------------------------------------------------------
# ARQUIVO: services/ordem_servico/excecoes.py
# DESCRICAO: Ordem de servico - excecoes reutilizaveis.
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status


# ===========================================================================
# EXCEÇÕES REUTILIZÁVEIS
# ===========================================================================

os_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Ordem de Serviço não encontrada"
)


cliente_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Cliente não encontrado"
)


funcionario_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Funcionário não encontrado"
)


item_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Item não encontrado nesta OS"
)


forma_pagamento_not_found_exce = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Forma de pagamento não encontrada ou inativa"
)


os_fechada_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Esta operação não é permitida para OS com status FINALIZADA ou CANCELADA"
)


os_nao_pode_reabrir_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Apenas OS com status FINALIZADA ou CANCELADA podem ser reabertas"
)


pagamento_valor_invalido_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A soma dos pagamentos não confere com o valor total da OS"
)


status_invalido_exce = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Use os endpoints /finalizar ou /cancelar para essas transições de status"
)
