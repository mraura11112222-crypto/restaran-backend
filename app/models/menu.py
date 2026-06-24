"""Menu models – категории и позиции меню."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Category(Base):
    """Menu category (e.g. Напитки, Десерты)."""

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    restaurant = relationship("Restaurant", back_populates="categories")
    menu_items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category {self.name!r}>"


class MenuItem(Base):
    """Single dish / product on the menu (позиция меню)."""

    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    restaurant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(512), nullable=True)
    video_url = Column(String(512), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    preparation_time = Column(Integer, nullable=True, comment="Estimated time in minutes")
    ar_model_url = Column(String(512), nullable=True, comment="AR Model for AR Menu Experience")
    vr_scene_url = Column(String(512), nullable=True, comment="VR Scene for VR Ordering")
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    category = relationship("Category", back_populates="menu_items")
    restaurant = relationship("Restaurant", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")

    def __repr__(self) -> str:
        return f"<MenuItem {self.name!r} price={self.price}>"


class Recipe(Base):
    """Recipe for a menu item."""
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    instructions = Column(Text, nullable=True)
    video_url = Column(String(512), nullable=True, comment="Video tutorial for chef")

    # Relationships
    menu_item = relationship("MenuItem", backref="recipe", uselist=False)
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    """Ingredients used in a recipe, linked to InventoryItem."""
    __tablename__ = "recipe_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    inventory_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity_required = Column(Numeric(10, 3), nullable=False)

    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    inventory_item = relationship("InventoryItem")
