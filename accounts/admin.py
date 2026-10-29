from django.contrib import admin

from .models import User


def reset_registration(modeladmin, request, queryset):
    for user in queryset:
        user.registered_at = None
        user.set_unusable_password()
        user.save()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'university_id', 'phone', 'status', 'email', 'registered_at']
    list_filter = ['status']
    search_fields = ['full_name', 'university_id', 'phone']
    fields = ['full_name', 'university_id', 'phone', 'status', 'email', 'registered_at', 'is_staff']
    readonly_fields = ['registered_at']
    actions = [reset_registration]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)
