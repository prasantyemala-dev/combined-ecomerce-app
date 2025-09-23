from flask import Flask, render_template, request
import config
from amazon.paapi import AmazonAPI

app = Flask(__name__)

def search_amazon_deals(keywords="electronics", min_saving_percent=60):
    """
    Connects to the Amazon API and searches for deals.
    Returns a list of items or an error string.
    """
    try:
        amazon = AmazonAPI(
            config.AMAZON_ACCESS_KEY,
            config.AMAZON_SECRET_KEY,
            config.AMAZON_PARTNER_TAG,
            'US'
        )

        search_result = amazon.search_items(
            keywords=keywords,
            search_index='All',
            item_count=10,
            sort_by='Price:LowToHigh',
            min_saving_percent=min_saving_percent
        )

        if search_result and search_result['data']:
            items_list = []
            for item in search_result['data']:
                item_data = {
                    "title": item.item_info.title.display_value,
                    "url": item.detail_page_url,
                    "image_url": item.images.primary.large.url if item.images and item.images.primary else "",
                    "price": "N/A",
                    "savings": "N/A",
                    "savings_percent": "N/A"
                }
                if item.offers and item.offers.listings:
                    item_data["price"] = item.offers.listings[0].price.display_amount
                    if item.offers.listings[0].saving_basis:
                        item_data["savings"] = item.offers.listings[0].saving_basis.display_amount
                        item_data["savings_percent"] = item.offers.listings[0].saving_basis.percentage

                items_list.append(item_data)
            return items_list, None
        elif search_result and search_result['errors']:
            error_message = f"API Error: {search_result['errors'][0]['message']}"
            return None, error_message
        else:
            return None, "No deals found matching the criteria."

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}. Please check your API credentials in config.py."
        return None, error_message

@app.route('/', methods=['GET', 'POST'])
def home():
    keywords = "electronics"
    min_saving_percent = 60
    if request.method == 'POST':
        keywords = request.form.get('keywords', 'electronics')
        min_saving_percent = int(request.form.get('min_saving_percent', 60))

    items, error = search_amazon_deals(keywords, min_saving_percent)

    return render_template('index.html', items=items, error=error, keywords=keywords, min_saving_percent=min_saving_percent)

if __name__ == '__main__':
    # Use a production-ready WSGI server in a real environment
    app.run(debug=True, host='0.0.0.0', port=8080)
