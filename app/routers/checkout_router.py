from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database.database import get_db
from app.models.models import Checkout, Order, OrderItem, Cart, CartItem, Product, Address, User, Voucher, VoucherUsage
from app.schemas.ecommerce_schemas import CheckoutCreate, CheckoutResponse, OrderResponse

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

@router.post("/")
def create_order(checkout: CheckoutCreate, db: Session = Depends(get_db)):
    try:
        print(f"DEBUG: Creating order for user {checkout.user_id}")
        print(f"DEBUG: Voucher ID: {checkout.voucher_id}")
        
        # Get user's cart
        cart = db.query(Cart).filter(Cart.user_id == checkout.user_id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Get cart items
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Validate address (only required for delivery)
        if checkout.delivery_type == "delivery":
            address = db.query(Address).filter(Address.id == checkout.address_id).first()
            if not address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Address not found"
                )
        
        # Check stock availability and calculate total
        total_amount = 0
        order_items_data = []
        
        for cart_item in cart_items:
            product = db.query(Product).filter(Product.product_id == cart_item.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {cart_item.product_id} not found"
                )
            
            if product.stock_quantity < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
                )
            
            # Calculate price (use discounted price if available)
            unit_price = float(product.discounted_price) if product.discounted_price else float(product.price)
            subtotal = unit_price * cart_item.quantity
            total_amount += subtotal
            
            order_items_data.append({
                'product_id': cart_item.product_id,
                'quantity': cart_item.quantity,
                'unit_price': unit_price,
                'subtotal': subtotal,
                'discount_applied': float(product.price) - unit_price if product.discounted_price else 0
            })
        
        print(f"DEBUG: Total amount calculated: {total_amount}")
        
        # Apply voucher discount if provided
        voucher_discount_amount = 0
        shipping_discount = 0
        
        if checkout.voucher_id:
            try:
                print(f"DEBUG: Applying voucher {checkout.voucher_id}")
                voucher = db.query(Voucher).filter(Voucher.id == checkout.voucher_id).first()
                if voucher:
                    # Check minimum order amount
                    if total_amount < float(voucher.min_order_amount):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Minimum order amount of ${float(voucher.min_order_amount)} required for this voucher"
                        )
                    
                    # Calculate voucher discount based on voucher type
                    if voucher.discount_type == 'percentage':
                        # Apply percentage discount to total amount
                        voucher_discount_amount = total_amount * (float(voucher.discount_value) / 100)
                        # Apply max discount limit if set
                        if voucher.max_discount:
                            voucher_discount_amount = min(voucher_discount_amount, float(voucher.max_discount))
                    else:
                        # Fixed amount discount
                        voucher_discount_amount = float(voucher.discount_value)
                    
                    # Calculate shipping discount
                    if voucher.free_shipping and checkout.delivery_type == "delivery":
                        shipping_discount = float(checkout.delivery_fee)
                    
                    # Apply voucher discount proportionally to each order item
                    if voucher_discount_amount > 0:
                        total_before_discount = sum(item['subtotal'] for item in order_items_data)
                        for item in order_items_data:
                            # Calculate proportional discount for this item
                            item_ratio = item['subtotal'] / total_before_discount if total_before_discount > 0 else 0
                            item_voucher_discount = voucher_discount_amount * item_ratio
                            
                            # Update item with voucher discount
                            item['voucher_discount'] = item_voucher_discount
                            item['discount_applied'] += item_voucher_discount
                            item['subtotal'] -= item_voucher_discount
                    
                    print(f"DEBUG: Voucher discount applied: {voucher_discount_amount}")
                    print(f"DEBUG: Shipping discount applied: {shipping_discount}")
                else:
                    print(f"DEBUG: Voucher {checkout.voucher_id} not found")
            except Exception as e:
                print(f"Error applying voucher: {e}")
                # Continue with order creation even if voucher application fails
        
        # Add delivery fee to total
        total_amount += checkout.delivery_fee
        # Subtract voucher discounts from total
        total_amount -= voucher_discount_amount
        total_amount -= shipping_discount
        
        print(f"DEBUG: Final total amount: {total_amount}")
        
        # Create order
        order = Order(
            user_id=checkout.user_id,
            order_date=datetime.utcnow(),
            status='pending',
            total_amount=total_amount,
            payment_method=checkout.payment_method,
            delivery_type=checkout.delivery_type,
            delivery_fee=checkout.delivery_fee,  # Add delivery fee
            shipping_address_id=checkout.address_id if checkout.delivery_type == "delivery" else None,
            billing_address_id=checkout.address_id if checkout.delivery_type == "delivery" else None,
            delivery_date=datetime.utcnow() + timedelta(days=7) if checkout.delivery_type == "delivery" else None,
            admin_notes=""
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        print(f"DEBUG: Order created with ID: {order.order_id}")

        # Apply voucher if provided
        if checkout.voucher_id:
            try:
                voucher = db.query(Voucher).filter(Voucher.id == checkout.voucher_id).first()
                if voucher:
                    # Create voucher usage record
                    voucher_usage = VoucherUsage(
                        voucher_id=checkout.voucher_id,
                        user_id=checkout.user_id,
                        order_id=order.order_id,
                        discount_amount=voucher_discount_amount,
                        shipping_discount=shipping_discount
                    )
                    db.add(voucher_usage)
                    
                    # Update voucher usage count
                    voucher.used_count += 1
                    
                    db.commit()
                    print(f"DEBUG: Voucher applied successfully")
                else:
                    print(f"DEBUG: Voucher {checkout.voucher_id} not found")
            except Exception as e:
                print(f"Error applying voucher: {e}")
                # Continue with order creation even if voucher application fails
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                subtotal=item_data['subtotal'],
                discount_applied=item_data['discount_applied'],
                status='pending'
            )
            db.add(order_item)
        
        # Clear cart
        for cart_item in cart_items:
            db.delete(cart_item)
        
        db.commit()
        
        print(f"DEBUG: Order creation completed successfully")
        
        # Return a simple success response
        return {
            "message": "Order created successfully",
            "order_id": order.order_id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "delivery_type": order.delivery_type
        }
        
    except Exception as e:
        print(f"ERROR in create_order: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}"
        )

@router.get("/orders/{user_id}")
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.order_date.desc()).all()
    return [
        {
            "id": order.order_id,
            "user_id": order.user_id,
            "order_date": order.order_date,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "payment_method": order.payment_method,
            "delivery_type": order.delivery_type,
            "admin_notes": order.admin_notes
        }
        for order in orders
    ]

@router.get("/order/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Get shipping address details
    shipping_address = None
    if order.shipping_address_id:
        shipping_address = db.query(Address).filter(Address.id == order.shipping_address_id).first()
    
    # Get billing address details
    billing_address = None
    if order.billing_address_id:
        billing_address = db.query(Address).filter(Address.id == order.billing_address_id).first()
    
    # Get order items with product details
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
    items_with_products = []
    
    for item in order_items:
        product = db.query(Product).filter(Product.product_id == item.product_id).first()
        items_with_products.append({
            "item_id": item.item_id,
            "product_id": item.product_id,
            "product_name": product.name if product else "Product not found",
            "product_image": f"http://localhost:8000{product.image_url}" if product and product.image_url else None,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
            "discount_applied": float(item.discount_applied),
            "status": item.status
        })
    
    # Get voucher usage information
    voucher_usage = None
    voucher_usage_record = db.query(VoucherUsage).filter(VoucherUsage.order_id == order.order_id).first()
    if voucher_usage_record:
        voucher = db.query(Voucher).filter(Voucher.id == voucher_usage_record.voucher_id).first()
        if voucher:
            voucher_usage = {
                "id": voucher_usage_record.id,
                "discount_amount": float(voucher_usage_record.discount_amount),
                "shipping_discount": float(voucher_usage_record.shipping_discount),
                "used_at": voucher_usage_record.used_at,
                "voucher": {
                    "id": voucher.id,
                    "code": voucher.code,
                    "name": voucher.name,
                    "description": voucher.description,
                    "discount_type": voucher.discount_type,
                    "discount_value": float(voucher.discount_value),
                    "free_shipping": voucher.free_shipping
                }
            }
    
    return {
        "id": order.order_id,
        "user_id": order.user_id,
        "order_date": order.order_date,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "payment_method": order.payment_method,
        "delivery_type": order.delivery_type,
        "delivery_fee": float(order.delivery_fee),
        "items": items_with_products,
        "shipping_address": {
            "street": shipping_address.street,
            "barangay": shipping_address.barangay,
            "city": shipping_address.city,
            "state": shipping_address.state,
            "zip_code": shipping_address.zip_code,
            "country": shipping_address.country
        } if shipping_address else None,
        "billing_address": {
            "street": billing_address.street,
            "barangay": billing_address.barangay,
            "city": billing_address.city,
            "state": billing_address.state,
            "zip_code": billing_address.zip_code,
            "country": billing_address.country
        } if billing_address else None,
        "voucher_usage": voucher_usage
    }

@router.get("/admin/orders")
def get_all_orders_for_admin(db: Session = Depends(get_db)):
    """Get all orders for admin review"""
    orders = db.query(Order).order_by(Order.order_date.desc()).all()
    
    orders_with_details = []
    for order in orders:
        # Get user info
        user = db.query(User).filter(User.id == order.user_id).first()
        
        # Get order items count
        items_count = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).count()
        
        # Get order items with product details
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
        items_with_products = []
        
        for item in order_items:
            product = db.query(Product).filter(Product.product_id == item.product_id).first()
            if product:
                items_with_products.append({
                    "product_id": item.product_id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                    "subtotal": float(item.subtotal)
                })
        
        # Get shipping address details
        shipping_address = None
        if order.shipping_address_id:
            shipping_address = db.query(Address).filter(Address.id == order.shipping_address_id).first()
        
        # Check if order used a voucher
        voucher_usage = db.query(VoucherUsage).filter(VoucherUsage.order_id == order.order_id).first()
        voucher_info = None
        if voucher_usage:
            voucher = db.query(Voucher).filter(Voucher.id == voucher_usage.voucher_id).first()
            if voucher:
                discount_text = f"${float(voucher_usage.discount_amount)} discount"
                if voucher_usage.shipping_discount > 0:
                    discount_text += f" + ${float(voucher_usage.shipping_discount)} shipping"
                
                voucher_info = {
                    "voucher_used": True,
                    "voucher_code": voucher.code,
                    "voucher_name": voucher.name,
                    "voucher_discount": discount_text
                }
        
        order_data = {
            "id": order.order_id,
            "user_id": order.user_id,
            "user_name": user.name if user else "Unknown User",
            "order_date": order.order_date,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "payment_method": order.payment_method,
            "delivery_type": order.delivery_type,
            "delivery_fee": float(order.delivery_fee),  # Add delivery fee to response
            "items_count": items_count,
            "admin_notes": order.admin_notes,
            "items": items_with_products,
            "voucher_used": voucher_info["voucher_used"] if voucher_info else False,
            "voucher_code": voucher_info["voucher_code"] if voucher_info else None,
            "voucher_name": voucher_info["voucher_name"] if voucher_info else None,
            "voucher_discount": voucher_info["voucher_discount"] if voucher_info else None,
            "shipping_address": {
                "street": shipping_address.street,
                "barangay": shipping_address.barangay,
                "city": shipping_address.city,
                "state": shipping_address.state,
                "zip_code": shipping_address.zip_code,
                "country": shipping_address.country
            } if shipping_address else None
        }
        
        orders_with_details.append(order_data)
    
    return orders_with_details

@router.put("/admin/orders/{order_id}/approve")
def approve_order(order_id: int, db: Session = Depends(get_db)):
    """Approve an order and update product stock"""
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order is already {order.status}, cannot approve"
            )
        
        # Get order items
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
        
        # Update product stock for each item
        for item in order_items:
            product = db.query(Product).filter(Product.product_id == item.product_id).first()
            if product:
                # Check if we have enough stock
                if product.stock_quantity < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock for product {product.name}. Available: {product.stock_quantity}, Requested: {item.quantity}"
                    )
                
                # Deduct stock
                product.stock_quantity -= item.quantity
        
        # Update order status
        order.status = 'approved'
        order.admin_notes = f"Order approved on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        
        db.commit()
        
        return {
            "message": "Order approved successfully",
            "order_id": order.order_id,
            "status": order.status
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving order: {str(e)}"
        )

@router.put("/admin/orders/{order_id}/deny")
def deny_order(order_id: int, reason: str = None, db: Session = Depends(get_db)):
    """Deny an order"""
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order is already {order.status}, cannot deny"
            )
        
        # Check if this order used a voucher and reverse the usage
        voucher_usage = db.query(VoucherUsage).filter(VoucherUsage.order_id == order.order_id).first()
        if voucher_usage:
            # Get the voucher and decrease its usage count
            voucher = db.query(Voucher).filter(Voucher.id == voucher_usage.voucher_id).first()
            if voucher:
                voucher.used_count = max(0, voucher.used_count - 1)  # Ensure it doesn't go below 0
            
            # Delete the voucher usage record
            db.delete(voucher_usage)
        
        # Update order status
        order.status = 'denied'
        order.admin_notes = f"Order denied on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        if reason:
            order.admin_notes += f" - Reason: {reason}"
        
        db.commit()
        
        return {
            "message": "Order denied successfully",
            "order_id": order.order_id,
            "status": order.status,
            "voucher_reversed": voucher_usage is not None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error denying order: {str(e)}"
        )