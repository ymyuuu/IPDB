import os
import asyncio
import aiohttp

api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

async def delete_dns_record(session, record_id):
    async with session.delete(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}", headers=headers) as response:
        if response.status == 200:
            print(f"{record_id}")

async def delete_all_a_records():
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                tasks = [delete_dns_record(session, record["id"]) for record in data["result"] if record["type"] == "A"]
                if not tasks: break
                await asyncio.gather(*tasks)

asyncio.run(delete_all_a_records())
