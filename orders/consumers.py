from channels.generic.websocket import AsyncWebsocketConsumer
import json

class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
        else:
            self.user_group = f'user_{self.scope["user"].id}'
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def order_update(self, event):
        await self.send(text_data=json.dumps(event['data']))