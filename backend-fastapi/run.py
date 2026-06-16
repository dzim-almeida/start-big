import os
import sys
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

if os.path.exists(DIST_DIR):
    sys.path.insert(0, DIST_DIR)
    print("[INFO] Rodando o Backend em modo Protegido (PyArmor)...")
else:
    print("[INFO] Rodando o Backend em modo Desenvolvimento (Código Aberto)...")
    
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)