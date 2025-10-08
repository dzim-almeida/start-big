# Importando as classes base

from sqlalchemy.ext.declarative import declarative_base # type: ignore

Base = declarative_base()

from app.schemas.product import Product 

