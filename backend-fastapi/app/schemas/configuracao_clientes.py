from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel


class ConfiguracaoClientesRead(BaseModel):
    id: int
    empresa_id: int

    exigir_cpf_pf: bool
    exigir_cnpj_pj: bool
    exigir_celular: bool
    exigir_rg_pf: bool
    exigir_ie_pj: bool
    exigir_email: bool
    exigir_endereco: bool

    tipo_pessoa_padrao: Literal["PF", "PJ"]
    exibir_genero: bool
    exibir_data_nascimento: bool

    bloquear_faturamento_inativo: bool
    oferecer_reativacao_rapida: bool

    ativar_limite_credito: bool
    bloquear_venda_limite: bool

    data_atualizacao: datetime

    model_config = {"from_attributes": True}


class ConfiguracaoClientesUpdate(BaseModel):
    exigir_cpf_pf: Optional[bool] = None
    exigir_cnpj_pj: Optional[bool] = None
    exigir_celular: Optional[bool] = None
    exigir_rg_pf: Optional[bool] = None
    exigir_ie_pj: Optional[bool] = None
    exigir_email: Optional[bool] = None
    exigir_endereco: Optional[bool] = None

    tipo_pessoa_padrao: Optional[Literal["PF", "PJ"]] = None
    exibir_genero: Optional[bool] = None
    exibir_data_nascimento: Optional[bool] = None

    bloquear_faturamento_inativo: Optional[bool] = None
    oferecer_reativacao_rapida: Optional[bool] = None

    ativar_limite_credito: Optional[bool] = None
    bloquear_venda_limite: Optional[bool] = None
