import os
import asyncio
import aiohttp

api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

async def delete_dns_record(session, record_id):
    try:
        async with session.delete(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}", headers=headers) as response:
            if response.status == 200:
                print(f"Deleted record: {record_id}")
    except Exception as e:
        pass  # 忽略错误并继续执行

async def delete_all_a_records():
    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        break
                    data = await response.json()
                    if 'result' not in data:
                        break
                    tasks = [delete_dns_record(session, record["id"]) for record in data["result"] if record["type"] == "A"]
                    if not tasks:
                        break
                    await asyncio.gather(*tasks)
            except Exception as e:
                pass  # 忽略错误并继续执行

asyncio.run(delete_all_a_records())
