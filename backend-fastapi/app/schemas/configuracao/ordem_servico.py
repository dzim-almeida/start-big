from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

# Apresentação dos comprovantes. Literal em vez de str solta: valor invalido e
# recusado na borda, em vez de virar uma classe CSS que nao existe e sair uma via
# torta na loja.
TamanhoFolha = Literal["A4", "A5"]
DensidadeComprovante = Literal["normal", "compacto"]
TipoItemOS = Literal["SERVICO", "PRODUTO"]


class ConfiguracaoOSBase(BaseModel):
    prazo_entrega_padrao: int = Field(7, ge=1, description="Prazo padrão de entrega em dias")
    garantia_padrao: str = Field("90 dias", max_length=20, description="Prazo de garantia padrão")
    prazo_abandono_dias: int = Field(90, ge=1, description="Dias para considerar equipamento abandonado")
    taxa_diagnostico_padrao: int = Field(0, ge=0, description="Taxa de diagnóstico padrão em centavos (0 = desativada)")

    # Só a FORMA do comprovante — o conteúdo é invariante (protege o cliente).
    comprovante_entrada_folha: TamanhoFolha = Field("A4", description="Papel da via de entrada")
    comprovante_entrada_densidade: DensidadeComprovante = Field("normal", description="Densidade do layout da via de entrada")
    comprovante_entrega_folha: TamanhoFolha = Field("A4", description="Papel da via de entrega")
    comprovante_entrega_densidade: DensidadeComprovante = Field("normal", description="Densidade do layout da via de entrega")

    # Marcenaria-fábrica (D0): só tem efeito no segmento Marcenaria.
    modo_fabrica: bool = Field(False, description="OS nova de Planejados nasce no trilho da fábrica (orçamento por móvel)")
    fabrica_travar_etapas: bool = Field(False, description="Pendência na etapa bloqueia (True) ou só avisa com motivo (False)")

    # Lava-rápido (SPEC-00 O11): vagas por horário na agenda. 0 = sem limite; só avisa.
    vagas_agenda: int = Field(0, ge=0, le=99, description="Veículos atendidos no mesmo horário (0 = sem limite)")
    # Em qual aba o "Adicionar Item" da OS abre (só a ordem; as duas continuam).
    item_os_abre_em: TipoItemOS = Field("SERVICO", description="Aba em que o Adicionar Item da OS abre")


class ConfiguracaoOSRead(ConfiguracaoOSBase):
    id: int
    empresa_id: int
    data_atualizacao: datetime
    model_config = ConfigDict(from_attributes=True)


class ConfiguracaoOSUpdate(BaseModel):
    prazo_entrega_padrao: Optional[int] = Field(None, ge=1)
    garantia_padrao: Optional[str] = Field(None, max_length=20)
    prazo_abandono_dias: Optional[int] = Field(None, ge=1)
    taxa_diagnostico_padrao: Optional[int] = Field(None, ge=0)

    comprovante_entrada_folha: Optional[TamanhoFolha] = None
    comprovante_entrada_densidade: Optional[DensidadeComprovante] = None
    comprovante_entrega_folha: Optional[TamanhoFolha] = None
    comprovante_entrega_densidade: Optional[DensidadeComprovante] = None

    modo_fabrica: Optional[bool] = None
    fabrica_travar_etapas: Optional[bool] = None
    vagas_agenda: Optional[int] = Field(None, ge=0, le=99)
    item_os_abre_em: Optional[TipoItemOS] = None

    model_config = ConfigDict(from_attributes=True)
