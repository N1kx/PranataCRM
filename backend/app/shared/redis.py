from fastapi import Request
from redis.asyncio import Redis


def get_redis(request: Request) -> Redis:
    """FastAPI dependency exposing the app-wide Redis client (set up once in
    main.py's lifespan) to request handlers, without importing app.main."""
    return request.app.state.redis
