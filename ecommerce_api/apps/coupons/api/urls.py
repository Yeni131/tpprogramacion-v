from django.urls import path
from .views import CouponApplyView, CouponRemoveView

urlpatterns = [
    path('apply/',  CouponApplyView.as_view(),  name='coupon-apply'),
    path('remove/', CouponRemoveView.as_view(),  name='coupon-remove'),
]