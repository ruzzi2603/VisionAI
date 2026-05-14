from channels.generic.websocket import AsyncJsonWebsocketConsumer


class AlertConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("alerts", self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard("alerts", self.channel_name)

    async def alert_message(self, event):
        await self.send_json(event["payload"])
