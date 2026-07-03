import os
import sys
import uvicorn
from app.main import app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

print(f"[INFO] Verificando se o diretório 'dist' existe para determinar o modo de execução... {DIST_DIR}")

if os.path.exists(DIST_DIR):
    sys.path.insert(0, DIST_DIR)
    print("[INFO] Rodando o Backend em modo Protegido (PyArmor)...")
else:
    print("[INFO] Rodando o Backend em modo Desenvolvimento (Código Aberto)...")
    
if __name__ == "__main__":
    ip_address = "0.0.0.0"
    port = 8000
    
    if len(sys.argv) > 2:
       ip_address = sys.argv[1]
       port = int(sys.argv[2])
        
    print(f"[INFO] Iniciando o servidor FastAPI no ip {ip_address} na porta {port}...")
    
    uvicorn.run(app, host=ip_address, port=port, reload=False)
