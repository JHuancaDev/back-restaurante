from .auth import router as auth_router
from .cart import router as cart_router
from .categories import router as categories_router
from .client_websocket import router as client_ws_router
from .favorite_controller import router as favorite_router
from .orders import router as orders_router
from .products import router as products_router
from .reviews import router as reviews_router
from .tables import router as tables_router
from .users import router as users_router

__all__ = [
    "auth_router", 
    "products_router", 
    "categories_router",
    "users_router",
    "favorite_router",
    "tables_router",
    "reviews_router", 
    "orders_router",
    "cart_router",
    "client_ws_router"
]