# ---------------------------------------------------------------------------
# ARQUIVO: schemas/ordem_servico/objeto.py
# DESCRICAO: Schemas da OS - objeto/equipamento e identificador.
# ---------------------------------------------------------------------------

from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from app.core.enum import (
    TipoEquipamento,
)


# ===========================================================================
# VERIFICAÇÃO DE IDENTIFICADOR (placa / nº de série já cadastrado)
# ===========================================================================

class OSIdentificadorConflito(BaseModel):
    """Objeto já cadastrado que usa o mesmo identificador, e de quem ele é."""
    objeto_id: int = Field(..., description="ID do objeto já cadastrado")
    cliente_id: int = Field(..., description="ID do cliente dono do objeto")
    cliente_nome: Optional[str] = Field(None, description="Nome de exibição do dono")
    marca: Optional[str] = Field(None, description="Marca registrada no objeto")
    modelo: Optional[str] = Field(None, description="Modelo registrado no objeto")
    numero_serie: Optional[str] = Field(None, description="Identificador como foi gravado")
    ultima_os_numero: Optional[str] = Field(None, description="Número da OS mais recente do objeto")
    ultima_os_data: Optional[datetime] = Field(None, description="Data da OS mais recente do objeto")

    model_config = ConfigDict(from_attributes=True)


class OSIdentificadorCheck(BaseModel):
    """
    Resposta da verificação de duplicidade do identificador.

    `pesquisavel=False` significa que o texto digitado não identifica um bem
    ("S/N", "não sei") — não é erro, só não há o que procurar. `conflitos` vazio
    significa que pode seguir sem aviso.
    """
    identificador: str = Field(..., description="Identificador consultado")
    pesquisavel: bool = Field(..., description="Se o texto vale como identificador de um bem")
    conflitos: List[OSIdentificadorConflito] = Field(
        default_factory=list,
        description="Objetos de OUTROS clientes com o mesmo identificador"
    )

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# BUSCA DE OBJETO POR IDENTIFICADOR (seletor de cliente da OS)
# ===========================================================================

class OSObjetoBuscaItem(BaseModel):
    """
    Objeto encontrado pela placa / nº de série / código da arte, com o dono
    junto — é a linha que o seletor de cliente da OS mostra quando o atendente
    digita o identificador em vez do nome.

    Carrega os campos do objeto (não só o id) porque quem clica nesta linha já
    disse qual é o bem: a OS abre com ele preenchido, sem passar pela tela de
    "objeto já cadastrado?".
    """
    objeto_id: int = Field(..., description="ID do objeto encontrado")
    cliente_id: int = Field(..., description="ID do cliente dono do objeto")
    cliente_nome: Optional[str] = Field(None, description="Nome de exibição do dono")
    tipo_equipamento: Optional[str] = Field(None, description="Tipo do objeto (livre por segmento)")
    marca: Optional[str] = Field(None, description="Marca registrada no objeto")
    modelo: Optional[str] = Field(None, description="Modelo registrado no objeto")
    numero_serie: Optional[str] = Field(None, description="Identificador como foi gravado")
    cor: Optional[str] = Field(None, description="Cor registrada no objeto")
    dados_adicionais: Optional[dict] = Field(
        default_factory=dict,
        description="Campos dinâmicos do segmento (chassi, ano, IMEI...)"
    )

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# EQUIPAMENTO DA OS
# ===========================================================================

class OSObjetoCreate(BaseModel):
    """Payload para registrar um objeto de serviço ao abrir uma OS."""
    tipo_equipamento: Optional[TipoEquipamento] = Field(None, description="Tipo do equipamento (opcional - compatibilidade)")
    # marca/modelo tambem sao opcionais aqui pela MESMA razao de numero_serie:
    # no segmento que gera identificador, o formulario pergunta so o nome da
    # arte, e o servico preenche o resto. Continuam exigidos para os demais --
    # ver _exigir_campos_do_objeto em services/ordem_servico.py.
    marca: Optional[str] = Field(None, max_length=100, description="Marca do objeto (ex: Fiat, Samsung)")
    modelo: Optional[str] = Field(None, max_length=100, description="Modelo do objeto (ex: Uno, S20)")
    # Opcional no schema porque ha segmento em que o SISTEMA gera o
    # identificador (serigrafia: "ART-0042"), e o formulario nem pergunta.
    # Para quem NAO gera, a exigencia continua existindo -- ela so mudou de
    # lugar, para o servico, que sabe qual e o segmento. Ver
    # _preencher_identificador_gerado em services/ordem_servico.py.
    numero_serie: Optional[str] = Field(None, max_length=100, description="Número de série ou identificador principal (ex: Placa, Serial). Gerado pelo sistema em segmentos que o declaram.")
    imei: Optional[str] = Field(None, max_length=20, description="IMEI (opcional - compatibilidade)")
    cor: Optional[str] = Field(None, max_length=50, description="Cor do objeto")
    proxima_revisao_data: Optional[date] = Field(None, description="Data agendada da próxima revisão (oficina)")
    proxima_revisao_km: Optional[int] = Field(None, ge=0, description="KM alvo da próxima revisão (oficina)")
    dados_adicionais: Optional[dict] = Field(default_factory=dict, description="Campos dinâmicos adicionais (JSON)")

    model_config = ConfigDict(from_attributes=True)


class OSObjetoRead(OSObjetoCreate):
    """Resposta completa do objeto de serviço de uma OS."""
    id: int = Field(..., description="ID único do objeto")
    cliente_id: int = Field(..., description="ID do cliente proprietário do objeto")
    ativo: bool = Field(..., description="Status ativo do objeto")
    data_criacao: datetime = Field(..., description="Data de cadastro")
    data_atualizacao: datetime = Field(..., description="Data da última atualização")

    # Na resposta, o tipo é livre por segmento (ex: 'COMPUTADOR' para informática,
    # 'Veículo' para oficina). Relaxamos o enum de TI para str e coagimos o valor
    # vindo da property/shim do modelo. A informática segue recebendo os mesmos
    # valores de sempre (ex: 'COMPUTADOR').
    tipo_equipamento: Optional[str] = Field(
        None, description="Tipo do objeto (livre por segmento; ex: COMPUTADOR, Veículo)"
    )

    @field_validator("tipo_equipamento", mode="before")
    @classmethod
    def _coagir_tipo_equipamento(cls, v):
        if v is None:
            return None
        return getattr(v, "value", None) or str(v)


class OSObjetoUpdate(BaseModel):
    """Payload para atualização parcial do objeto de serviço."""
    tipo_equipamento: Optional[TipoEquipamento] = Field(None, description="Novo tipo de equipamento")
    marca: Optional[str] = Field(None, max_length=100, description="Nova marca")
    modelo: Optional[str] = Field(None, max_length=100, description="Novo modelo")
    numero_serie: Optional[str] = Field(None, max_length=100, description="Novo identificador/placa")
    imei: Optional[str] = Field(None, max_length=20, description="Novo IMEI")
    cor: Optional[str] = Field(None, max_length=50, description="Nova cor")
    cliente_id: Optional[int] = Field(None, description="Novo ID do cliente proprietário")
    proxima_revisao_data: Optional[date] = Field(None, description="Nova data da próxima revisão")
    proxima_revisao_km: Optional[int] = Field(None, ge=0, description="Novo KM alvo da próxima revisão")
    dados_adicionais: Optional[dict] = Field(None, description="Novos dados adicionais (JSON)")

    model_config = ConfigDict(from_attributes=True)


# Aliases de compatibilidade
OSEquipamentoCreate = OSObjetoCreate


OSEquipamentoRead = OSObjetoRead


OSEquipamentoUpdate = OSObjetoUpdate
