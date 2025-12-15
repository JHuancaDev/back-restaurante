from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Importar routers
from app.controllers.auth import router as auth_router
from app.controllers.products import router as products_router
from app.controllers.categories import router as categories_router
from app.controllers.users import router as users_router
from app.controllers.favorite_controller import router as favorites_router
from app.controllers.tables import router as tables_router
from app.controllers.reviews import router as reviews_router
from app.controllers.orders import router as orders_router
from app.controllers.cart import router as cart_router
from app.controllers.client_websocket import router as client_ws_router
from app.controllers.websocket import router as websocket_router
from app.controllers.extras import router as extras_router

from app.db.connection import create_tables

# Crear tablas en la base de datos
create_tables()

app = FastAPI(
    title="Restaurant API",
    description="Backend para aplicación de restaurante",
    version="4.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Añade esto
    max_age=600,
)

# Incluir routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(users_router)
app.include_router(favorites_router)
app.include_router(tables_router)
app.include_router(reviews_router)
app.include_router(orders_router)
app.include_router(cart_router) 
app.include_router(client_ws_router)
app.include_router(websocket_router)
app.include_router(extras_router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Restaurante"}

# Información de WebSockets
@app.get("/websocket-info")
def websocket_info():
    return {
        "websocket_url": "ws://localhost:8000/orders/ws",
        "supported_protocols": ["json"],
        "features": ["real-time-orders", "notifications"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ws_ping_interval=20,  # Mantener conexión activa
        ws_ping_timeout=20,
        ws="websockets"  # Forzar uso de websockets
    )