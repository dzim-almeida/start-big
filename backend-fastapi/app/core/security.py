# Arquivo para segurança, como hashing de senhas e verificação

from passlib.context import CryptContext  # type: ignore

# Contexto de criptografia para hashing de senhas
codificador = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha: str, senha_hash: str) -> bool:
    # Verifica se a senha fornecida corresponde ao hash armazenado
    return codificador.verify(senha, senha_hash)

def gerar_senha_hash(senha: str) -> str:
    # Gera um hash seguro para a senha fornecida
    return codificador.hash(senha)