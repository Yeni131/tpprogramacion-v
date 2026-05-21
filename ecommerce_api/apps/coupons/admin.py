from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'active', 'valid_from', 'valid_to', 'used_count']
    list_editable = ['active']