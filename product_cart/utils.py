# product_cart/utils.py

def calculate_totals(cart_items, coupon_code=None):
    # Your logic to calculate totals based on cart items and optional coupon
    total = sum(item.price * item.quantity for item in cart_items)
    shipping_fee = 5.00  # Example fee
    discount_amount = 0.00
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            discount_amount = total * (coupon.discount_percentage / 100)
        except Coupon.DoesNotExist:
            discount_amount = 0.00
    
    grand_total = total + shipping_fee - discount_amount
    return total, shipping_fee, discount_amount, grand_total

def process_order(cart, address, payment_method, total, shipping_fee, discount_amount, grand_total):
    # Your logic to create an order and process payment
    order = Order.objects.create(
        user=cart.user,
        address=address,
        payment_method=payment_method,
        total=total,
        shipping_fee=shipping_fee,
        discount_amount=discount_amount,
        grand_total=grand_total
    )
    
    for item in CartItem.objects.filter(cart=cart):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
    
    return order
