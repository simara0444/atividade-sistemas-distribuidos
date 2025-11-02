import redis.asyncio as redis
import os

redis_client: redis.Redis | None = None

async def connect_redis():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    try:
        await redis_client.ping()
        print(">>> Redis ping OK")
    except Exception as e:
        print(f"Erro ao conectar ao Redis: {e}")
        redis_client = None
