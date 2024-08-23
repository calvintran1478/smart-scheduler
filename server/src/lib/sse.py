from litestar.channels import ChannelsPlugin
from litestar.types import SSEData

from models.user import User

from collections.abc import AsyncGenerator

async def sse_generator(channels: ChannelsPlugin, user: User, resource: str) -> AsyncGenerator[SSEData, None]:
    async with channels.start_subscription([f"{resource}_{user.id}"]) as subscriber:
        async for message in subscriber.iter_events():
            yield message
