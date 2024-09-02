from litestar.channels import ChannelsPlugin
from litestar.types import SSEData

from models.user import User

from collections.abc import AsyncGenerator
from uuid import UUID

from msgspec.json import Encoder
from msgspec.json import Decoder

decoder = Decoder()
encoder = Encoder()

async def sse_generator(channels: ChannelsPlugin, user: User, client_id: UUID, resource: str) -> AsyncGenerator[SSEData, None]:
    async with channels.start_subscription([f"{resource}_{user.id}"]) as subscriber:
        async for message in subscriber.iter_events():
            # Send server event if message originates from a different client
            decoded_message = decoder.decode(message)
            if (decoded_message["origin_client"] != str(client_id)):
                del decoded_message["origin_client"]
                yield encoder.encode(decoded_message)
