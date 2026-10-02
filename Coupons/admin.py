from django.contrib import admin
from django.utils import timezone
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'valid_til', 'currently_valid']
    search_fields = ['code']
    ordering = ['-created_at']

    def currently_valid(self, obj):
        return obj.is_valid()
    currently_valid.boolean = True  # shows a green tick / red cross icon in admin list
    currently_valid.short_description = 'Still Valid?'