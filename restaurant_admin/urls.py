from django.urls import path
from .views import OrdersView, PastOrdersView

app_name = 'restaurant_admin'

urlpatterns = [
    # Define your URLs here
    path('orders/', OrdersView.as_view(), name='orders'),
    path('past-orders/', PastOrdersView.as_view(), name='past_orders'),
    # path('menu/', MenuManagementView.as_view(), name='menu'),
]