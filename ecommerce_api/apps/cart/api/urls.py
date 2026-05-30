from django.urls import path
from .views import (
    CartDetailView, CartAddView,
    CartRemoveView, CartUpdateView, CartClearView
)

urlpatterns = [
    path('',                    CartDetailView.as_view(), name='cart-detail'),
    path('add/',                CartAddView.as_view(),    name='cart-add'),
    path('remove/<int:item_id>/', CartRemoveView.as_view(), name='cart-remove'),
    path('update/<int:item_id>/', CartUpdateView.as_view(), name='cart-update'),
    path('clear/',              CartClearView.as_view(),  name='cart-clear'),
]