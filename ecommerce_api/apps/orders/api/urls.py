from django.urls import path
from .views import (
    OrderListView, OrderCreateView,
    OrderDetailView, OrderCancelView
)

urlpatterns = [
    path('',              OrderListView.as_view(),  name='order-list'),
    path('create/',       OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/',     OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
]