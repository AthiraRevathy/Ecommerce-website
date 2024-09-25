# product_cart/context_processors.py

from .models import Cart

def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        count = cart.items.count() if cart else 0
        return {'cart_count': count}
    return {'cart_count': 0}
