# ---------------------------------------------------------------------------
# ARQUIVO: test/core/test_permissoes.py
# DESCRICAO: LIC-01 (CT-17) -- verificacao das permissoes da pasta de dados.
#
# A leitura real da lista de acesso (Get-Acl) so existe no Windows; aqui se
# testa a regra de decisao, com a lista de acesso simulada, e o "fora do
# Windows nao faz nada".
# ---------------------------------------------------------------------------

import logging

from app.core import permissoes


def test_ct17_fora_do_windows_nao_faz_nada_e_nao_lanca(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(permissoes.sys, "platform", "linux")
    chamou = []
    monkeypatch.setattr(permissoes, "_ler_sids_com_acesso", lambda caminho: chamou.append(caminho))

    with caplog.at_level(logging.WARNING):
        permissoes.verificar_pasta_de_dados(str(tmp_path))

    assert chamou == []                     # nem tentou ler a lista de acesso
    assert "PASTA_DADOS_ABERTA" not in caplog.text


def test_pasta_liberada_para_todos_gera_aviso_sem_alterar_nada(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(permissoes.sys, "platform", "win32")
    monkeypatch.setattr(permissoes, "_esta_no_perfil", lambda caminho: True)
    # S-1-1-0 = "Todos"; S-1-5-18 = SYSTEM (esperado)
    monkeypatch.setattr(permissoes, "_ler_sids_com_acesso", lambda caminho: {"S-1-1-0", "S-1-5-18"})

    with caplog.at_level(logging.WARNING):
        permissoes.verificar_pasta_de_dados(str(tmp_path))

    assert "PASTA_DADOS_ABERTA" in caplog.text


def test_pasta_restrita_no_perfil_nao_gera_aviso(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(permissoes.sys, "platform", "win32")
    monkeypatch.setattr(permissoes, "_esta_no_perfil", lambda caminho: True)
    monkeypatch.setattr(permissoes, "_ler_sids_com_acesso",
                        lambda caminho: {"S-1-5-18", "S-1-5-32-544", "S-1-5-21-1-2-3-1001"})

    with caplog.at_level(logging.WARNING):
        permissoes.verificar_pasta_de_dados(str(tmp_path))

    assert "PASTA_DADOS_ABERTA" not in caplog.text


def test_pasta_fora_do_perfil_gera_aviso(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(permissoes.sys, "platform", "win32")
    monkeypatch.setattr(permissoes, "_esta_no_perfil", lambda caminho: False)
    monkeypatch.setattr(permissoes, "_ler_sids_com_acesso", lambda caminho: {"S-1-5-18"})

    with caplog.at_level(logging.WARNING):
        permissoes.verificar_pasta_de_dados(str(tmp_path))

    assert "PASTA_DADOS_ABERTA" in caplog.text


def test_falha_ao_ler_a_lista_de_acesso_so_vai_para_o_log(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(permissoes.sys, "platform", "win32")
    monkeypatch.setattr(permissoes, "_esta_no_perfil", lambda caminho: True)

    def _falha(caminho):
        raise OSError("powershell nao respondeu")

    monkeypatch.setattr(permissoes, "_ler_sids_com_acesso", _falha)

    with caplog.at_level(logging.WARNING):
        permissoes.verificar_pasta_de_dados(str(tmp_path))   # nao pode lancar

    assert "PASTA_DADOS_ABERTA" not in caplog.text
