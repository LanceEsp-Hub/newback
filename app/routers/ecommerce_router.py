from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Body
from fastapi import Path as FastAPIPath
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Annotated, Optional
from pathlib import Path
import shutil
import os
from typing import Union
from fastapi.staticfiles import StaticFiles

from app.database.database import get_db
from app.models.models import (
    Product, ProductCategory, Cart, CartItem, Order, 
    OrderItem, ProductReview, InventoryLog, Promotion, DeliverySettings
)
from app.schemas.ecommerce_schemas import (
    ProductCreate, ProductResponse, ProductAdminResponse, ProductUpdate,
    ProductCategoryCreate, ProductCategoryResponse,
    CartItemCreate, CartItemResponse, CartResponse,
    OrderCreate, OrderResponse, OrderItemCreate, OrderItemResponse,
    TransactionResponse, ProductReviewCreate, ProductReviewResponse,
    PromotionCreate, PromotionResponse, DeliverySettingsCreate, DeliverySettingsResponse
)
from app.auth.dependencies import admin_required

router = APIRouter(
    prefix="/api/ecommerce",
    tags=["ecommerce"]
)



# Product Categories Endpoints
@router.post("/categories", response_model=ProductCategoryResponse)
def create_category(
    category: ProductCategoryCreate, 
    db: Session = Depends(get_db),
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    try:
        # Validate parent category exists if provided
        if category.parent_category_id is not None:
            parent_category = db.query(ProductCategory).filter(
                ProductCategory.category_id == category.parent_category_id
            ).first()
            if not parent_category:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parent category with ID {category.parent_category_id} does not exist."
                )
        
        # Check if category name already exists
        existing_category = db.query(ProductCategory).filter(
            ProductCategory.name.ilike(category.name)
        ).first()
        if existing_category:
            raise HTTPException(
                status_code=400,
                detail=f"Category with name '{category.name}' already exists."
            )
        
        # Create the category
        db_category = ProductCategory(**category.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create category: {str(e)}"
        )

@router.get("/categories", response_model=List[ProductCategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(ProductCategory).all()

@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
def update_category(
    category_id: int,
    category_update: ProductCategoryCreate,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    try:
        # Find the category to update
        db_category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
        if not db_category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Validate parent category exists if provided and different from current
        if category_update.parent_category_id is not None:
            if category_update.parent_category_id == category_id:
                raise HTTPException(
                    status_code=400,
                    detail="Category cannot be its own parent."
                )
            
            parent_category = db.query(ProductCategory).filter(
                ProductCategory.category_id == category_update.parent_category_id
            ).first()
            if not parent_category:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parent category with ID {category_update.parent_category_id} does not exist."
                )
        
        # Check if category name already exists (excluding current category)
        existing_category = db.query(ProductCategory).filter(
            ProductCategory.name.ilike(category_update.name),
            ProductCategory.category_id != category_id
        ).first()
        if existing_category:
            raise HTTPException(
                status_code=400,
                detail=f"Category with name '{category_update.name}' already exists."
            )
        
        # Update the category
        for field, value in category_update.model_dump(exclude_unset=True).items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        return db_category
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update category: {str(e)}"
        )

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    try:
        # Find the category to delete
        category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Check if category has products
        products_count = db.query(Product).filter(Product.category_id == category_id).count()
        if products_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete category. It has {products_count} products associated with it. Please reassign or delete the products first."
            )
        
        # Check if category has subcategories
        subcategories_count = db.query(ProductCategory).filter(ProductCategory.parent_category_id == category_id).count()
        if subcategories_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete category. It has {subcategories_count} subcategories. Please delete or reassign the subcategories first."
            )
        
        # Delete the category
        db.delete(category)
        db.commit()
        return {"message": f"Category '{category.name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete category: {str(e)}"
        )

# Product Endpoints (Admin)
@router.post("/admin/products", response_model=ProductAdminResponse)
async def create_product_admin(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    discounted_price: Optional[str] = Form(None),
    stock_quantity: int = Form(...),
    category_id: Optional[str] = Form(None),
    sku: str = Form(...),
    weight: Optional[str] = Form(None),
    dimensions: Optional[str] = Form(None),
    is_active: bool = Form(True),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    # current_user: dict = Depends(admin_required)  # Uncomment when auth is ready
):
    # Ensure upload directory exists
    upload_dir = Path("app/uploads/products")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save image
    file_location = upload_dir / f"{sku}_{image.filename}"
    with file_location.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/uploads/products/{sku}_{image.filename}"

    # Convert empty strings to None or correct type
    discounted_price = float(discounted_price) if discounted_price not in ("", None) else None
    category_id = int(category_id) if category_id not in ("", None) else None
    weight = float(weight) if weight not in ("", None) else None
    
    # Validate category_id exists if provided
    if category_id is not None:
        existing_category = db.query(ProductCategory).filter(ProductCategory.category_id == category_id).first()
        if not existing_category:
            raise HTTPException(
                status_code=400, 
                detail=f"Category with ID {category_id} does not exist. Please use a valid category ID or leave empty."
            )

    # Create product data dictionary
    product_data = {
        "name": name,
        "description": description,
        "price": price,
        "discounted_price": discounted_price,
        "stock_quantity": stock_quantity,
        "category_id": category_id,
        "sku": sku,
        "image_url": image_url,
        "weight": weight,
        "dimensions": dimensions,
        "is_active": is_active
    }

    try:
        # Save product
        db_product = Product(**product_data)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        

        # Log inventory
        db_inventory = InventoryLog(
            product_id=db_product.product_id,
            change_quantity=stock_quantity,
            current_quantity=stock_quantity,
            reason="initial_stock",
            reference_id=f"product_{db_product.product_id}"
        )
        db.add(db_inventory)
        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        db.rollback()
        # Handle specific database errors
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Invalid category ID provided. Please use a valid category ID or leave the field empty."
            )
        elif "unique constraint" in str(e).lower() and "sku" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"SKU '{sku}' already exists. Please use a unique SKU."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create product: {str(e)}"
            )

from fastapi import UploadFile, File, Form

@router.put("/admin/products/{product_id}", response_model=ProductAdminResponse)
async def update_product_admin(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    discounted_price: float = Form(None),
    stock_quantity: int = Form(...),
    category_id: int = Form(None),
    sku: str = Form(...),
    weight: float = Form(None),
    dimensions: str = Form(""),
    is_active: bool = Form(True),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)
):
    db_product = db.query(Product).filter(Product.product_id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    stock_change = 0
    if stock_quantity != db_product.stock_quantity:
        stock_change = stock_quantity - db_product.stock_quantity

    db_product.name = name
    db_product.description = description
    db_product.price = price
    db_product.discounted_price = discounted_price
    db_product.stock_quantity = stock_quantity
    db_product.category_id = category_id
    db_product.sku = sku
    db_product.weight = weight
    db_product.dimensions = dimensions
    db_product.is_active = is_active

    # Handle image upload
    if image:
        upload_dir = Path("app/uploads/products")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_location = upload_dir / f"{sku}_{image.filename}"
        with file_location.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        db_product.image_url = f"/uploads/products/{sku}_{image.filename}"

    db.commit()
    db.refresh(db_product)

    # Inventory log
    if stock_change != 0:
        db_inventory = InventoryLog(
            product_id=product_id,
            change_quantity=stock_change,
            current_quantity=stock_quantity,
            reason="manual_adjustment",
            reference_id=f"product_{product_id}"
        )
        db.add(db_inventory)
        db.commit()

    return db_product


@router.delete("/admin/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Save product name snapshot in inventory_logs
    db.query(InventoryLog).filter(InventoryLog.product_id == product_id).update(
        {
            InventoryLog.product_name_snapshot: product.name,
            InventoryLog.product_id: None,
        }
    )

    # Delete related cart items
    db.query(CartItem).filter(CartItem.product_id == product_id).delete()

    # Delete related order items
    db.query(OrderItem).filter(OrderItem.product_id == product_id).delete()

    # Delete product
    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


@router.get("/admin/products", response_model=List[ProductAdminResponse])
def get_all_products_admin(
    db: Session = Depends(get_db),
    # current_user: dict = Depends(admin_required)
):
    return db.query(Product).order_by(Product.created_at.desc()).all()

@router.get("/admin/products/{product_id}", response_model=ProductAdminResponse)
def get_product_admin(
    product_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(admin_required)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Public Product Endpoints
@router.get("/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.is_active == True).all()

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Cart Endpoints
@router.post("/cart/items", response_model=CartItemResponse)
def add_to_cart(
    item: CartItemCreate, 
    user_id: int = Query(...),  # <-- explicitly mark as query param
    db: Session = Depends(get_db)
):
    try:
        print("DEBUG: add_to_cart endpoint called")
        print("  user_id:", user_id)
        print("  item:", item)
        # Check if product exists and is active
        product = db.query(Product).filter(
            Product.product_id == item.product_id,
            Product.is_active == True
        ).first()
        if not product:
            print("  ERROR: Product not available")
            raise HTTPException(status_code=404, detail="Product not available")
        
        # Check stock
        if product.stock_quantity < item.quantity:
            print(f"  ERROR: Only {product.stock_quantity} items available in stock")
            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock_quantity} items available in stock"
            )
        
        # Get or create cart
        cart = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            print("  Creating new cart for user_id:", user_id)
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
            print("Created new cart:", cart.cart_id)
        else:
            print("Found existing cart:", cart.cart_id)
        
        # Add or update item in cart
        cart_item = db.query(CartItem).filter(
            CartItem.cart_id == cart.cart_id,
            CartItem.product_id == item.product_id
        ).first()

        if cart_item:
            new_quantity = cart_item.quantity + item.quantity
            if new_quantity > product.stock_quantity:
                print(f"  ERROR: Cannot add more than {product.stock_quantity} items to cart")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot add more than {product.stock_quantity} items to cart"
                )
            cart_item.quantity = new_quantity
            db.commit()
            db.refresh(cart_item)
            print("  Updated cart item quantity:", cart_item)
        else:
            if item.quantity > product.stock_quantity:
                print(f"  ERROR: Cannot add more than {product.stock_quantity} items to cart")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot add more than {product.stock_quantity} items to cart"
                )
            cart_item = CartItem(
                cart_id=cart.cart_id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)
            print("  Cart item added successfully:", cart_item)
        return cart_item
    except Exception as e:
        print("DEBUG: Exception in add_to_cart:", str(e))
        raise

@router.get("/cart", response_model=CartResponse)
def get_cart(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@router.put("/cart/items/{cart_item_id}", response_model=CartItemResponse)
def update_cart_item_quantity(
    cart_item_id: int = FastAPIPath(...),
    quantity: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    product = db.query(Product).filter(Product.product_id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail=f"Cannot add more than {product.stock_quantity} items to cart")
    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.delete("/cart/items/{cart_item_id}")
def delete_cart_item(
    cart_item_id: int = FastAPIPath(...),
    db: Session = Depends(get_db)
):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(cart_item)
    db.commit()
    return {"detail": "Cart item deleted"}

# Delivery Settings Endpoints
@router.get("/admin/delivery-settings", response_model=DeliverySettingsResponse)
def get_delivery_settings(db: Session = Depends(get_db)):
    """Get current delivery settings"""
    settings = db.query(DeliverySettings).filter(DeliverySettings.is_active == True).first()
    if not settings:
        # Create default settings if none exist
        settings = DeliverySettings(
            delivery_fee=50.00,
            free_shipping_threshold=None,
            is_active=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

@router.put("/admin/delivery-settings", response_model=DeliverySettingsResponse)
def update_delivery_settings(
    settings: DeliverySettingsCreate,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(admin_required)  # Temporarily disabled for testing
):
    """Update delivery settings"""
    # Deactivate current settings
    current_settings = db.query(DeliverySettings).filter(DeliverySettings.is_active == True).all()
    for setting in current_settings:
        setting.is_active = False
    
    # Create new settings
    new_settings = DeliverySettings(
        delivery_fee=settings.delivery_fee,
        free_shipping_threshold=settings.free_shipping_threshold,
        is_active=True,
        updated_by=1  # Default admin ID for testing
    )
    
    db.add(new_settings)
    db.commit()
    db.refresh(new_settings)
    
    return new_settings

@router.get("/delivery-fee")
def get_delivery_fee(db: Session = Depends(get_db)):
    """Get current delivery fee for frontend"""
    settings = db.query(DeliverySettings).filter(DeliverySettings.is_active == True).first()
    if not settings:
        return {"delivery_fee": 50.00, "free_shipping_threshold": None}
    
    return {
        "delivery_fee": float(settings.delivery_fee),
        "free_shipping_threshold": float(settings.free_shipping_threshold) if settings.free_shipping_threshold else None

    }
