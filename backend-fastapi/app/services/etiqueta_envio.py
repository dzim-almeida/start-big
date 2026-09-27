# ---------------------------------------------------------------------------
# ARQUIVO: app/services/etiqueta_envio.py
# MÓDULO: Service — Dados das etiquetas de envio (Central de Etiquetas, fase 5)
# ---------------------------------------------------------------------------
"""
De onde vêm os dados de uma etiqueta de volume / DANFE Simplificado.

- Remetente: SEMPRE o cadastro da Empresa (nada de cidade escrita no modelo).
- Destinatário: o cliente da OS (pelo objeto) ou da Venda, com o primeiro
  endereço cadastrado.
- NF-e: o documento fiscal AUTORIZADO, modelo 55, de finalidade normal. A
  referência do documento à origem é polimórfica e NÃO é igual nos dois
  lados: para a Venda, `origem_id` guarda o NÚMERO da venda (emissao.py),
  e para a OS guarda o id.

Permissão: cada tipo de origem exige a permissão do seu módulo. Quem só
cuida do estoque não enxerga o endereço dos clientes das vendas.
"""

import re
from datetime import datetime
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.busca import extrair_termos, normalizar
from app.core.enum import EntityType, OrdemServicoStatus, VendaStatus
from app.db.models.cliente import Cliente, ClientePF, ClientePJ
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.endereco import Endereco
from app.db.models.objeto_servico import ObjetoServico
from app.db.models.ordem_servico import OrdemServico
from app.db.models.venda import Venda
from app.schemas.etiqueta_envio import DadosEnvio, EnderecoEnvio, NfeEnvio, OrigemEnvioItem, ParteEnvio

PERMISSOES_VENDA = ["venda", "view_sales", "manage_sales", "delete_sales"]
PERMISSOES_OS = ["servico"]

# Quantas de cada tipo entram na busca. É uma lista para escolher o que
# acabou de ser embalado, não um relatório.
JANELA_BUSCA = 300
LIMITE_RESULTADOS = 30


def pode(usuario_token: dict[str, Any], permissoes: list[str]) -> bool:
    """Mesma regra de `check_permission`, para decidir sem levantar 403."""
    if usuario_token.get("is_master") is True:
        return True
    perms = usuario_token.get("permissoes") or {}
    return bool(perms.get("all")) or any(perms.get(p) is True for p in permissoes)


def _exigir(usuario_token: dict[str, Any], permissoes: list[str]) -> None:
    if not pode(usuario_token, permissoes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permissão negada. Requer: '{', '.join(permissoes)}'",
        )


def _nome_cliente(cliente: Optional[Cliente]) -> Optional[str]:
    if cliente is None:
        return None
    if isinstance(cliente, ClientePJ):
        return cliente.nome_fantasia or cliente.razao_social
    if isinstance(cliente, ClientePF):
        return cliente.nome
    return None


def _documento_cliente(cliente: Cliente) -> Optional[str]:
    if isinstance(cliente, ClientePJ):
        return cliente.cnpj
    if isinstance(cliente, ClientePF):
        return cliente.cpf
    return None


def _endereco(endereco: Optional[Endereco]) -> Optional[EnderecoEnvio]:
    if endereco is None:
        return None
    uf = endereco.estado.value if hasattr(endereco.estado, "value") else str(endereco.estado or "")
    return EnderecoEnvio(
        logradouro=endereco.logradouro or "",
        numero=endereco.numero or "",
        complemento=endereco.complemento,
        bairro=endereco.bairro or "",
        cidade=endereco.cidade or "",
        uf=uf,
        cep=endereco.cep or "",
    )


def _destinatario(cliente: Optional[Cliente]) -> Optional[ParteEnvio]:
    if cliente is None:
        return None
    return ParteEnvio(
        # Para ENTREGA, a razão social é o que vale no documento; o fantasia
        # só entra quando não há razão (cadastro incompleto).
        nome=(cliente.razao_social if isinstance(cliente, ClientePJ) else None) or _nome_cliente(cliente) or "",
        documento=_documento_cliente(cliente),
        inscricao_estadual=cliente.ie if isinstance(cliente, ClientePJ) else None,
        telefone=cliente.celular or cliente.telefone,
        endereco=_endereco(cliente.endereco[0] if cliente.endereco else None),
    )


def _remetente(db: Session, empresa_id: int) -> ParteEnvio:
    empresa = db.get(Empresa, empresa_id)
    if empresa is None:
        return ParteEnvio()
    endereco = db.scalars(
        select(Endereco).where(
            Endereco.tipo_entidade == EntityType.EMPRESA, Endereco.id_entidade == empresa_id
        )
    ).first()
    return ParteEnvio(
        nome=empresa.razao_social or empresa.nome_fantasia or "",
        documento=empresa.documento,
        inscricao_estadual=empresa.inscricao_estadual,
        telefone=empresa.celular or empresa.telefone,
        endereco=_endereco(endereco),
    )


def _nfe_autorizada(db: Session, origem_tipo: str, origem_id: Optional[int]) -> Optional[DocumentoFiscal]:
    """A NF-e (modelo 55) autorizada mais recente da origem, de finalidade normal."""
    if origem_id is None:
        return None
    stmt = (
        select(DocumentoFiscal)
        .where(
            DocumentoFiscal.origem_tipo == origem_tipo,
            DocumentoFiscal.origem_id == origem_id,
            DocumentoFiscal.tipo_documento.in_(["NFE", "nfe"]),
            DocumentoFiscal.status == "AUTORIZADA",
            DocumentoFiscal.finalidade_emissao == 1,
            DocumentoFiscal.chave_acesso.is_not(None),
        )
        .order_by(DocumentoFiscal.data_autorizacao.desc(), DocumentoFiscal.id.desc())
    )
    return db.scalars(stmt).first()


def _nfe(doc: Optional[DocumentoFiscal]) -> Optional[NfeEnvio]:
    if doc is None or doc.numero_documento is None or not doc.chave_acesso:
        return None
    return NfeEnvio(
        numero=doc.numero_documento,
        serie=doc.serie or 0,
        chave_acesso=doc.chave_acesso,
        protocolo=doc.protocolo_autorizacao,
        data_autorizacao=doc.data_autorizacao,
        data_emissao=doc.data_emissao or doc.data_autorizacao,
        valor_total=doc.valor_total,
        ambiente=doc.ambiente_emissao,
        destinatario_nome=doc.destinatario_nome_enviado,
        destinatario_documento=doc.destinatario_documento_enviado,
    )


def _numero_venda(venda: Venda) -> str:
    return str(venda.numero_venda) if venda.numero_venda is not None else f"#{venda.id}"


# ---------------------------------------------------------------------------
# Busca de origem
# ---------------------------------------------------------------------------

def _casa(termos: list[str], *campos: Optional[str]) -> bool:
    if not termos:
        return True
    alvo = normalizar(" ".join(c for c in campos if c))
    return all(t in alvo for t in termos)


def _sequencial_os(numero_os: str) -> Optional[int]:
    """O número sequencial da OS: "OS-2026-000002" → 2."""
    grupos = re.findall(r"\d+", numero_os or "")
    return int(grupos[-1]) if grupos else None


def buscar_origens(db: Session, usuario_token: dict[str, Any], busca: Optional[str]) -> list[OrigemEnvioItem]:
    """OS e vendas recentes que podem virar etiqueta de envio, mais novas primeiro.

    Busca só com dígitos ("02") compara com o NÚMERO da OS/venda, e não com o
    texto: "02" está dentro de "2026", e casaria com toda OS do ano.
    """
    termos = extrair_termos(busca)
    digitado = (busca or "").strip()
    numero_digitado = int(digitado) if digitado.isdigit() else None
    itens: list[OrigemEnvioItem] = []

    if pode(usuario_token, PERMISSOES_OS):
        ordens = db.scalars(
            select(OrdemServico)
            .options(selectinload(OrdemServico.objeto).selectinload(ObjetoServico.cliente))
            .where(OrdemServico.ativo.is_(True), OrdemServico.status != OrdemServicoStatus.CANCELADA)
            .order_by(OrdemServico.data_criacao.desc())
            .limit(JANELA_BUSCA)
        ).all()
        for os_ in ordens:
            cliente = os_.objeto.cliente if os_.objeto else None
            nome = _nome_cliente(cliente)
            identificador = os_.objeto.numero_serie if os_.objeto else None
            casa = (
                _sequencial_os(os_.numero_os) == numero_digitado or _casa(termos, nome, identificador)
                if numero_digitado is not None
                else _casa(termos, os_.numero_os, nome, identificador)
            )
            if casa:
                itens.append(OrigemEnvioItem(
                    tipo="os", id=os_.id, numero=os_.numero_os, cliente_nome=nome, data=os_.data_criacao,
                ))

    if pode(usuario_token, PERMISSOES_VENDA):
        vendas = db.scalars(
            select(Venda)
            .options(selectinload(Venda.cliente))
            .where(Venda.status == VendaStatus.FINALIZADA)
            .order_by(Venda.criado_em.desc())
            .limit(JANELA_BUSCA)
        ).all()
        for venda in vendas:
            nome = _nome_cliente(venda.cliente)
            numero = _numero_venda(venda)
            casa = (
                venda.numero_venda == numero_digitado or _casa(termos, nome)
                if numero_digitado is not None
                else _casa(termos, numero, f"venda {numero}", nome)
            )
            if casa:
                itens.append(OrigemEnvioItem(
                    tipo="venda", id=venda.id, numero=numero, cliente_nome=nome, data=venda.criado_em,
                ))

    itens.sort(key=lambda i: i.data or datetime.min, reverse=True)
    itens = itens[:LIMITE_RESULTADOS]

    # Só os que ficaram na lista pagam a consulta da NF-e.
    for item in itens:
        if item.tipo == "os":
            item.tem_nfe = _nfe_autorizada(db, "OS", item.id) is not None
        else:
            venda = db.get(Venda, item.id)
            item.tem_nfe = venda is not None and _nfe_autorizada(db, "VENDA", venda.numero_venda) is not None
    return itens


# ---------------------------------------------------------------------------
# Dados de uma origem
# ---------------------------------------------------------------------------

def dados_os(db: Session, usuario_token: dict[str, Any], os_id: int) -> DadosEnvio:
    _exigir(usuario_token, PERMISSOES_OS)
    os_ = db.scalars(
        select(OrdemServico)
        .options(selectinload(OrdemServico.objeto).selectinload(ObjetoServico.cliente).selectinload(Cliente.endereco))
        .where(OrdemServico.id == os_id, OrdemServico.ativo.is_(True))
    ).first()
    if os_ is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada.")
    cliente = os_.objeto.cliente if os_.objeto else None
    return DadosEnvio(
        tipo="os",
        id=os_.id,
        numero=os_.numero_os,
        identificador=os_.objeto.numero_serie if os_.objeto else None,
        remetente=_remetente(db, usuario_token["empresa_id"]),
        destinatario=_destinatario(cliente),
        nfe=_nfe(_nfe_autorizada(db, "OS", os_.id)),
    )


def dados_venda(db: Session, usuario_token: dict[str, Any], venda_id: int) -> DadosEnvio:
    _exigir(usuario_token, PERMISSOES_VENDA)
    venda = db.scalars(
        select(Venda)
        .options(selectinload(Venda.cliente).selectinload(Cliente.endereco))
        .where(Venda.id == venda_id)
    ).first()
    if venda is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada.")
    return DadosEnvio(
        tipo="venda",
        id=venda.id,
        numero=_numero_venda(venda),
        remetente=_remetente(db, usuario_token["empresa_id"]),
        destinatario=_destinatario(venda.cliente),
        nfe=_nfe(_nfe_autorizada(db, "VENDA", venda.numero_venda)),
    )


def remetente(db: Session, usuario_token: dict[str, Any]) -> ParteEnvio:
    """Só o remetente — para a etiqueta avulsa, cujo destinatário é digitado na tela."""
    return _remetente(db, usuario_token["empresa_id"])
