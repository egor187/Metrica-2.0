import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class MyConsumer(WebsocketConsumer):
    groups = ['friendship_messages', ]

    def connect(self):
        """
        Logic before accepting websocket connection. Last instruction must be accept()
        """
        self.accept()

    # def disconnect(self, code):
    #     """
    #     Logic before disconnecting from websocket.
    #     """
    #     pass

    def receive(self, text_data=None, bytes_data=None):
        """
        Receiving data (messages) from websocket
        """
        text_data_json = json.loads(text_data)
        if text_data_json['message']:
            message_json = text_data_json['message']
            #  Send event to group
            async_to_sync(self.channel_layer.group_send)(
                self.groups[0],
                {
                    #  'type' is a key corresponding to the name of the method that should be invoked on
                    #  consumers that receive the event.
                    'type': 'friendship_request_message',
                    'message': message_json
                }
            )

    #  Receive message from group
    #  Name of 'receiver' class method must be equal to 'type' key of sending event
    def friendship_request_message(self, event):
        message = event['message']
        friendship_request_sender = message[0]["from_user__username"]
        friendship_request_receivers = [elem['to_user'] for elem in message]

        #  Send message to websocket
        self.send(text_data=json.dumps({
            'message': f"{friendship_request_sender} send a friendship request to {friendship_request_receivers}"
        }))
