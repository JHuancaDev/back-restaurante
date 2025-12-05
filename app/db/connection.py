from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.product import Product
from app.models.review import Review
from app.models.table import Table
from app.models.user import User

from .database import Base, engine


def create_tables():
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente!")