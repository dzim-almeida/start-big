# Arquivo para segurança, como hashing de senhas e verificação

import bcrypt # type: ignore

def verificar_senha(senha: str, senha_hash: str) -> bool:
    senha_bytes = senha.encode('utf-8')
    senha_hash_bytes = senha_hash.encode('utf-8')
    # Verifica se a senha fornecida corresponde ao hash armazenado
    return bcrypt.checkpw(senha_bytes, senha_hash_bytes)

def gerar_senha_hash(senha: str) -> str:
    # Gera um hash seguro para a senha fornecida
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')