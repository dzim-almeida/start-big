# app/services/fiscal/__init__.py
from app.services.fiscal.core import verificar_completude_venda, verificar_completude_os

__all__ = ["verificar_completude_venda", "verificar_completude_os"]