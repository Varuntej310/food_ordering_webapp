from django.contrib import admin
from .models import CustomModel
from home.models import Menu, Category
from orders.models import Orders, OrderItem


class CustomAdminSite(admin.AdminSite):
    site_header = 'Lohit Canteen Administration'
    site_title = 'Lohit Canteen Admin'
    index_title = 'Canteen Management'

    def get_urls(self):
        from django.urls import path
        from .views import OrdersView, PastOrdersView

        urls = super().get_urls()
        custom_urls = [
            path('orders/', self.admin_view(OrdersView.as_view()), name='orders'),
            path('past-orders/', self.admin_view(PastOrdersView.as_view()), name='past_orders'),
            # path('menu/', self.admin_view(MenuManagementView.as_view()), name='menu'),
        ]
        return custom_urls + urls


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('menu_item', 'quantity', 'get_cost')
    can_delete = False
    extra = 0
    max_num = 0  # Prevents adding new items

    def has_add_permission(self, request, obj=None):
        return False

    def get_cost(self, obj):
        return f"₹{obj.get_cost()}"

    get_cost.short_description = 'Total'


class OrdersAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'mode_of_eating', 'status', 'date', 'get_total_price']
    list_filter = ['status', 'mode_of_eating']
    readonly_fields = ['user', 'mode_of_eating', 'date', 'time', 'address', 'get_total_price']
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


custom_admin_site = CustomAdminSite(name='restaurant_admin')
custom_admin_site.register(CustomModel)
custom_admin_site.register(Orders, OrdersAdmin)
custom_admin_site.register(Menu)
custom_admin_site.register(Category)

__all__ = ['custom_admin_site']