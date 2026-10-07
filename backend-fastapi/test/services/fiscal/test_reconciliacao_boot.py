"""
Reconciliação fiscal de boot: ligada ao lifespan em 07/10/2026.

A função existia e era testada desde 08/09, mas ninguém a chamava. Estes
testes cobrem o que mudou ao ligá-la: ela roda depois do boot (sem segurá-lo)
e grava documento a documento, para não travar o SQLite da loja durante as
consultas de rede.
"""
import asyncio
import inspect

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.documento_fiscal import DocumentoFiscal
from app.db.models.empresa import Empresa
from app.db.models.empresa_fiscal_settings import EmpresaFiscalSettings


@pytest.fixture
def fabrica():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _semear(db, *refs):
    db.add(Empresa(id=1, razao_social="Loja LTDA", documento="11222333000181", is_cnpj=True))
    db.flush()
    db.add(EmpresaFiscalSettings(empresa_id=1, serie_nfe=1, ultimo_numero_nfe=43, ambiente_emissao=2))
    for i, ref in enumerate(refs, start=1):
        db.add(DocumentoFiscal(tipo_documento="NFE", origem_tipo="VENDA", origem_id=1000 + i,
                               status="PROCESSANDO", ref_api=ref))
    db.commit()


def _status(fabrica, ref):
    """Lê por OUTRA sessão: só aparece o que foi de fato commitado."""
    outra = fabrica()
    try:
        return outra.query(DocumentoFiscal).filter(DocumentoFiscal.ref_api == ref).one().status
    finally:
        outra.close()


def test_grava_documento_a_documento(fabrica, monkeypatch):
    """
    O primeiro desfecho já está no banco quando o segundo documento é
    consultado. Com um commit só no fim, a escrita ficaria aberta durante
    todas as consultas — e no SQLite isso trava a venda no caixa.
    """
    from app.services.fiscal import reconciliacao

    db = fabrica()
    _semear(db, "venda-1", "venda-2")
    visto_durante_a_segunda = {}

    def consulta(db_, documento_id, empresa_id):
        doc = db_.query(DocumentoFiscal).filter(DocumentoFiscal.id == documento_id).one()
        if doc.ref_api == "venda-2":
            visto_durante_a_segunda["venda-1"] = _status(fabrica, "venda-1")
        doc.status = "AUTORIZADA"
        return doc

    monkeypatch.setattr("app.services.fiscal.emissao.consultar_documento", consulta)

    resumo = reconciliacao.reconciliar_pendentes(db)

    assert resumo == {"verificados": 2, "resolvidos": 2, "ainda_pendentes": 0}
    assert visto_durante_a_segunda == {"venda-1": "AUTORIZADA"}
    assert _status(fabrica, "venda-2") == "AUTORIZADA"
    db.close()


def test_falha_no_meio_desfaz_so_aquele_documento(fabrica, monkeypatch):
    """A consulta que quebra no meio não deixa estado parcial para o próximo commit levar."""
    from app.services.fiscal import reconciliacao

    db = fabrica()
    _semear(db, "venda-1", "venda-2")

    def consulta(db_, documento_id, empresa_id):
        doc = db_.query(DocumentoFiscal).filter(DocumentoFiscal.id == documento_id).one()
        if doc.ref_api == "venda-1":
            doc.status = "REJEITADA"          # alteração pela metade...
            raise ConnectionError("caiu")     # ...e a rede cai
        doc.status = "AUTORIZADA"
        return doc

    monkeypatch.setattr("app.services.fiscal.emissao.consultar_documento", consulta)

    resumo = reconciliacao.reconciliar_pendentes(db)

    assert resumo == {"verificados": 2, "resolvidos": 1, "ainda_pendentes": 1}
    assert _status(fabrica, "venda-1") == "PROCESSANDO"
    assert _status(fabrica, "venda-2") == "AUTORIZADA"
    db.close()


def test_no_boot_espera_e_roda_uma_vez_fora_do_loop(monkeypatch):
    from app.core import tarefas

    esperas, chamadas = [], []

    async def dormir(segundos):
        esperas.append(segundos)

    monkeypatch.setattr(tarefas.asyncio, "sleep", dormir)
    monkeypatch.setattr(
        "app.services.fiscal.reconciliacao.reconciliar_no_startup",
        lambda: chamadas.append("rodou"),
    )

    asyncio.run(tarefas._reconciliar_fiscal_apos_boot())

    assert esperas == [tarefas.ESPERA_RECONCILIACAO_FISCAL_SEGUNDOS]
    assert chamadas == ["rodou"]


def test_lifespan_agenda_e_cancela_a_reconciliacao():
    """Ficou um mês escrita sem ninguém chamar: isto acusa se for desligada de novo."""
    from app.core import tarefas

    src = inspect.getsource(tarefas.lifespan)
    assert "asyncio.create_task(_reconciliar_fiscal_apos_boot())" in src
    assert "tarefa_reconciliacao_fiscal.cancel()" in src
