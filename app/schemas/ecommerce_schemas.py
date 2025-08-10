from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ProductCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_category_id: Optional[int] = None
    image_url: Optional[str] = None

class ProductCategoryResponse(ProductCategoryCreate):
    category_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    discounted_price: Optional[float] = Field(None, gt=0)
    stock_quantity: int = Field(0, ge=0)
    category_id: Optional[int] = None
    sku: str
    image_url: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[str] = None
    is_active: bool = True

class ProductResponse(BaseModel):
    product_id: int
    name: str
    description: Optional[str]
    price: float
    discounted_price: Optional[float]
    stock_quantity: int
    category_id: Optional[int]
    sku: Optional[str]
    image_url: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    discounted_price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[str] = None
    is_active: Optional[bool] = None

class ProductAdminResponse(ProductResponse):
    product_id: int
    name: str
    description: Optional[str]
    price: float
    discounted_price: Optional[float]
    stock_quantity: int
    sku: Optional[str]
    category_id: Optional[int]
    weight: Optional[float]
    dimensions: Optional[str]
    is_active: bool
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, gt=0)

class CartItemResponse(BaseModel):
    cart_item_id: int
    product: ProductResponse
    quantity: int
    added_at: datetime
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    cart_id: int
    user_id: int
    items: List[CartItemResponse]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    returned = "returned"

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float
    discount_applied: float = 0

class OrderCreate(BaseModel):
    shipping_address_id: int
    billing_address_id: Optional[int] = None
    payment_method: str
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    unit_price: float
    subtotal: float
    discount_applied: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    order_date: datetime
    status: OrderStatus
    total_amount: float
    payment_method: str
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"

class TransactionResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    transaction_date: datetime
    status: TransactionStatus
    
    class Config:
        from_attributes = True

class ProductReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None

class ProductReviewResponse(ProductReviewCreate):
    id: int
    user_id: int
    review_date: datetime
    
    class Config:
        from_attributes = True

class PromotionCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    start_date: datetime
    end_date: datetime
    min_order_amount: float = 0
    max_uses: Optional[int] = None
    is_active: bool = True

class PromotionResponse(PromotionCreate):
    id: int
    current_uses: int
    
    class Config:
        from_attributes = True

class AddressCreate(BaseModel):
    user_id: int
    street: str
    barangay: str
    city: str
    state: str
    zip_code: str
    country: str

class AddressResponse(AddressCreate):
    id: int
    created_at: datetime

class DeliveryType(str, Enum):
    delivery = "delivery"
    pickup = "pickup"

class CheckoutCreate(BaseModel):
    user_id: int
    address_id: int
    total_price: float
    payment_method: str = "Cash on Delivery"
    delivery_type: DeliveryType = DeliveryType.delivery
    delivery_fee: float = 0.00  # New delivery fee field
    voucher_id: Optional[int] = None  # Voucher ID if applied
    # Add more fields as needed

class CheckoutResponse(CheckoutCreate):
    id: int
    created_at: datetime

class VoucherCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    discount_type: str  # 'percentage' or 'fixed'
    discount_value: float
    min_order_amount: float = 0
    max_discount: Optional[float] = None
    free_shipping: bool = False
    usage_limit: Optional[int] = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True

class VoucherResponse(VoucherCreate):
    id: int
    used_count: int
    created_at: datetime
    created_by: Optional[int] = None
    
    class Config:
        from_attributes = True

class VoucherUsageCreate(BaseModel):
    voucher_id: int
    user_id: int
    order_id: int
    discount_amount: float
    shipping_discount: float = 0

class VoucherUsageResponse(VoucherUsageCreate):
    id: int
    used_at: datetime
    
    class Config:
        from_attributes = True

class VoucherValidationRequest(BaseModel):
    code: str
    user_id: int
    subtotal: float
    delivery_fee: float = 0

class VoucherValidationResponse(BaseModel):
    is_valid: bool
    voucher: Optional[VoucherResponse] = None
    discount_amount: float = 0
    shipping_discount: float = 0
    message: str = ""

class UserVoucherCreate(BaseModel):
    user_id: int
    voucher_id: int
    assigned_by: Optional[int] = None

class UserVoucherResponse(BaseModel):
    id: int
    user_id: int
    voucher_id: int
    assigned_at: datetime
    assigned_by: Optional[int] = None
    is_active: bool
    voucher: VoucherResponse
    
    class Config:
        from_attributes = True

class DeliverySettingsCreate(BaseModel):
    delivery_fee: float = Field(..., gt=0)
    free_shipping_threshold: Optional[float] = Field(None, gt=0)
    is_active: bool = True

class DeliverySettingsResponse(DeliverySettingsCreate):
    id: int
    updated_at: datetime
    updated_by: Optional[int] = None
    
    class Config:
        from_attributes = True