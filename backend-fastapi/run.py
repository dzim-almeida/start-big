import os
import sys
import uvicorn
from app.main import app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

APP_ENV = os.getenv("APP_ENV", "development").lower()
print(f"[INFO] Ambiente de execução: {APP_ENV}")

if APP_ENV == "production":
    if not os.path.exists(DIST_DIR):
        print("[ERROR] O diretório 'dist' não foi encontrado. Certifique-se de que o código foi empacotado corretamente.")
        sys.exit(1)
    
    sys.path.insert(0, DIST_DIR)
    print("[INFO] Rodando o Backend em modo Protegido (PyArmor)...")
else:
    print("[INFO] Rodando o Backend em modo Desenvolvimento (Código Aberto)...")
    
if __name__ == "__main__":
    ip_address = "0.0.0.0"
    port = 8080

    if len(sys.argv) > 2:
       ip_address = sys.argv[1]
       port = int(sys.argv[2])
        
    print(f"[INFO] Iniciando o servidor FastAPI no ip {ip_address} na porta {port}...")
    
    uvicorn.run(app, host=ip_address, port=port, reload=False)
