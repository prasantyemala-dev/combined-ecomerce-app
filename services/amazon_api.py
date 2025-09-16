import json
import os

def search_amazon_deals(keywords="electronics"):
    """
    Connects to the Amazon API and searches for deals.
    Returns a list of items or an error string.
    """
    # In a real application, this would connect to the Amazon API.
    # For now, it reads from a mock data file.
    mock_data_path = os.path.join(os.path.dirname(__file__), '..', 'mock_data', 'amazon.json')
    try:
        with open(mock_data_path, 'r') as f:
            data = json.load(f)

        # Filter products based on keywords (simple filtering)
        if keywords != "electronics":
            filtered_items = [
                item for item in data['items']
                if keywords.lower() in item['title'].lower()
            ]
        else:
            filtered_items = data['items']

        return filtered_items, None
    except FileNotFoundError:
        return None, "Amazon mock data not found."
    except Exception as e:
        return None, f"An error occurred: {e}"
