# ---------------------------------------------------------------------------
# ARQUIVO: app/schemas/emissao_fiscal.py
# DESCRIÇÃO: Schemas Pydantic para emissão de NF-e (request/response).
# ---------------------------------------------------------------------------

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EmissaoNFeRequest(BaseModel):
    """Request para emitir NF-e a partir de uma venda ou OS."""

    venda_id: Optional[int] = None
    numero_os: Optional[str] = None

    @model_validator(mode="after")
    def validar_origem(self):
        if not self.venda_id and not self.numero_os:
            raise ValueError("Informe venda_id ou numero_os.")
        if self.venda_id and self.numero_os:
            raise ValueError("Informe apenas venda_id OU numero_os, não ambos.")
        return self


class CancelamentoRequest(BaseModel):
    """Request para cancelar documento fiscal autorizado."""

    justificativa: str

    @field_validator("justificativa")
    @classmethod
    def validar_justificativa(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 15:
            raise ValueError("Justificativa deve ter no mínimo 15 caracteres (exigência SEFAZ).")
        if len(v) > 255:
            raise ValueError("Justificativa deve ter no máximo 255 caracteres.")
        return v


class CartaCorrecaoRequest(BaseModel):
    """Request para registrar uma CC-e numa NF-e autorizada.

    Não reaproveita `CancelamentoRequest`: o limite é OUTRO (1000, não 255) —
    a carta precisa caber a consolidação de todas as anteriores, porque a
    SEFAZ só considera vigente a última.
    """

    correcao: str

    @field_validator("correcao")
    @classmethod
    def validar_correcao(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 15:
            raise ValueError("A correção deve ter no mínimo 15 caracteres (exigência SEFAZ).")
        if len(v) > 1000:
            raise ValueError("A correção deve ter no máximo 1000 caracteres.")
        return v


class CartaCorrecaoRead(BaseModel):
    """Uma CC-e registrada (ou tentada) numa NF-e."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int
    sequencia: Optional[int] = None
    correcao: str
    status: str
    protocolo: Optional[str] = None
    codigo_status_sefaz: Optional[int] = None
    mensagem_sefaz: Optional[str] = None
    url_xml: Optional[str] = None
    url_pdf: Optional[str] = None
    xml_local: bool = False
    pdf_local: bool = False
    data_evento: Optional[datetime] = None
    data_criacao: datetime

    @classmethod
    def de_registro(cls, carta) -> "CartaCorrecaoRead":
        """`xml_local`/`pdf_local` derivam dos caminhos, como no DocumentoFiscalRead."""
        dados = cls.model_validate(carta)
        dados.xml_local = bool(carta.caminho_xml_local)
        dados.pdf_local = bool(carta.caminho_pdf_local)
        return dados


class ItemDevolucaoRequest(BaseModel):
    """Um item da nota original a devolver, em milésimos (1000 = 1 UN)."""

    documento_item_id: int = Field(..., description="ID do DocumentoFiscalItem da nota original")
    quantidade: int = Field(..., gt=0, description="Quantidade a devolver em milésimos")


class DestinatarioAvulsoRequest(BaseModel):
    """Quem está devolvendo, quando a nota de origem não identificou ninguém.

    A NF-e (modelo 55) exige destinatário com endereço; uma NFC-e sem CPF não
    tem de onde tirar isso, então o operador informa aqui.
    """

    cpf_ou_cnpj: str = Field(..., description="CPF (11) ou CNPJ (14), só dígitos ou formatado")
    nome_razao_social: str = Field(..., min_length=2, max_length=120)
    indicador_inscricao_estadual: int = Field(
        default=9, description="1=Contribuinte, 2=Isento, 9=Não contribuinte",
    )
    inscricao_estadual: Optional[str] = Field(None, max_length=20)
    logradouro: str = Field(..., min_length=2, max_length=120)
    numero: str = Field(..., min_length=1, max_length=20)
    complemento: Optional[str] = Field(None, max_length=60)
    bairro: str = Field(..., min_length=2, max_length=60)
    codigo_municipio: str = Field(..., min_length=7, max_length=7, description="Código IBGE, 7 dígitos")
    municipio: str = Field(..., min_length=2, max_length=60)
    uf: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., description="8 dígitos, com ou sem hífen")

    @model_validator(mode="after")
    def sanitizar_e_validar(self):
        self.cpf_ou_cnpj = re.sub(r"\D", "", self.cpf_ou_cnpj)
        if len(self.cpf_ou_cnpj) not in (11, 14):
            raise ValueError("Documento deve ser CPF (11 dígitos) ou CNPJ (14 dígitos).")
        self.cep = re.sub(r"\D", "", self.cep)
        if len(self.cep) != 8:
            raise ValueError("CEP deve conter 8 dígitos.")
        if not self.codigo_municipio.isdigit():
            raise ValueError("Código do município deve ser o IBGE de 7 dígitos.")
        if self.indicador_inscricao_estadual == 1 and not self.inscricao_estadual:
            raise ValueError("Inscrição Estadual obrigatória para contribuinte (indicador=1).")
        self.uf = self.uf.upper()
        return self


class EmissaoDevolucaoRequest(BaseModel):
    """Request da NF-e de devolução (finalidade 4) a partir de uma nota autorizada."""

    motivo: str = Field(..., min_length=15, max_length=255, description="Justificativa da devolução")
    devolver_estoque: bool = Field(
        default=True, description="Dá entrada dos itens no estoque quando a SEFAZ autorizar",
    )
    itens: Optional[list[ItemDevolucaoRequest]] = Field(
        None, description="Itens parciais. Omitido/vazio = devolve todo o saldo restante.",
    )
    destinatario_avulso: Optional[DestinatarioAvulsoRequest] = Field(
        None, description="Obrigatório quando a nota de origem não identificou o comprador.",
    )


class EmissaoNFCeRequest(BaseModel):
    """Request para emitir NFC-e (modelo 65).

    Separado do `EmissaoNFeRequest` porque o contrato é OUTRO: a NFC-e só
    nasce de uma venda de balcão, nunca de uma OS. Reaproveitar o schema da
    NF-e obrigaria o endpoint a recusar `numero_os` na mão — e validação de
    forma é trabalho do Pydantic, não do controlador.
    """

    venda_id: int = Field(..., gt=0, description="Venda finalizada que origina o cupom")


class EmissaoResponse(BaseModel):
    """Response padrão de operações de emissão/consulta/cancelamento."""

    documento_id: int
    ref_api: Optional[str] = None
    status: str
    mensagem: str
    ambiente: int

    @classmethod
    def de_documento(cls, doc, rotulo: str = "Documento") -> "EmissaoResponse":
        """Monta a resposta a partir do DocumentoFiscal.

        Existe para o controlador não repetir o mapeamento a cada endpoint de
        emissão — e para a mensagem de fallback ficar num lugar só quando a
        SEFAZ não devolve texto.
        """
        return cls(
            documento_id=doc.id,
            ref_api=doc.ref_api,
            status=doc.status,
            mensagem=doc.mensagem_sefaz or f"{rotulo} {doc.status.lower()}.",
            ambiente=doc.ambiente_emissao or 2,
        )


class EnvioPlataforma(BaseModel):
    """O que a plataforma respondeu a um cadastro (CSC, certificado).

    `indisponivel=True` é "a plataforma ainda não recebe isto" — o dado ficou
    só neste computador. É diferente de `aceito=False` sem `indisponivel`, que
    é recusa e vem com a frase da plataforma.
    """

    aceito: bool
    indisponivel: bool = False
    mensagem: Optional[str] = None


class FiscalConfiguracao(BaseModel):
    """Configuração atual do ambiente fiscal."""

    ambiente: int
    ambiente_label: str
    mock_ativo: bool
    certificado_configurado: bool
    certificado_valido: bool
    certificado_status: Optional[str] = None
    certificado_cnpj: Optional[str] = None
    certificado_validade: Optional[datetime] = None
    # Negativo = vencido. None = sem certificado ou sem validade conhecida.
    certificado_dias_restantes: Optional[int] = None
    serie_nfe: Optional[int] = 1
    ultimo_numero_nfe: Optional[int] = 0
    serie_nfce: Optional[int] = 1
    ultimo_numero_nfce: Optional[int] = 0
    # Trava da Rejeição 204: False até alguém confirmar a sequência inicial.
    numeracao_confirmada: bool = False
    # MASCARADO. O CSC é o segredo que autentica o QR Code — sai daqui só com
    # os 4 últimos caracteres, o bastante para o lojista reconhecer qual token
    # cadastrou. Reenviar a máscara no PUT não sobrescreve nada.
    csc_token: Optional[str] = None
    # `csc_configurado` diz que o CSC está DIGITADO AQUI. Quem monta o QR Code
    # é a emissora, e o CSC só vale quando está na ficha dela — isso quem
    # responde é `cscConfigurado` no diagnóstico da plataforma. A tela mostra
    # esse, não este.
    csc_configurado: bool = False
    csc_id: Optional[str] = None
    # Só no PUT que trouxe um CSC novo: o que a plataforma respondeu ao
    # recebê-lo. None quando o PUT não mexeu no CSC.
    csc_plataforma: Optional[EnvioPlataforma] = None
    limite_consumidor_anonimo: Optional[int] = 1000000


class DiagnosticoPlataforma(BaseModel):
    """O que a PLATAFORMA enxerga desta licença, ao lado do que o ERP manda.

    Existe por causa de um episódio concreto: a loja recebeu "CNPJ do emitente
    não autorizado" e não havia como saber, de dentro do sistema, se o problema
    era o cadastro daqui ou a ficha de lá. A investigação levou um dia e
    terminou numa leitura de código.

    `consultou=False` significa "não sei" — a plataforma não respondeu. Nunca
    tratar isso como "não configurado": é a mesma regra do `_assert_csc_configurado`.
    """

    consultou: bool
    ambiente: Optional[int] = None
    ambiente_nome: Optional[str] = None
    configurado: Optional[bool] = None
    token_configurado: Optional[bool] = None
    csc_configurado: Optional[bool] = None
    certificado_status: Optional[str] = None
    pendencias: list[str] = []

    # O lado de cá, para a comparação ficar na mesma tela.
    cnpj_erp: Optional[str] = None
    cnpj_plataforma: Optional[str] = None
    # None = não dá para comparar (a plataforma ainda não devolve o CNPJ dela).
    cnpj_confere: Optional[bool] = None


class EmissaoPreviewItem(BaseModel):
    numero_item: int
    produto_id: Optional[int] = None
    nome: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    cfop: str
    ncm: str
    cst_csosn: str = ""


class EmissaoPreviewTotais(BaseModel):
    valor_produtos: float
    descontos: float
    frete: float
    valor_nota: float
    total_tributos: int


class EmissaoPreviewDestinatario(BaseModel):
    nome: str
    documento: str


class EmissaoPreviewPagamento(BaseModel):
    nome: str
    codigo_sefaz: str
    valor: int


class EmissaoPreviewResponse(BaseModel):
    """Dados retornados para a tela de pré-visualização no frontend."""
    destinatario: EmissaoPreviewDestinatario
    totais: EmissaoPreviewTotais
    itens: list[EmissaoPreviewItem]
    formas_pagamento: list[EmissaoPreviewPagamento] = []


# --- Batch ---

class EmissaoNFeBatchRequest(BaseModel):
    """Request para emissão em lote de NF-e."""
    venda_ids: list[int] = Field(..., min_length=1, max_length=20)

    @field_validator("venda_ids")
    @classmethod
    def deduplicar(cls, v: list[int]) -> list[int]:
        return list(dict.fromkeys(v))


class EmissaoBatchItemResult(BaseModel):
    venda_id: int
    documento_id: Optional[int] = None
    status: str
    mensagem: str


class EmissaoBatchResponse(BaseModel):
    resultados: list[EmissaoBatchItemResult]
    total: int
    sucesso: int
    falha: int


# ===========================================================================
# INUTILIZAÇÃO DE NUMERAÇÃO
# ===========================================================================

class GapNumeracao(BaseModel):
    """Faixa de numeração reservada que nunca virou nota autorizada."""

    serie: int
    numero_inicial: int
    numero_final: int
    quantidade: int


class InutilizacaoRequest(BaseModel):
    """Pedido de inutilização de uma faixa de numeração."""

    serie: int = Field(..., ge=0, description="Série da NF-e")
    numero_inicial: int = Field(..., ge=1)
    numero_final: int = Field(..., ge=1)
    justificativa: str = Field(..., description="Motivo declarado à SEFAZ")

    @field_validator("justificativa")
    @classmethod
    def validar_justificativa(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 15:
            raise ValueError("A justificativa deve ter ao menos 15 caracteres.")
        return v


class InutilizacaoRead(BaseModel):
    """Registro de inutilização já solicitado."""

    id: int
    serie: int
    ano: int
    numero_inicial: int
    numero_final: int
    justificativa: str
    status: str
    protocolo: Optional[str] = None
    mensagem_sefaz: Optional[str] = None
    url_xml: Optional[str] = None
    data_solicitacao: Optional[datetime] = None
    data_homologacao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
