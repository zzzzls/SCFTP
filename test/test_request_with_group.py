import httpx
import asyncio

async def test_request_with_group(group_name:str|None=None):
    if group_name is None:
        proxy = "http://127.0.0.1:9042" 
    else:
        proxy = f"http://{group_name}:pwd@127.0.0.1:9042"
        
    print(f"====test proxy -> {proxy}")
    
    async def fetch(url):
        async with httpx.AsyncClient(proxy=proxy, verify=False, timeout=10) as client:
            response = await client.get(url)
            data = response.json()
            print(data["ip"], data["city_name"])

    tasks = [asyncio.create_task(fetch("https://api.ip2location.io/")) for _ in range(5)]
    await asyncio.gather(*tasks, return_exceptions=True)
    


if __name__ == '__main__':
    asyncio.run(test_request_with_group())
    asyncio.run(test_request_with_group(group_name="group1"))
    asyncio.run(test_request_with_group(group_name="group2"))
    asyncio.run(test_request_with_group(group_name="group3"))  # 测试不存在的分组
