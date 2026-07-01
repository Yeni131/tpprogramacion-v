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
from apps.users.api.views import LoginView, RegisterView


# ── Vistas de página (template views) ────────────────────────────────────────

def login_page(request):
    if request.method == 'POST':
        return LoginView.as_view()(request)
    if request.user.is_authenticated:
        return redirect('checkout')
    return render(request, 'users/login.html')


def register_page(request):
    if request.method == 'POST':
        return RegisterView.as_view()(request)
    if request.user.is_authenticated:
        return redirect('checkout')
    return render(request, 'users/register.html')


@login_required(login_url='/api/users/login/')
def checkout_page(request):
    return render(request, 'checkout.html')


@login_required(login_url='/api/users/login/')
def order_confirmed_page(request, order_id):
    from apps.payments.models import Payment
    from apps.orders.models import Order
    try:
        order   = Order.objects.get(pk=order_id, user=request.user)
        payment = Payment.objects.filter(order=order).first()
        payment_method = payment.payment_method if payment else 'cash'
    except Order.DoesNotExist:
        payment_method = 'cash'

    return render(request, 'orders/confirmed.html', {
        'order_id':       order_id,
        'payment_method': payment_method,
    })


def my_orders_page(request):
    return render(request, 'orders/my_orders.html')


def my_account_page(request):
    return render(request, 'users/my_account.html')


def offers_page(request):
    return render(request, 'offers.html')


def home(request):
    featured_products = Product.objects.filter(available=True).select_related('category')[:6]
    categories        = Category.objects.all()
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'categories':        categories,
    })


def product_list(request):
    # Si viene con parámetros de API, dejar que el include lo maneje
    if request.GET.get('format') == 'json' or request.GET.get('search'):
        from apps.products.api.views import ProductListView
        return ProductListView.as_view()(request)

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
    # Si viene con parámetros de API, delegar a la APIView
    if request.GET.get('format') == 'json' or request.META.get('HTTP_ACCEPT') == 'application/json':
        from apps.products.api.views import ProductDetailView
        return ProductDetailView.as_view()(request, pk=pk)

    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, 'products/detail.html', {'product': product})


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
    path('',                                     home,                 name='home'),
    path('api/users/login/',                     login_page,           name='login'),
    path('api/users/register/',                  register_page,        name='register'),
    path('api/checkout/',                        checkout_page,        name='checkout'),
    path('api/orden-confirmada/<int:order_id>/', order_confirmed_page, name='order-confirmed'),
    path('api/mis-pedidos/',                     my_orders_page,       name='my-orders'),
    path('api/mi-cuenta/',                       my_account_page,      name='my-account'),
    path('api/coupons/',                         offers_page,          name='offers'),
    path('api/products/',                        product_list,         name='product_list'),
    path('api/products/<int:pk>/',               product_detail,       name='product_detail'),

    # ── API ───────────────────────────────────────────────────────────────────
    path('api/',          api_root,                        name='api-root'),
    path('api/users/',    include('apps.users.api.urls')),
    path('api/products/', include('apps.products.api.urls')),
    path('api/cart/',     include('apps.cart.api.urls')),
    path('api/orders/',   include('apps.orders.api.urls')),
    path('api/payments/', include('apps.payments.api.urls')),
    path('api/reviews/',  include('apps.reviews.api.urls')),
    path('api/coupons/',  include('apps.coupons.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)