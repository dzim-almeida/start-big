# Roteador principal da API V1

from fastapi import APIRouter # type: ignore
from app.api.v1.endpoints import auth, usuario

router = APIRouter()
router.include_router(usuario.router, prefix="/usuarios", tags=["Usuários"])
router.include_router(auth.router, prefix="/auth", tags=["Login"])