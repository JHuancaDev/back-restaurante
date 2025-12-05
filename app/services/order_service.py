from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.table import Table
from app.schemas.order import OrderCreate, OrderUpdate


def get_orders(db: Session, skip: int = 0, limit: int = 100, user_id: int = None):
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.table),
        joinedload(Order.user)
    )
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    # 🔥 AGREGAR ESTA PARTE: Asignar campos adicionales a todas las órdenes
    for order in orders:
        # Agregar información de la mesa
        if order.table:
            order.table_number = order.table.number
            order.table_capacity = order.table.capacity
        
        # Agregar información del usuario
        order.user_name = order.user.full_name if order.user else "Usuario"
        
        # Agregar información de productos a los items
        for item in order.items:
            if item.product:
                item.product_name = item.product.name
                item.product_image = item.product.image_url
            else:
                # Valores por defecto si no hay producto
                item.product_name = "Producto no disponible"
                item.product_image = ""
    
    return orders

# En order_service.py - CORREGIR el método get_order_by_id
def get_order_by_id(db: Session, order_id: int):
    order = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product),
        joinedload(Order.table),
        joinedload(Order.user)
    ).filter(Order.id == order_id).first()
    
    if order:
        print(f"DEBUG: Order encontrada - ID: {order.id}")
        print(f"DEBUG: Número de items: {len(order.items)}")
        
        # Agregar información de la mesa a la respuesta
        if order.table:
            order.table_number = order.table.number
            order.table_capacity = order.table.capacity
            print(f"DEBUG: Mesa - Número: {order.table_number}, Capacidad: {order.table_capacity}")
        
        # Agregar información del usuario
        order.user_name = order.user.full_name if order.user else "Usuario"
        print(f"DEBUG: Usuario: {order.user_name}")
        
        # Agregar información de productos a los items (CRÍTICO)
        for index, item in enumerate(order.items):
            print(f"DEBUG: Item {index} - Product ID: {item.product_id}")
            
            if item.product:
                # Asignar los campos directamente al objeto OrderItem
                item.product_name = item.product.name
                item.product_image = item.product.image_url
                print(f"DEBUG:   Producto: {item.product_name}, Imagen: {item.product_image}")
            else:
                # Valores por defecto si no hay producto
                item.product_name = "Producto no disponible"
                item.product_image = ""
                print(f"DEBUG:   Producto no encontrado en BD")
    
    return order

def create_order(db: Session, order: OrderCreate, user_id: int):
    # Validar mesa si es dine_in
    if order.order_type == 'dine_in' and order.table_id:
        table = db.query(Table).filter(Table.id == order.table_id).first()
        if not table:
            raise ValueError("Mesa no encontrada")
        if not table.is_available:
            raise ValueError("Mesa no disponible")
        if not table.is_active:
            raise ValueError("Mesa no está activa")
    
    # Calcular total y verificar stock
    total_amount = 0
    order_items = []
    
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise ValueError(f"Producto {item.product_id} no encontrado")
        if product.stock < item.quantity:
            raise ValueError(f"Stock insuficiente para {product.name}. Disponible: {product.stock}")
        
        subtotal = item.quantity * product.price
        total_amount += subtotal
        
        order_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": product.price,
            "subtotal": subtotal,
            "special_instructions": item.special_instructions
        })
    
    # Crear la orden
    db_order = Order(
        user_id=user_id,
        order_type=order.order_type,
        table_id=order.table_id if order.order_type == 'dine_in' else None,
        delivery_address=order.delivery_address,
        special_instructions=order.special_instructions,
        total_amount=total_amount,
        status="recibido"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    print(f"DEBUG: Orden creada - ID: {db_order.id}")
    
    # Crear items de la orden y actualizar stock
    for item_data in order_items:
        db_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)
        
        # Actualizar stock del producto
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]
        if product.stock < 0:
            product.stock = 0
        
        print(f"DEBUG: Item creado - Product ID: {item_data['product_id']}, Cantidad: {item_data['quantity']}")
    
    # Si es dine_in, marcar mesa como no disponible
    if order.order_type == 'dine_in' and order.table_id:
        table = db.query(Table).filter(Table.id == order.table_id).first()
        table.is_available = False
        print(f"DEBUG: Mesa {table.id} marcada como no disponible")
    
    db.commit()
    
    # 🔥 FORZAR la recarga con todas las relaciones
    db.expire_all()  # Esto fuerza a recargar todos los objetos desde la BD
    
    # Cargar relaciones para la respuesta
    db_order = get_order_by_id(db, db_order.id)
    
    # Verificación final
    if db_order and db_order.items:
        for item in db_order.items:
            if not hasattr(item, 'product_name') or item.product_name is None:
                print(f"ERROR: Item {item.id} no tiene product_name")
            if not hasattr(item, 'product_image') or item.product_image is None:
                print(f"ERROR: Item {item.id} no tiene product_image")
    
    return db_order

# En app/services/order_service.py - CORREGIR el método update_order_status
def update_order_status(db: Session, order_id: int, status: str):
    db_order = get_order_by_id(db, order_id)
    if db_order:
        db_order.status = status
        
        # Si la orden se completa y es dine_in, liberar la mesa
        if status == "completado" and db_order.order_type == 'dine_in' and db_order.table_id:
            table = db.query(Table).filter(Table.id == db_order.table_id).first()
            if table:
                table.is_available = True
        
        db.commit()
        db.refresh(db_order)
        
        # 🔥 CORREGIDO: Usar BackgroundTasks en lugar de asyncio.create_task
        # Las notificaciones se manejarán desde el controlador
        print(f"✅ Estado actualizado - Orden #{order_id} -> {status}")
        
    return db_order

def update_order(db: Session, order_id: int, order_update: OrderUpdate):
    db_order = get_order_by_id(db, order_id)
    if not db_order:
        return None
    
    update_data = order_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def delete_order(db: Session, order_id: int):
    db_order = get_order_by_id(db, order_id)
    if db_order:
        # Si es dine_in, liberar la mesa
        if db_order.order_type == 'dine_in' and db_order.table_id:
            table = db.query(Table).filter(Table.id == db_order.table_id).first()
            if table:
                table.is_available = True
        
        db.delete(db_order)
        db.commit()
    return db_order