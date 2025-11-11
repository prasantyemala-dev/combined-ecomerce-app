import requests
import os

class CuelinksAPI:
    BASE_URL = "https://api.cuelinks.com/integrate/"

    def __init__(self, publisher_id, api_key):
        self.publisher_id = publisher_id
        self.api_key = api_key

    def generate_affiliate_url(self, target_url):
        """Generate affiliate URL for a given target product/link"""
        endpoint = f"{self.BASE_URL}get_affiliate_link.json"
        headers = {
            "Publisher-ID": self.publisher_id,
            "API-Key": self.api_key,
            "Accept": "application/json"
        }
        payload = {
            "url": target_url
        }
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("affiliate_link", "")

# Usage Example (use env variables or config, don't hardcode keys)
if __name__ == "__main__":
    PUBLISHER_ID = os.getenv("CUELINKS_PUBLISHER_ID")
    API_KEY = os.getenv("CUELINKS_API_KEY")
    cuelinks = CuelinksAPI(PUBLISHER_ID, API_KEY)
    test_url = "https://www.amazon.in/dp/B08L5V7Q5K"  # Example product URL
    affiliate_url = cuelinks.generate_affiliate_url(test_url)
    print("Affiliate URL:", affiliate_url)