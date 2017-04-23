# Standard library imports.

# Django imports.

# Third-party imports.
from channels.generic.websockets import WebsocketConsumer

# Local imports.


class TripConsumer(WebsocketConsumer):
    def connection_groups(self, **kwargs):
        return ['riders']

    def connect(self, message, **kwargs):
        self.message.reply_channel.send({'accept': True})

    def receive(self, text=None, bytes=None, **kwargs):
        # self.send(text=text, bytes=bytes)
        self.group_send(name='riders', text='cool')

    def disconnect(self, message, **kwargs):
        pass
