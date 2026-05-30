"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('apps.users.api.urls')),
    path('api/products/', include('apps.products.api.urls')),
    path('api/cart/',     include('apps.cart.api.urls')),
    path('api/orders/',   include('apps.orders.api.urls')),
    path('api/payments/', include('apps.payments.api.urls')), 
    path('api/reviews/',   include('apps.reviews.api.urls')),  
    path('api/coupons/',   include('apps.coupons.api.urls')), 
]
