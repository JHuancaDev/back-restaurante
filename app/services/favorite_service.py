from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.favorite import Favorite
from app.models.product import Product
from app.models.user import User
from app.schemas.favorite import FavoriteCreate


class FavoriteService:
    def add_favorite(self, db: Session, data: FavoriteCreate, current_user_id: int):
        # Validar que el usuario existe
        user = db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Validar que el producto existe
        product = db.query(Product).filter(Product.id == data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Verificar que el usuario solo gestiona sus propios favoritos
        if data.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes gestionar favoritos de otros usuarios"
            )

        # Verificar si ya existe en favoritos
        existing = db.query(Favorite).filter(
            Favorite.user_id == data.user_id,
            Favorite.product_id == data.product_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto ya está en favoritos"
            )

        favorite = Favorite(
            user_id=data.user_id,
            product_id=data.product_id
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite

    def remove_favorite(self, db: Session, user_id: int, product_id: int, current_user_id: int):
        # Verificar permisos
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes eliminar favoritos de otros usuarios"
            )
            
        favorite = db.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.product_id == product_id
        ).first()

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorito no encontrado"
            )

        db.delete(favorite)
        db.commit()
        return {"message": "Producto eliminado de favoritos correctamente"}

    def get_favorites_by_user(self, db: Session, user_id: int, current_user_id: int):
        # Verificar permisos
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes ver los favoritos de otros usuarios"
            )
            
        favorites = db.query(Favorite).join(Favorite.product).filter(Favorite.user_id == user_id).all()
        return favorites