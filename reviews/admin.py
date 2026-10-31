from django.contrib import admin

from .models import Review


def approve_reviews(modeladmin, request, queryset):
    queryset.update(status='approved')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['listing', 'reviewer', 'rating', 'status', 'created_at']
    list_filter = ['status']
    actions = [approve_reviews]
