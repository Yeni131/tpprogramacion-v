from django.urls import path
from .views import ReviewListCreateView, ReviewDeleteView

urlpatterns = [
    path('<int:product_id>/',          ReviewListCreateView.as_view(), name='review-list-create'),
    path('<int:product_id>/<int:pk>/', ReviewDeleteView.as_view(),     name='review-delete'),
]