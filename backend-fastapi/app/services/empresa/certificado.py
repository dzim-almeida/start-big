# ---------------------------------------------------------------------------
# ARQUIVO: services/empresa/certificado.py
# DESCRICAO: Empresa - certificado digital: envio para a plataforma (focus) e
#            certificados instalados no Windows.
# ---------------------------------------------------------------------------

import platform
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

# Importa modelos e serviços
from app.db.models.empresa import Empresa as EmpresaModel
from app.schemas.empresa import (
    WindowsCertificateRead,
)
from app.db.crud import empresa as empresa_crud
from app.services.empresa.cadastro import NOT_FOUND_EXCE
from app.services.empresa.fiscal import get_or_create_fiscal_settings


# ---------------------------------------------------------------------------
# FUNÇÕES DE CERTIFICADO DIGITAL
# ---------------------------------------------------------------------------

def upload_certificado_focus(
    db: Session,
    empresa_id: int,
    file: UploadFile,
    senha: str,
    resultado_envio: Optional[dict] = None,
) -> EmpresaModel:
    """
    Valida um certificado A1 (PKCS#12) destinado a emissao pela API na nuvem.

    O arquivo NAO fica no disco e a senha NAO e guardada (o antigo
    `upload_certificado_a1`, que guardava, foi aposentado em 12/10/2026):
    quem assina e o servico remoto, entao a loja nao
    precisa manter o material criptografico.

    ATENCAO: o envio para a API Online ainda e um mock (passo 5). O que esta
    funcional e a validacao local do certificado e a gravacao dos metadados.
    """
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.backends import default_backend

    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)
    if not empresa_in_db:
        raise NOT_FOUND_EXCE

    # 1. Ler arquivo em memoria
    file_content = file.file.read()

    # 2. Validar certificado com a senha
    try:
        private_key, certificate, chain = pkcs12.load_key_and_certificates(
            file_content,
            senha.encode('utf-8'),
            default_backend()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha incorreta ou certificado invalido"
        )
    finally:
        file.file.close()

    if certificate is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificado nao encontrado no arquivo"
        )

    # 3. Extrair metadados
    cert_subject = certificate.subject.rfc4514_string()
    cert_validade = certificate.not_valid_after_utc

    # Extrair CNPJ se possivel
    import re
    cnpj_match = (
        re.search(r'2\.5\.4\.97=#131[a-f0-9]{2}([0-9]{14})', cert_subject)
        or re.search(r'CNPJ:?([0-9]{14})', cert_subject)
    )
    cert_cnpj = cnpj_match.group(1) if cnpj_match else None

    # 4. Verificar se nao esta expirado.
    # `not_valid_after_utc` vem COM fuso, entao a comparacao tem que ser com um
    # datetime tambem com fuso -- utcnow() aqui levanta TypeError.
    if cert_validade < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificado expirado em {cert_validade.strftime('%d/%m/%Y')}"
        )

    # 5. Entrega a plataforma, que cadastra o certificado na emissora.
    #
    # Era `time.sleep(0.5)` com um comentario dizendo "AINDA MOCK": o arquivo
    # morria na memoria do processo e o cadastro era gravado como
    # CONECTADO_NUVEM. A tela dizia "Conectado" e nada tinha sido enviado --
    # uma mentira que so aparecia na primeira emissao, longe daqui.
    #
    # A rota do outro lado ainda nao existe (docs/fiscal-onboarding-plano.md
    # secao 4.1). Ate existir, o resultado volta `indisponivel=True` e o
    # cadastro fica VALIDADO_LOCAL -- que e a verdade: o arquivo foi conferido
    # aqui e nao chegou na emissora. No dia em que a rota subir, o mesmo codigo
    # passa a gravar CONECTADO_NUVEM sem precisar de instalador novo.
    import base64

    from app.services.fiscal.http import get_fiscal_client
    from app.db.crud import fiscal as fiscal_crud

    from app.services.fiscal.ativacao import contato_da_empresa, montar_emitente_para_ativacao

    settings_fiscais = get_or_create_fiscal_settings(db, empresa_id)

    # Ativação, e não só o certificado (06/10/2026): junto vai o emitente, para
    # a plataforma criar a empresa na emissora quando ela ainda não existe.
    # Plataforma antiga cai sozinha na rota antiga (ver `ativar_emissao`).
    email, telefone = contato_da_empresa(empresa_in_db)
    resultado = get_fiscal_client(
        settings_fiscais.ambiente_emissao or 2,
        fiscal_crud.get_licenca_token(db),
    ).ativar_emissao(
        montar_emitente_para_ativacao(
            empresa_in_db, fiscal_crud.get_endereco_empresa(db, empresa_id), settings_fiscais,
        ),
        email,
        telefone,
        base64.b64encode(file_content).decode("ascii"),
        senha,
    )

    # Recusa EXPLICITA (CNPJ divergente, certificado invalido para a emissora)
    # e erro do lojista, e precisa parar aqui com a frase que a plataforma deu.
    # Indisponibilidade nao: essa segue, e o cadastro diz o que de fato houve.
    if not resultado["aceito"] and not resultado["indisponivel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado.get("mensagem") or "A emissora recusou o certificado.",
        )

    # 6. Atualizar configuracoes fiscais
    settings_fiscais.tipo_certificado = "NUVEM"
    settings_fiscais.certificado_digital_path = None
    settings_fiscais.certificado_validade = cert_validade
    settings_fiscais.certificado_subject = cert_subject
    settings_fiscais.certificado_thumbprint = None
    # A senha NAO fica: quem assina e o servico remoto.
    settings_fiscais.certificado_senha = None
    settings_fiscais.certificado_status = (
        "CONECTADO_NUVEM" if resultado["aceito"] else "VALIDADO_LOCAL"
    )
    if cert_cnpj:
        settings_fiscais.certificado_cnpj = cert_cnpj

    # Quem chamou quer saber o que a plataforma disse (a tela mostra o motivo
    # quando o certificado não chegou à emissora). Opcional para não mudar a
    # assinatura de quem já chama.
    if resultado_envio is not None:
        resultado_envio.update(
            aceito=resultado["aceito"],
            mensagem=resultado.get("mensagem"),
            certificado_status=settings_fiscais.certificado_status,
        )

    db.flush()
    db.refresh(empresa_in_db)

    return empresa_in_db


def list_windows_certificates() -> List[WindowsCertificateRead]:
    """
    Lista certificados digitais do Windows Certificate Store.

    NOTA: O backend deve rodar no mesmo usuário do SO que possui os certificados.
    Esta função só funciona em Windows.

    Returns:
        Lista de certificados válidos (não expirados).
    """
    if platform.system() != "Windows":
        return []

    try:
        import wincertstore
    except ImportError:
        # wincertstore não instalado
        return []

    certificates = []
    now = datetime.now()

    try:
        with wincertstore.CertSystemStore("MY") as store:
            for cert in store.itercerts():
                # Filtrar certificados expirados
                if hasattr(cert, 'not_valid_after') and cert.not_valid_after:
                    if cert.not_valid_after < now:
                        continue

                certificates.append(WindowsCertificateRead(
                    thumbprint=cert.get_thumbprint() if hasattr(cert, 'get_thumbprint') else "",
                    subject=str(cert.get_name()) if hasattr(cert, 'get_name') else "",
                    friendly_name=getattr(cert, 'friendly_name', "") or str(cert.get_name()) if hasattr(cert, 'get_name') else "",
                    issuer=str(cert.get_issuer()) if hasattr(cert, 'get_issuer') else "",
                    valid_until=cert.not_valid_after.isoformat() if hasattr(cert, 'not_valid_after') and cert.not_valid_after else None,
                    serial_number=str(cert.get_serial_number()) if hasattr(cert, 'get_serial_number') else ""
                ))
    except Exception as e:
        # Log error but return empty list
        print(f"[WARN] Erro ao listar certificados Windows: {e}")

    return certificates


def vincular_certificado_windows(
    db: Session,
    empresa_id: int,
    thumbprint: str
) -> EmpresaModel:
    """
    Vincula um certificado do Windows Certificate Store à empresa.

    Args:
        db: Sessão do banco de dados.
        empresa_id: ID da empresa.
        thumbprint: Thumbprint (identificador) do certificado.

    Raises:
        HTTPException 404: Se a empresa ou certificado não for encontrado.

    Returns:
        EmpresaModel: Empresa atualizada.
    """
    empresa_in_db = empresa_crud.get_empresa_by_id(db, empresa_id=empresa_id)
    if not empresa_in_db:
        raise NOT_FOUND_EXCE

    # Validar existência no store
    certs = list_windows_certificates()
    cert = next((c for c in certs if c.thumbprint == thumbprint), None)

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificado não encontrado no Windows Certificate Store"
        )

    # Atualizar configurações fiscais
    settings = get_or_create_fiscal_settings(db, empresa_id)
    settings.tipo_certificado = "WINDOWS"
    settings.certificado_thumbprint = thumbprint
    settings.certificado_subject = cert.subject
    settings.certificado_validade = (
        datetime.fromisoformat(cert.valid_until) if cert.valid_until else None
    )
    settings.certificado_digital_path = None  # Limpar arquivo se estava usando

    db.flush()
    db.refresh(empresa_in_db)

    return empresa_in_db
