from flask import Flask, render_template, request, session, jsonify, url_for
from services.amazon_api import search_amazon_deals
from services.flipkart_api import search_flipkart_deals
from services.meesho_api import search_meesho_deals
from services.ajio_api import search_ajio_deals
import re

app = Flask(__name__)
app.secret_key = 'a-very-secret-key-for-a-demo-app' # In production, use a secure, environment-variable-based key

@app.before_request
def setup_session():
    session.permanent = True
    if 'wishlist' not in session:
        session['wishlist'] = []

def parse_price(price_str):
    """Converts a price string like '₹1,24,999' to a float."""
    if not isinstance(price_str, str):
        return 0.0
    cleaned_price = re.sub(r'[₹,]', '', price_str)
    try:
        return float(cleaned_price)
    except (ValueError, TypeError):
        return 0.0

def parse_discount(discount_str):
    """Converts a discount string like '70%' to an integer."""
    if not isinstance(discount_str, str):
        return 0
    cleaned_discount = discount_str.replace('%', '').strip()
    try:
        return int(cleaned_discount)
    except (ValueError, TypeError):
        return 0

def get_biggest_discounts():
    """
    Fetches products with a discount of 60% or more from all stores.
    """
    all_items = []

    amazon_items, _ = search_amazon_deals()
    if amazon_items: all_items.extend(amazon_items)
    flipkart_items, _ = search_flipkart_deals()
    if flipkart_items: all_items.extend(flipkart_items)
    meesho_items, _ = search_meesho_deals()
    if meesho_items: all_items.extend(meesho_items)
    ajio_items, _ = search_ajio_deals()
    if ajio_items: all_items.extend(ajio_items)

    high_discount_items = [
        item for item in all_items if parse_discount(item.get('discount', '0%')) >= 60
    ]

    high_discount_items.sort(key=lambda x: parse_discount(x.get('discount', '0%')), reverse=True)

    return high_discount_items

def search_all_stores(keywords):
    """
    Searches for a product across all integrated stores and compares prices.
    """
    all_items = []
    errors = []

    # Fetch deals from all sources
    amazon_items, amazon_error = search_amazon_deals(keywords)
    if amazon_error: errors.append(f"Amazon: {amazon_error}")
    if amazon_items: all_items.extend(amazon_items)

    flipkart_items, flipkart_error = search_flipkart_deals(keywords)
    if flipkart_error: errors.append(f"Flipkart: {flipkart_error}")
    if flipkart_items: all_items.extend(flipkart_items)

    meesho_items, meesho_error = search_meesho_deals(keywords)
    if meesho_error: errors.append(f"Meesho: {meesho_error}")
    if meesho_items: all_items.extend(meesho_items)

    ajio_items, ajio_error = search_ajio_deals(keywords)
    if ajio_error: errors.append(f"Ajio: {ajio_error}")
    if ajio_items: all_items.extend(ajio_items)

    # Group items by title (simple approach for now)
    product_groups = {}
    for item in all_items:
        normalized_title = ' '.join(item['title'].split()[:4]).lower()
        if normalized_title not in product_groups:
            product_groups[normalized_title] = {
                'title': item['title'],
                'image_url': item['image_url'],
                'offers': []
            }

        product_groups[normalized_title]['offers'].append({
            'source': item['source'],
            'price': item['price'],
            'numeric_price': parse_price(item['price']),
            'url': item['url'],
            'discount': item.get('discount', 'N/A')
        })

    # Find the best price and format results
    comparison_results = []
    for _, group_data in product_groups.items():
        if not group_data['offers']:
            continue

        sorted_offers = sorted(group_data['offers'], key=lambda x: x['numeric_price'])
        lowest_offer = sorted_offers[0]

        comparison_results.append({
            'title': group_data['title'],
            'image_url': group_data['image_url'],
            'lowest_price': lowest_offer['price'],
            'best_source': lowest_offer['source'],
            'buy_url': lowest_offer['url'],
            'all_offers': sorted_offers
        })

    comparison_results.sort(key=lambda x: parse_price(x['lowest_price']))
    error_message = "; ".join(errors) if errors else None

    return comparison_results, error_message

@app.route('/', methods=['GET', 'POST'])
def home():
    search_results = []
    error = None
    keywords = ""

    if request.method == 'POST':
        keywords = request.form.get('keywords', '')
        if keywords:
            search_results, error = search_all_stores(keywords)

    # Always fetch biggest discounts for the homepage
    biggest_deals = get_biggest_discounts()

    return render_template('index.html',
                           items=search_results,
                           deals=biggest_deals,
                           error=error,
                           keywords=keywords)

def get_deals_by_category(category='all'):
    """
    Fetches high-discount products, optionally filtered by a category.
    """
    all_high_discount_items = get_biggest_discounts()

    if category == 'all':
        return all_high_discount_items

    category_keywords = {
        'mobiles': ['mobile', 'smartphone'],
        'fashion': ['shirt', 'jacket', 'kurti', 'shoes'],
        'electronics': ['headphone', 'laptop', 'camera', 'earbuds'],
    }

    keywords_to_check = category_keywords.get(category, [])
    category_items = [
        item for item in all_high_discount_items
        if any(keyword in item['title'].lower() for keyword in keywords_to_check)
    ]

    return category_items

@app.route('/deals')
def deals_page():
    selected_category = request.args.get('category', 'all')
    categories = ['all', 'mobiles', 'fashion', 'electronics']
    deals = get_deals_by_category(selected_category)

    return render_template('deals.html',
                           deals=deals,
                           categories=categories,
                           selected_category=selected_category)

@app.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    product = request.get_json()
    if not product or 'url' not in product:
        return jsonify({'success': False, 'message': 'Invalid product data.'})

    if not any(p['url'] == product['url'] for p in session['wishlist']):
        session['wishlist'].append(product)
        session.modified = True

    return jsonify({'success': True, 'wishlist_count': len(session['wishlist'])})

@app.route('/wishlist/remove', methods=['POST'])
def remove_from_wishlist():
    product = request.get_json()
    if not product or 'url' not in product:
        return jsonify({'success': False, 'message': 'Invalid product data.'})

    session['wishlist'] = [p for p in session['wishlist'] if p.get('url') != product['url']]
    session.modified = True
    return jsonify({'success': True, 'wishlist_count': len(session['wishlist'])})

@app.route('/wishlist')
def wishlist_page():
    return render_template('wishlist.html', wishlist_items=session.get('wishlist', []))


if __name__ == '__main__':
    # Use a production-ready WSGI server in a real environment
    app.run(debug=True, host='0.0.0.0', port=8080)
