import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def delete_all_a_records(api_token, zone_id):
    a_records = get_a_records(api_token, zone_id)
    if not a_records:
        print("No A records found.")
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(delete_dns_record, api_token, zone_id, record['id']) for record in a_records]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error deleting A record: {e}")

def get_a_records(api_token, zone_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'result' in data:
            return data['result']
        else:
            return []
    except requests.RequestException as e:
        print(f"Error fetching A records: {e}")
        return []

def delete_dns_record(api_token, zone_id, record_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        print(f"Deleted A record {record_id}")
    except requests.RequestException as e:
        raise Exception(f"Error deleting A record {record_id}: {e}")

def main():
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")

    if api_token and zone_id:
        delete_all_a_records(api_token, zone_id)
    else:
        print("Please provide both CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID.")

if __name__ == "__main__":
    main()
