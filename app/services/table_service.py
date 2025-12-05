from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.table import Table
from app.schemas.table import TableCreate, TablePositionUpdate, TableUpdate


def get_tables_with_status(db: Session):
    """
    Obtener todas las mesas con información de estado y órdenes activas.
    """
    tables = db.query(Table).filter(Table.is_active == True).all()
    
    result = []
    for table in tables:
        # Buscar órdenes activas para esta mesa
        active_orders = db.query(Order).filter(
            Order.table_id == table.id,
            Order.status.in_(["recibido", "en_preparacion", "listo"])
        ).all()
        
        table_info = {
            "id": table.id,
            "number": table.number,
            "capacity": table.capacity,
            "position_x": table.position_x,
            "position_y": table.position_y,
            "is_available": table.is_available,
            "active_orders": [
                {
                    "order_id": order.id,
                    "status": order.status,
                    "created_at": order.created_at
                }
                for order in active_orders
            ],
            "active_orders_count": len(active_orders)
        }
        result.append(table_info)
    
    return result


def get_tables(db: Session, skip: int = 0, limit: int = 100, available_only: bool = False):
    query = db.query(Table).filter(Table.is_active == True)
    
    if available_only:
        query = query.filter(Table.is_available == True)
    
    return query.order_by(Table.number).offset(skip).limit(limit).all()

def get_table_by_id(db: Session, table_id: int):
    return db.query(Table).filter(Table.id == table_id).first()

def get_table_by_number(db: Session, table_number: int):
    return db.query(Table).filter(Table.number == table_number).first()

def create_table(db: Session, table: TableCreate):
    # Verificar si ya existe una mesa con ese número
    existing_table = get_table_by_number(db, table.number)
    if existing_table:
        raise ValueError("Ya existe una mesa con este número")
    
    db_table = Table(**table.dict())
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    return db_table

def update_table(db: Session, table_id: int, table_update: TableUpdate):
    db_table = get_table_by_id(db, table_id)
    if not db_table:
        return None
    
    update_data = table_update.dict(exclude_unset=True)
    
    # Verificar número único si se está actualizando
    if 'number' in update_data and update_data['number'] != db_table.number:
        existing_table = get_table_by_number(db, update_data['number'])
        if existing_table:
            raise ValueError("Ya existe una mesa con este número")
    
    for field, value in update_data.items():
        setattr(db_table, field, value)
    
    db.commit()
    db.refresh(db_table)
    return db_table

def update_table_position(db: Session, table_id: int, position_update: TablePositionUpdate):
    db_table = get_table_by_id(db, table_id)
    if not db_table:
        return None
    
    db_table.position_x = position_update.position_x
    db_table.position_y = position_update.position_y
    
    db.commit()
    db.refresh(db_table)
    return db_table

def delete_table(db: Session, table_id: int):
    db_table = get_table_by_id(db, table_id)
    if db_table:
        # Soft delete - marcamos como inactivo en lugar de eliminar
        db_table.is_active = False
        db.commit()
        db.refresh(db_table)
    return db_table

def get_available_tables(db: Session):
    return db.query(Table).filter(
        Table.is_available == True, 
        Table.is_active == True
    ).order_by(Table.number).all()

