# ---------------------------------------------------------------------------
# TESTES: core/imagem.py
# Valida o pipeline de validacao, processamento e armazenamento de imagens.
# ---------------------------------------------------------------------------

import os
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.core.imagem import (
    TAMANHO_MAXIMO_BYTES,
    deletar_imagem,
    processar_imagem,
    salvar_imagem,
    validar_imagem,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _criar_imagem_bytes(
    largura: int = 200,
    altura: int = 200,
    formato: str = "PNG",
    modo: str = "RGB",
) -> bytes:
    """Cria uma imagem em memoria e retorna os bytes."""
    img = Image.new(modo, (largura, altura), color="red")
    buffer = BytesIO()
    img.save(buffer, format=formato)
    return buffer.getvalue()


def _criar_upload_file(
    conteudo: bytes,
    filename: str = "foto.png",
    content_type: str = "image/png",
) -> UploadFile:
    """Cria um UploadFile mock a partir de bytes."""
    return UploadFile(
        file=BytesIO(conteudo),
        filename=filename,
        headers=MagicMock(get=lambda k, d=None: content_type if k == "content-type" else d),
    )


# ---------------------------------------------------------------------------
# Testes de validar_imagem
# ---------------------------------------------------------------------------

class TestValidarImagem:

    def test_tipo_mime_invalido(self):
        conteudo = b"conteudo qualquer"
        arquivo = _criar_upload_file(conteudo, "doc.txt", "text/plain")

        with pytest.raises(HTTPException) as exc_info:
            validar_imagem(arquivo)

        assert exc_info.value.status_code == 400
        assert "Tipo de arquivo" in exc_info.value.detail

    def test_extensao_invalida(self):
        conteudo = _criar_imagem_bytes()
        arquivo = _criar_upload_file(conteudo, "foto.bmp", "image/png")

        with pytest.raises(HTTPException) as exc_info:
            validar_imagem(arquivo)

        assert exc_info.value.status_code == 400
        assert "Extensao" in exc_info.value.detail

    def test_tamanho_excedido(self):
        # Cria bytes maiores que o limite
        conteudo = b"\x00" * (TAMANHO_MAXIMO_BYTES + 1)
        arquivo = _criar_upload_file(conteudo, "foto.png", "image/png")

        with pytest.raises(HTTPException) as exc_info:
            validar_imagem(arquivo)

        assert exc_info.value.status_code == 400
        assert "5MB" in exc_info.value.detail

    def test_imagem_corrompida(self):
        conteudo = b"nao e uma imagem de verdade"
        arquivo = _criar_upload_file(conteudo, "foto.png", "image/png")

        with pytest.raises(HTTPException) as exc_info:
            validar_imagem(arquivo)

        assert exc_info.value.status_code == 400
        assert "corrompido" in exc_info.value.detail

    def test_imagem_valida_retorna_bytes(self):
        conteudo = _criar_imagem_bytes()
        arquivo = _criar_upload_file(conteudo, "foto.png", "image/png")

        resultado = validar_imagem(arquivo)

        assert isinstance(resultado, bytes)
        assert len(resultado) > 0


# ---------------------------------------------------------------------------
# Testes de processar_imagem
# ---------------------------------------------------------------------------

class TestProcessarImagem:

    def test_redimensiona_imagem_grande(self):
        conteudo = _criar_imagem_bytes(3000, 2000)
        resultado = processar_imagem(conteudo, "produto")

        img = Image.open(BytesIO(resultado))
        assert img.width <= 1200
        assert img.height <= 1200

    def test_mantem_aspecto(self):
        # 3000x1500 -> deve manter proporcao 2:1
        conteudo = _criar_imagem_bytes(3000, 1500)
        resultado = processar_imagem(conteudo, "produto")

        img = Image.open(BytesIO(resultado))
        proporcao = img.width / img.height
        assert abs(proporcao - 2.0) < 0.01

    def test_nao_amplia_imagem_pequena(self):
        conteudo = _criar_imagem_bytes(100, 80)
        resultado = processar_imagem(conteudo, "produto")

        img = Image.open(BytesIO(resultado))
        assert img.width == 100
        assert img.height == 80

    def test_formato_webp(self):
        conteudo = _criar_imagem_bytes()
        resultado = processar_imagem(conteudo, "produto")

        img = Image.open(BytesIO(resultado))
        assert img.format == "WEBP"

    def test_contexto_empresa_logo(self):
        conteudo = _criar_imagem_bytes(800, 800)
        resultado = processar_imagem(conteudo, "empresa_logo")

        img = Image.open(BytesIO(resultado))
        assert img.width <= 400
        assert img.height <= 400

    def test_contexto_usuario_perfil(self):
        conteudo = _criar_imagem_bytes(600, 600)
        resultado = processar_imagem(conteudo, "usuario_perfil")

        img = Image.open(BytesIO(resultado))
        assert img.width <= 300
        assert img.height <= 300

    def test_contexto_os_foto(self):
        conteudo = _criar_imagem_bytes(4000, 3000)
        resultado = processar_imagem(conteudo, "os_foto")

        img = Image.open(BytesIO(resultado))
        assert img.width <= 1920
        assert img.height <= 1920

    def test_exif_rotacao(self):
        # Cria imagem 200x100 e injeta EXIF Orientation 6 (90 graus CW)
        # Apos exif_transpose, deve ficar 100x200
        img = Image.new("RGB", (200, 100), color="blue")

        # Usar Pillow Exif API para injetar orientation
        from PIL.ExifTags import Base as ExifBase

        exif = img.getexif()
        exif[ExifBase.Orientation] = 6  # Rotate 90 CW

        buffer = BytesIO()
        img.save(buffer, format="JPEG", exif=exif.tobytes())
        conteudo = buffer.getvalue()

        resultado = processar_imagem(conteudo, "produto")
        img_resultado = Image.open(BytesIO(resultado))

        # Apos rotacao 90 CW: 200x100 -> 100x200
        assert img_resultado.height > img_resultado.width

    def test_preserva_transparencia_logo(self):
        # Cria imagem com pixels semi-transparentes (alpha < 255)
        img = Image.new("RGBA", (500, 500), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        conteudo = buffer.getvalue()

        resultado = processar_imagem(conteudo, "empresa_logo")

        img_resultado = Image.open(BytesIO(resultado))
        # WebP preserva RGBA quando ha transparencia real
        assert img_resultado.mode == "RGBA"


# ---------------------------------------------------------------------------
# Testes de salvar_imagem
# ---------------------------------------------------------------------------

class TestSalvarImagem:

    def test_salva_arquivo_webp(self, tmp_path, monkeypatch):
        # Redireciona o diretorio base para tmp_path
        monkeypatch.setitem(
            __import__("app.core.imagem", fromlist=["CONTEXTO_IMAGEM"]).CONTEXTO_IMAGEM,
            "produto",
            {
                "max_dimensao": (1200, 1200),
                "qualidade": 85,
                "diretorio_base": str(tmp_path / "uploads"),
            },
        )

        conteudo = _criar_imagem_bytes(400, 300)
        arquivo = _criar_upload_file(conteudo, "foto.png", "image/png")

        url = salvar_imagem(arquivo, entidade_id=42, contexto="produto")

        assert url.endswith(".webp")
        assert "42" in url

        # Verifica que o arquivo existe no disco
        caminho = str(tmp_path / "uploads" / "42")
        arquivos = os.listdir(caminho)
        assert len(arquivos) == 1
        assert arquivos[0].endswith(".webp")


# ---------------------------------------------------------------------------
# Testes de deletar_imagem
# ---------------------------------------------------------------------------

class TestDeletarImagem:

    def test_remove_arquivo(self, tmp_path):
        # Cria arquivo temporario
        pasta = tmp_path / "entidade" / "1"
        pasta.mkdir(parents=True)
        arquivo = pasta / "foto.webp"
        arquivo.write_bytes(b"conteudo")

        resultado = deletar_imagem(str(arquivo))

        assert resultado is True
        assert not arquivo.exists()
        # Diretorio vazio deve ser removido
        assert not pasta.exists()

    def test_mantem_diretorio_com_outros_arquivos(self, tmp_path):
        pasta = tmp_path / "entidade" / "1"
        pasta.mkdir(parents=True)
        arquivo1 = pasta / "foto1.webp"
        arquivo2 = pasta / "foto2.webp"
        arquivo1.write_bytes(b"conteudo1")
        arquivo2.write_bytes(b"conteudo2")

        resultado = deletar_imagem(str(arquivo1))

        assert resultado is True
        assert not arquivo1.exists()
        assert arquivo2.exists()
        assert pasta.exists()  # Diretorio mantido pois nao esta vazio

    def test_arquivo_inexistente(self):
        resultado = deletar_imagem("/caminho/que/nao/existe.webp")
        assert resultado is False
