from app.db.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.table import Table
from app.models.review import Review
from app.models.cart import Cart, CartItem
from app.services.auth import get_password_hash

def init_database():
    print("🔄 Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    
    try:
        # Verificar si ya existe el usuario administrador
        admin_user = db.query(User).filter(User.email == "admin@restaurant.com").first()
        if not admin_user:
            # Crear usuario administrador
            hashed_password = get_password_hash("admin123")
            admin_user = User(
                email="admin@restaurant.com",
                password=hashed_password,
                full_name="Administrador Principal",
                role="administrador",
                auth_provider="email"  # ← Agregar este campo
            )
            db.add(admin_user)
            print("✅ Usuario administrador creado:")
            print("   Email: admin@restaurant.com")
            print("   Password: admin123")
        
        # Crear usuario normal de ejemplo
        normal_user = db.query(User).filter(User.email == "cliente@ejemplo.com").first()
        if not normal_user:
            hashed_password = get_password_hash("cliente123")
            normal_user = User(
                email="cliente@ejemplo.com",
                password=hashed_password,
                full_name="Cliente Ejemplo",
                role="usuario"
            )
            db.add(normal_user)
            print("✅ Usuario normal creado:")
            print("   Email: cliente@ejemplo.com")
            print("   Password: cliente123")
        
        # Crear categorías por defecto con imágenes opcionales
        default_categories = [
            {"name": "Entradas", "description": "Platos para comenzar tu comida", "url_image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0f/07/2f/05/burger.jpg"},
            {"name": "Platos Fuertes", "description": "Platos principales del menú", "url_image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0f/07/2f/05/burger.jpg"},
            {"name": "Postres", "description": "Dulces delicias para terminar", "url_image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0f/07/2f/05/burger.jpg"},
            {"name": "Bebidas", "description": "Refrescantes bebidas y cócteles", "url_image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0f/07/2f/05/burger.jpg"},
            {"name": "Ensaladas", "description": "Ensaladas frescas y saludables", "url_image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0f/07/2f/05/burger.jpg"}
        ]
        
        categories_dict = {}
        for cat_data in default_categories:
            existing_category = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing_category:
                category = Category(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    url_image=cat_data.get("url_image")
                )
                db.add(category)
                categories_dict[cat_data["name"]] = category
                print(f"✅ Categoría creada: {cat_data['name']}")
        
        db.flush()  # Para obtener los IDs de las categorías
        
        # Crear productos de ejemplo con los nuevos campos para IA
        default_products = [
            {
                "name": "Ceviche Clásico",
                "description": "Ceviche de pescado con limón, cebolla y ají limo",
                "price": 25.90,
                "category": "Entradas",
                "image_url": "https://www.recetasnestle.com.ec/sites/default/files/srh_recipes/4e4293857c03d819e4ae51de1e86d66a.jpg",
                "is_spicy": True,
                "is_vegan": False,
                "is_gluten_free": True,
                "preparation_time": 15,
                "calories": 320,
                "tags": ["popular", "peruano", "fresco"]
            },
            {
                "name": "Lomo Saltado",
                "description": "Salteado de lomo fino con cebolla, tomate y papas fritas",
                "price": 32.50,
                "category": "Platos Fuertes", 
                "image_url": "https://www.recetasnestle.com.ec/sites/default/files/srh_recipes/4e4293857c03d819e4ae51de1e86d66a.jpg",
                "is_spicy": False,
                "is_vegan": False,
                "is_gluten_free": False,
                "preparation_time": 20,
                "calories": 450,
                "tags": ["tradicional", "peruano", "plato-fuerte"]
            },
            {
                "name": "Ensalada César",
                "description": "Lechuga romana, crutones, parmesano y aderezo césar",
                "price": 18.00,
                "category": "Ensaladas",
                "image_url": "https://www.recetasnestle.com.ec/sites/default/files/srh_recipes/4e4293857c03d819e4ae51de1e86d66a.jpg",
                "is_spicy": False,
                "is_vegan": False,
                "is_gluten_free": False,
                "preparation_time": 10,
                "calories": 280,
                "tags": ["light", "clásico", "ensalada"]
            },
            {
                "name": "Tiramisú",
                "description": "Postre italiano con café, cacao y mascarpone",
                "price": 15.50,
                "category": "Postres",
                "image_url": "https://www.recetasnestle.com.ec/sites/default/files/srh_recipes/4e4293857c03d819e4ae51de1e86d66a.jpg",
                "is_spicy": False,
                "is_vegan": False,
                "is_gluten_free": False,
                "preparation_time": 5,
                "calories": 380,
                "tags": ["dulce", "italiano", "café"]
            },
            {
                "name": "Pisco Sour",
                "description": "Coctel peruano con pisco, limón, clara de huevo y amargo de angostura",
                "price": 22.00,
                "category": "Bebidas",
                "image_url": "https://www.recetasnestle.com.ec/sites/default/files/srh_recipes/4e4293857c03d819e4ae51de1e86d66a.jpg",
                "is_spicy": False,
                "is_vegan": True,
                "is_gluten_free": True,
                "preparation_time": 8,
                "calories": 180,
                "tags": ["coctel", "peruano", "alcohol"]
            },
            {
                "name": "Hamburguesa Clásica",
                "description": "Carne de res, queso, lechuga, tomate y salsa especial",
                "price": 28.00,
                "category": "Platos Fuertes",
                "image_url": "https://www.recetasnestle.com.ec/sites/default/files/srh_recipes/4e4293857c03d819e4ae51de1e86d66a.jpg",
                "is_spicy": False,
                "is_vegan": False,
                "is_gluten_free": False,
                "preparation_time": 15,
                "calories": 520,
                "tags": ["popular", "hamburguesa", "americana"]
            }
        ]
        
        for prod_data in default_products:
            existing_product = db.query(Product).filter(Product.name == prod_data["name"]).first()
            if not existing_product:
                category = categories_dict.get(prod_data["category"])
                if category:
                    product = Product(
                        name=prod_data["name"],
                        description=prod_data["description"],
                        price=prod_data["price"],
                        category_id=category.id,
                        image_url=prod_data["image_url"],
                        stock=50,  # Stock inicial
                    )
                    db.add(product)
                    print(f"✅ Producto creado: {prod_data['name']} - S/ {prod_data['price']}")
        
        # Crear mesas de ejemplo
        existing_tables = db.query(Table).count()
        if existing_tables == 0:
            tables_data = [
                {"number": 1, "capacity": 4, "position_x": 100.0, "position_y": 100.0},
                {"number": 2, "capacity": 2, "position_x": 200.0, "position_y": 100.0},
                {"number": 3, "capacity": 6, "position_x": 300.0, "position_y": 100.0},
                {"number": 4, "capacity": 4, "position_x": 100.0, "position_y": 200.0},
                {"number": 5, "capacity": 8, "position_x": 250.0, "position_y": 200.0},
                {"number": 6, "capacity": 4, "position_x": 400.0, "position_y": 150.0},
                {"number": 7, "capacity": 2, "position_x": 150.0, "position_y": 300.0},
                {"number": 8, "capacity": 6, "position_x": 300.0, "position_y": 250.0},
            ]
            
            for table_data in tables_data:
                table = Table(
                    number=table_data["number"],
                    capacity=table_data["capacity"],
                    position_x=table_data["position_x"],
                    position_y=table_data["position_y"],
                    is_available=True
                )
                db.add(table)
                print(f"✅ Mesa creada: #{table_data['number']} - Capacidad: {table_data['capacity']} personas")
        
        # Crear algunas reseñas de ejemplo
        existing_reviews = db.query(Review).count()
        if existing_reviews == 0 and normal_user:
            # Obtener algunos productos para las reseñas
            sample_products = db.query(Product).limit(3).all()
            
            for i, product in enumerate(sample_products):
                review = Review(
                    user_id=normal_user.id,
                    product_id=product.id,
                    rating=4.0 + (i * 0.5),  # Ratings entre 4.0 y 5.0
                    comment=f"¡Excelente {product.name}! Muy recomendado.",
                    is_approved=True
                )
                db.add(review)
                print(f"✅ Reseña creada: {product.name} - Rating: {review.rating}")
        
        db.commit()
        print("🎉 Base de datos inicializada correctamente!")
        print("\n📊 Resumen de datos creados:")
        print(f"   👥 Usuarios: {db.query(User).count()}")
        print(f"   📂 Categorías: {db.query(Category).count()}")
        print(f"   🍽️  Productos: {db.query(Product).count()}")
        print(f"   🪑 Mesas: {db.query(Table).count()}")
        print(f"   ⭐ Reseñas: {db.query(Review).count()}")
        print("\n🔑 Credenciales de prueba:")
        print("   Administrador: admin@restaurant.com / admin123")
        print("   Cliente: cliente@ejemplo.com / cliente123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al inicializar la base de datos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()