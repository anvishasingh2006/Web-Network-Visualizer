import asyncio
from security import validate_url_safety

async def test():
    print("google.com safe?", await validate_url_safety("https://google.com"))
    print("localhost safe?", await validate_url_safety("http://127.0.0.1"))
    print("internal IP safe?", await validate_url_safety("http://192.168.1.1"))

asyncio.run(test())