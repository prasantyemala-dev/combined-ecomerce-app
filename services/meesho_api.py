import json
import os

def search_meesho_deals(keywords="fashion"):
    """
    Simulates a search on Meesho's API.
    Returns a list of items or an error string.
    """
    mock_data_path = os.path.join(os.path.dirname(__file__), '..', 'mock_data', 'meesho.json')
    try:
        with open(mock_data_path, 'r') as f:
            data = json.load(f)

        if keywords != "fashion":
            filtered_items = [
                item for item in data['items']
                if keywords.lower() in item['title'].lower()
            ]
        else:
            filtered_items = data['items']

        return filtered_items, None
    except FileNotFoundError:
        return None, "Meesho mock data not found."
    except Exception as e:
        return None, f"An error occurred: {e}"
