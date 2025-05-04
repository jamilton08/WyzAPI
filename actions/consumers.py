

import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ActionsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print(self.scope["user"].username)
        print(self.scope["user"].email)
        print(self.scope["org"])
        self.org = self.scope['org'].pk
        self.org_action = f'action_group_{self.org}'
        await self.channel_layer.group_add(self.org_action, self.channel_name)
        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.org_action, self.channel_name)

    async def recieve(self, text_data):
        print("____________________________manito que pasa_____________________")
        text_as_json = json.loads(text_data)
        message = text_as_json["message"]

        # IDEA: Implement something such as recieve a code that will identify what kind of actions is recieved and resolve
        # TODO: after implemented what decides we will send to group, it wil be sort or a encrypt and decrypt and then we send to group

        await self.channel_layer.group_send(
            self.org_action, {type : "code.decipher", "message" : message}
        )


    async def code_decipher(self, event):
        msessage = event["message"]
        # IDEA: here wil will implement the above comments inside recieve function
        await self.send(text_data = json.dumps({"message": message}))


    async def receive_json(self, message):
        command = message.get("command")
        if command == "Say hello !":
            print(message["data_string"])
            await self.send_json({
                "command_response": "The command to \
                say hello was received ",
                "data_string_bacK": message.get
              ("data_string", None)
            })
