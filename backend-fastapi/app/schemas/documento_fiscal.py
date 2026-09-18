# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/documento_fiscal.py
# DESCRIÇÃO: Schemas Pydantic para o Centro Fiscal (documentos e pendências).
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DocumentoItemResumo(BaseModel):
    """Resumo de item da nota/venda para conferência fiscal."""

    id: Optional[int] = None
    produto_id: Optional[int] = None
    nome: str
    codigo_barras: Optional[str] = None
    quantidade: int
    valor_unitario: int
    subtotal: int
    desconto: int = 0
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    # Devolução (TASK003): saldo por item em MILÉSIMOS (1000 = 1 UN), porque a
    # quantidade inteira acima perde a fração e a devolução parcial precisa
    # dela. Só o snapshot preenche; itens reconstruídos do cadastro ficam None.
    quantidade_milesimos: Optional[int] = None
    quantidade_devolvida_acumulada: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentoFiscalRead(BaseModel):
    """Documento fiscal emitido — leitura."""

    id: int
    tipo_documento: str
    origem_tipo: str
    origem_id: Optional[int] = None
    origem_numero_os: Optional[str] = None
    status: str
    chave_acesso: Optional[str] = None
    numero_documento: Optional[int] = None
    serie: Optional[int] = None
    protocolo_autorizacao: Optional[str] = None
    data_autorizacao: Optional[datetime] = None
    url_pdf: Optional[str] = None
    url_xml: Optional[str] = None
    # O XML está guardado NESTE computador?
    #
    # Booleano e não o caminho: a tela só precisa saber se pode prometer
    # "funciona sem internet". Caminho absoluto do servidor na resposta seria
    # ruído — e informação de infraestrutura que a interface não usa.
    xml_local: bool = False
    pdf_local: bool = False
    # Cartas de correção AUTORIZADAS (só NF-e). O texto da última vem junto
    # para o drawer pré-preencher a próxima carta sem uma segunda requisição:
    # a SEFAZ só considera vigente a última, então ela precisa consolidar.
    total_cartas_correcao: int = 0
    ultima_carta_correcao: Optional[str] = None
    # Devolução: 1 = normal, 4 = esta nota É uma devolução (aponta para a
    # origem). `totalmente_devolvida` é derivado do saldo dos itens.
    finalidade_emissao: int = 1
    documento_referenciado_id: Optional[int] = None
    chave_documento_referenciado: Optional[str] = None
    totalmente_devolvida: bool = False
    mensagem_sefaz: Optional[str] = None
    codigo_status_sefaz: Optional[int] = None
    motivo_rejeicao: Optional[str] = None
    # Status cru da emissora, ao lado do normalizado. A tela usa para
    # separar denegada de rejeitada e para o suporte ver o termo original.
    status_focus: Optional[str] = None
    valor_total: Optional[int] = None
    # --- NFC-e: o que o DANFE térmico precisa imprimir ---
    # Vêm aqui (e não só na nota da venda) porque a REIMPRESSÃO parte do
    # documento fiscal — sem eles seria preciso consultar o provedor de novo.
    qrcode: Optional[str] = None
    url_consulta: Optional[str] = None
    valor_tributos: Optional[int] = None
    ref_api: Optional[str] = None
    ambiente_emissao: Optional[int] = None
    tentativa_anterior_id: Optional[int] = None
    data_emissao: Optional[datetime] = None
    data_criacao: datetime
    data_atualizacao: datetime
    
    # Metadados enriquecidos para o Drawer & Gestão Fiscal
    venda_id: Optional[int] = None
    destinatario_id: Optional[int] = None
    destinatario_nome: Optional[str] = None
    destinatario_documento: Optional[str] = None
    destinatario_uf: Optional[str] = None
    destinatario_municipio: Optional[str] = None
    itens_resumo: Optional[List[DocumentoItemResumo]] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentoFiscalListRead(BaseModel):
    """Lista paginada de documentos fiscais."""

    items: list[DocumentoFiscalRead]
    total: int
    pagina: int
    paginas: int


class DocumentoFiscalResumo(BaseModel):
    """Contadores operacionais por status."""

    pendentes: int = 0
    autorizadas: int = 0
    rejeitadas: int = 0
    canceladas: int = 0


class PendenciaGlobalItem(BaseModel):
    """Item individual de pendência cadastral."""

    id: int
    nome: str
    campo_faltante: str


class PendenciasGlobais(BaseModel):
    """Pendências globais para o painel do Centro Fiscal."""

    emitente_completo: bool
    emitente_pendencias: list[str]
    # Cadastro errado que NÃO impede emitir. Pendência recusa a nota; aviso
    # só conta. Ver `_avisos_do_emitente`.
    emitente_avisos: list[str] = []
    # Aviso (nao pendencia): o certificado vence em ate 30 dias, ou ja venceu.
    # Vencido tambem entra em `emitente_pendencias`, porque ai barra o gate.
    certificado_aviso: Optional[str] = None
    certificado_dias_restantes: Optional[int] = None
    produtos_sem_ncm: list[PendenciaGlobalItem]
    servicos_sem_lc116: list[PendenciaGlobalItem]
    pagamentos_sem_sefaz: list[PendenciaGlobalItem]


class DocumentoFiscalHistorico(BaseModel):
    """Histórico de tentativas de emissão (linked list)."""

    tentativas: list[DocumentoFiscalRead]
    total_tentativas: int
