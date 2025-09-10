import pytest
from unittest.mock import MagicMock, patch
from app import app, search_amazon_deals

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    with app.test_client() as client:
        yield client

# Mock data for a successful API response
mock_api_response = {
    'data': [
        MagicMock(
            item_info=MagicMock(title=MagicMock(display_value='Test Product')),
            detail_page_url='http://example.com/product',
            images=MagicMock(primary=MagicMock(large=MagicMock(url='http://example.com/image.jpg'))),
            offers=MagicMock(
                listings=[
                    MagicMock(
                        price=MagicMock(display_amount='$10.00'),
                        saving_basis=MagicMock(
                            display_amount='$5.00',
                            percentage=50
                        )
                    )
                ]
            )
        )
    ],
    'errors': None
}

def test_search_amazon_deals_success():
    """
    Test the search_amazon_deals function for a successful API call.
    """
    with patch('app.AmazonAPI') as mock_amazon_api:
        # Configure the mock to return the mock response
        mock_api_instance = mock_amazon_api.return_value
        mock_api_instance.search_items.return_value = mock_api_response

        items, error = search_amazon_deals("test")

        # Assertions
        assert error is None
        assert len(items) == 1
        assert items[0]['title'] == 'Test Product'
        assert items[0]['price'] == '$10.00'
        assert items[0]['savings_percent'] == 50
        mock_api_instance.search_items.assert_called_once_with(
            keywords="test",
            search_index='All',
            item_count=10,
            sort_by='Price:LowToHigh',
            min_saving_percent=60
        )

# Mock data for an API error response
mock_api_error_response = {
    'data': None,
    'errors': [{'message': 'Invalid API key'}]
}

def test_search_amazon_deals_api_error():
    """
    Test the search_amazon_deals function for an API error.
    """
    with patch('app.AmazonAPI') as mock_amazon_api:
        mock_api_instance = mock_amazon_api.return_value
        mock_api_instance.search_items.return_value = mock_api_error_response

        items, error = search_amazon_deals("test")

        assert items is None
        assert "API Error: Invalid API key" in error

def test_search_amazon_deals_no_results():
    """
    Test the search_amazon_deals function for a case with no results.
    """
    with patch('app.AmazonAPI') as mock_amazon_api:
        mock_api_instance = mock_amazon_api.return_value
        mock_api_instance.search_items.return_value = {'data': None, 'errors': None}

        items, error = search_amazon_deals("test")

        assert items is None
        assert "No deals found matching the criteria" in error

def test_search_amazon_deals_exception():
    """
    Test the search_amazon_deals function for an unexpected exception.
    """
    with patch('app.AmazonAPI') as mock_amazon_api:
        mock_api_instance = mock_amazon_api.return_value
        mock_api_instance.search_items.side_effect = Exception("Something went wrong")

        items, error = search_amazon_deals("test")

        assert items is None
        assert "An unexpected error occurred: Something went wrong" in error

def test_home_get(client):
    """
    Test the home route with a GET request.
    """
    with patch('app.search_amazon_deals') as mock_search:
        mock_search.return_value = ([], None)  # No items, no error
        response = client.get('/')
        assert response.status_code == 200
        assert b"E-commerce Deal Finder" in response.data
        mock_search.assert_called_once_with("electronics")

def test_home_post(client):
    """
    Test the home route with a POST request.
    """
    with patch('app.search_amazon_deals') as mock_search:
        mock_search.return_value = ([], None)
        response = client.post('/', data={'keywords': 'books'})
        assert response.status_code == 200
        assert b"E-commerce Deal Finder" in response.data
        mock_search.assert_called_once_with("books")
