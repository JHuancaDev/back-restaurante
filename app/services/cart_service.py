from sqlalchemy.orm import Session, joinedload

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.schemas.order import OrderCreate, OrderItemCreate


def get_or_create_cart(db: Session, user_id: int):
    """Obtener el carrito activo del usuario o crear uno nuevo."""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    return cart

def get_cart_with_items(db: Session, user_id: int):
    """Obtener carrito con todos sus items."""
    cart = db.query(Cart).options(
        joinedload(Cart.items).joinedload(CartItem.product)
    ).filter(Cart.user_id == user_id).first()
    
    if cart:
        # Calcular campos dinámicos
        cart.total_amount = calculate_cart_total(cart)
        cart.items_count = len(cart.items)
        
        # Calcular campos para cada item
        for item in cart.items:
            item.product_name = item.product.name
            item.product_price = item.product.price
            item.product_image = item.product.image_url
            item.subtotal = item.quantity * item.product.price
    
    return cart

def add_item_to_cart(db: Session, user_id: int, item_data: CartItemCreate):
    """Agregar item al carrito."""
    cart = get_or_create_cart(db, user_id)
    
    # Verificar si el producto existe
    product = db.query(Product).filter(Product.id == item_data.product_id).first()
    if not product or not product.is_available:
        raise ValueError("Producto no disponible")
    
    # Verificar stock
    if product.stock < item_data.quantity:
        raise ValueError(f"Stock insuficiente. Disponible: {product.stock}")
    
    # Verificar si el producto ya está en el carrito
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_data.product_id
    ).first()
    
    if existing_item:
        # Actualizar cantidad si ya existe
        existing_item.quantity += item_data.quantity
        if item_data.special_instructions:
            existing_item.special_instructions = item_data.special_instructions
    else:
        # Crear nuevo item
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            special_instructions=item_data.special_instructions
        )
        db.add(cart_item)
    
    db.commit()
    return get_cart_with_items(db, user_id)

def update_cart_item(db: Session, user_id: int, item_id: int, item_update: CartItemUpdate):
    """Actualizar item del carrito."""
    cart = get_or_create_cart(db, user_id)
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise ValueError("Item no encontrado en el carrito")
    
    # Verificar stock si se está actualizando la cantidad
    if item_update.quantity is not None:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if product.stock < item_update.quantity:
            raise ValueError(f"Stock insuficiente. Disponible: {product.stock}")
        cart_item.quantity = item_update.quantity
    
    if item_update.special_instructions is not None:
        cart_item.special_instructions = item_update.special_instructions
    
    db.commit()
    return get_cart_with_items(db, user_id)

def remove_item_from_cart(db: Session, user_id: int, item_id: int):
    """Eliminar item del carrito."""
    cart = get_or_create_cart(db, user_id)
    
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()
    
    if not cart_item:
        raise ValueError("Item no encontrado en el carrito")
    
    db.delete(cart_item)
    db.commit()
    return get_cart_with_items(db, user_id)

def clear_cart(db: Session, user_id: int):
    """Vaciar todo el carrito."""
    cart = get_or_create_cart(db, user_id)
    
    # Eliminar todos los items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    
    return get_cart_with_items(db, user_id)

def calculate_cart_total(cart: Cart) -> float:
    """Calcular el total del carrito."""
    total = 0.0
    for item in cart.items:
        total += item.quantity * item.product.price
    return total

def get_cart_summary(db: Session, user_id: int):
    """Obtener resumen del carrito."""
    cart = get_cart_with_items(db, user_id)
    if not cart:
        return None
    
    total_amount = calculate_cart_total(cart)
    items_count = len(cart.items)
    
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "total_amount": total_amount,
        "items_count": items_count,
        "created_at": cart.created_at
    }


def checkout_cart(db: Session, user_id: int, order_data: dict):
    print(f"DEBUG: order_data recibido: {order_data}")

    """
    Convertir carrito en orden con información de mesa.
    """
    cart = get_cart_with_items(db, user_id)
    if not cart or not cart.items:
        raise ValueError("Carrito vacío")
    
    print(f"DEBUG: Items en carrito: {[(item.product_id, item.quantity) for item in cart.items]}")
    
     # Crear la orden desde el carrito
    order_create = OrderCreate(
        order_type=order_data.get('order_type', 'dine_in'),
        table_id=order_data.get('table_id'),
        delivery_address=order_data.get('delivery_address'),
        special_instructions=order_data.get('special_instructions', ''),
        items=[
            OrderItemCreate(
                product_id=item.product_id,
                quantity=item.quantity,
                special_instructions=item.special_instructions
            )
            for item in cart.items
        ]
    )
    
    # Usar el servicio de órdenes para crear la orden
    from app.services.order_service import create_order
    order = create_order(db, order_create, user_id)
    
    # Limpiar el carrito después de crear la orden
    clear_cart(db, user_id)
    
    return order