from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.utils import timezone
from orders.models import Orders
from home.models import Menu, Category

# Create your views here.

@method_decorator(staff_member_required, name='dispatch')
class OrdersView(TemplateView):
    template_name = 'restaurant_admin/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Get selected tab from query params, default to 'all'
        selected_tab = self.request.GET.get('tab', 'all')
        context['selected_tab'] = selected_tab

        # Base queryset for active orders
        orders_query = Orders.objects.filter(
            status__in=['pending', 'confirmed', 'ready', 'out_for_delivery']
        ).prefetch_related('items', 'items__menu_item').order_by('-date')

        # Filter by mode of eating if not 'all'
        if selected_tab != 'all':
            orders_query = orders_query.filter(mode_of_eating=selected_tab)

        context['active_orders_count'] = orders_query.count()
        context['avg_prep_time'] = 25
        context['available_staff'] = 4
        context['pending_orders'] = orders_query

        return context

    def post(self, request, *args, **kwargs):
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        if order_id and new_status:
            try:
                order = Orders.objects.get(id=order_id)
                if new_status == order.get_next_status():
                    order.status = new_status
                    order.save()
            except Orders.DoesNotExist:
                pass
        return self.get(request, *args, **kwargs)

    def get_status_choices(self, order):
        if order.mode_of_eating == 'delivery':
            return Orders.DELIVERY_STATUS_CHOICES
        return Orders.PICKUP_STATUS_CHOICES


@method_decorator(staff_member_required, name='dispatch')
class PastOrdersView(TemplateView):
    template_name = 'restaurant_admin/past_orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_orders'] = Orders.objects.filter(
            status__in=['completed', 'delivered']
        ).prefetch_related('items', 'items__menu_item').order_by('-date')
        return context


