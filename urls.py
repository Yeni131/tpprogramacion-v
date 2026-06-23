from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.conf import settings
from django.conf.urls.static import static

from apps.products.models import Product, Category


# ── Vistas de página (template views) ────────────────────────────────────────
# FIX: estas 4 funciones estaban duplicadas (definidas dos veces en el
# archivo original). La segunda definición sobrescribía a la primera
# silenciosamente — no causaba error porque eran idénticas, pero es
# código muerto. Se deja una sola copia de cada una.

@login_required(login_url='/api/users/login/')
def checkout_page(request):
    """El checkout requiere autenticación obligatoria."""
    return render(request, 'checkout.html')

def my_orders_page(request):
    """Página de historial de compras del usuario autenticado."""
    return render(request, 'orders/my_orders.html')

def my_account_page(request):
    """Página de datos personales del usuario autenticado."""
    return render(request, 'users/my_account.html')

def offers_page(request):
    """Página pública de Ofertas y Cupones (no requiere login)."""
    return render(request, 'offers.html')

def login_page(request):
    """Si ya está logueado, redirigir al checkout."""
    if request.user.is_authenticated:
        return redirect('checkout')
    return render(request, 'users/login.html')


def register_page(request):
    """Si ya está logueado, redirigir al checkout."""
    if request.user.is_authenticated:
        return redirect('checkout')
    return render(request, 'users/register.html')


@login_required(login_url='/api/users/login/')
def order_confirmed_page(request, order_id):
    return render(request, 'orders/confirmed.html', {'order_id': order_id})


def home(request):
    featured_products = Product.objects.filter(available=True).select_related('category')[:6]
    categories        = Category.objects.all()
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories':        categories,
    })


def product_list(request):
    products   = Product.objects.filter(available=True).select_related('category')
    categories = Category.objects.all()

    category_slug = request.GET.get('category')
    price_min     = request.GET.get('price_min')
    price_max     = request.GET.get('price_max')
    sort          = request.GET.get('sort', 'default')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)

    sort_map = {
        'price_asc':  'price',
        'price_desc': '-price',
        'newest':     '-created',
        'name_asc':   'name',
    }
    products = products.order_by(sort_map.get(sort, '-created'))

    current_category = None
    if category_slug:
        current_category = Category.objects.filter(slug=category_slug).first()

    return render(request, 'products/list.html', {
        'products':         products,
        'categories':       categories,
        'current_category': current_category,
        'active_sort':      sort,
        'active_filters': {
            'categories': [category_slug] if category_slug else [],
            'price_min':  price_min,
            'price_max':  price_max,
        },
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, 'products/detail.html', {'product': product})


# ── API root ───────────────────────────────────────────────────────────────
# FIX: /api/ devolvía 404 porque nunca existió un path('api/', ...) — solo
# estaban registrados los sub-paths (api/users/, api/products/, etc.).
# Esta vista lista todos los endpoints raíz disponibles, al estilo del
# "API root" que genera DefaultRouter de DRF.
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    return Response({
        'users':    request.build_absolute_uri('/api/users/'),
        'products': request.build_absolute_uri('/api/products/'),
        'cart':     request.build_absolute_uri('/api/cart/'),
        'orders':   request.build_absolute_uri('/api/orders/'),
        'payments': request.build_absolute_uri('/api/payments/'),
        'reviews':  request.build_absolute_uri('/api/reviews/'),
        'coupons':  request.build_absolute_uri('/api/coupons/'),
    })


# ── URL patterns ──────────────────────────────────────────────────────────────

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── FRONTEND ─────────────────────────────────────────────────────────────
    path('',                      home,           name='home'),
    path('api/products/', product_list, name='product_list'),
    path('api/products/<int:pk>/', product_detail, name='product_detail'),
    # Auth pages
    path('api/users/login/', login_page, name='login'),
    path('api/users/register/', register_page, name='register'),
    # Checkout (requiere login)
    path('checkout/', checkout_page, name='checkout'),

    # Confirmación de orden
    path('orden-confirmada/<int:order_id>/', order_confirmed_page, name='order-confirmed'),

    # Historial de pedidos
    path('mis-pedidos/', my_orders_page, name='my-orders'),
    # Mi cuenta
    path('mi-cuenta/', my_account_page, name='my-account'),
    # Ofertas y cupones
    path('api/coupons/', offers_page, name='offers'),

    # ── API ───────────────────────────────────────────────────────────────────
    path('api/',          api_root,                       name='api-root'),  # FIX: agregado
    path('api/users/',    include('apps.users.api.urls')),
    path('api/products/', include('apps.products.api.urls')),
    path('api/cart/',     include('apps.cart.api.urls')),
    path('api/orders/',   include('apps.orders.api.urls')),
    path('api/payments/', include('apps.payments.api.urls')),
    path('api/reviews/',  include('apps.reviews.api.urls')),
    path('api/coupons/',  include('apps.coupons.api.urls')),
]

# ── Media (imágenes) ──────────────────────────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)