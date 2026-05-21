from django.urls import path
from .views import ReviewListCreateView, ReviewDeleteView

urlpatterns = [
    path('<slug:product_slug>/',          ReviewListCreateView.as_view(), name='review-list-create'),
    path('<slug:product_slug>/<int:pk>/', ReviewDeleteView.as_view(),     name='review-delete'),
]