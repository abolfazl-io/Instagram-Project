import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Thread, Message, MyUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated or not await self.user_is_participant():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == 'new_message':
            message_body = data.get('message', '')
            parent_message_id = data.get('parent_message_id')
            
            # ایجاد پیام و دریافت داده‌های کامل آن
            new_message_data = await self.create_new_message(message_body, parent_message_id)
            
            # ارسال پیام به گروه
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': new_message_data
                }
            )
        elif event_type == 'like_message':
            message_id = data['message_id']
            like_update_data = await self.toggle_message_like(message_id)
            if like_update_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    { 'type': 'like_update', 'update': like_update_data }
                )
        elif event_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'sender': self.user.username
                }
            )

    # Handler برای ارسال پیام به کلاینت
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    async def like_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'like_update',
            'update': event['update']
        }))

    async def typing_indicator(self, event):
        if event['sender'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'sender': event['sender']
            }))

    # --- توابع پایگاه داده ---

    @sync_to_async
    def user_is_participant(self):
        try:
            thread = Thread.objects.get(id=self.thread_id)
            return thread.participants.filter(id=self.user.id).exists()
        except Thread.DoesNotExist:
            return False

    @sync_to_async
    def create_new_message(self, body, parent_id):
        parent_message = None
        if parent_id:
            try:
                parent_message = Message.objects.get(id=parent_id)
            except Message.DoesNotExist:
                pass
        
        message = Message.objects.create(
            thread_id=self.thread_id,
            sender=self.user,
            body=body,
            parent_message=parent_message
        )
        message.seen_by.add(self.user)

        parent_info = None
        if message.parent_message:
            parent_info = {
                'sender': message.parent_message.sender.username,
                'body': message.parent_message.body
            }

        return {
            'id': message.id,
            'sender': message.sender.username,
            'body': message.body,
            'file_url': None,
            'is_video': False,
            'created_at': message.created_at.strftime('%H:%M'),
            'is_reply': bool(parent_message),
            'parent': parent_info,
            'likes_count': 0
        }
        
    @sync_to_async
    def toggle_message_like(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if self.user in message.likes.all():
                message.likes.remove(self.user)
            else:
                message.likes.add(self.user)
            
            return {
                'message_id': message.id,
                'likes_count': message.likes.count()
            }
        except Message.DoesNotExist:
            return None