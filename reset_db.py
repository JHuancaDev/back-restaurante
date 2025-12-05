from app.db.database import Base, engine

print("🗑️  Eliminando todas las tablas...")
Base.metadata.drop_all(bind=engine)

print("🔄 Creando nuevas tablas...")
Base.metadata.create_all(bind=engine)

print("✅ Base de datos resetada. Ahora ejecuta:")
print("   python init_db.py")