from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from orders.models import Orders
from django.core.exceptions import ObjectDoesNotExist


class OrderStatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.user = self.scope['user']

        # if not await self.can_access_order():
        #     await self.close()
        #     return

        self.group_name = f"order_{self.order_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        print('connected to websocket', self.group_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        pass

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    @database_sync_to_async
    def can_access_order(self):
        try:
            order = Orders.objects.get(id=self.order_id)
            # Allow access if user is staff or the order owner
            return self.user.is_staff or order.user == self.user
        except ObjectDoesNotExist:
            return False

    async def order_status_update(self, event):
        print(f"Received order status update for order {event['order_id']}")
        await self.send_json({
            "order_id": event["order_id"],
            "status": event["status"],
            "timestamp": event["timestamp"]
        })
