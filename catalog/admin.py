from django.contrib import admin
from django.utils import timezone

from .models import BuyRequest, Category, Listing, ListingImage


def approve(modeladmin, request, queryset):
    queryset.update(status='approved', reviewed_by=request.user, reviewed_at=timezone.now())


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'listing_type', 'status', 'is_sold', 'created_at']
    list_filter = ['status', 'is_sold', 'listing_type', 'category']
    search_fields = ['title']
    actions = [approve]
    inlines = [ListingImageInline]

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


admin.site.register(BuyRequest)
