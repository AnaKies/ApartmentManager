import sys
import os
from unittest.mock import patch

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ApartmentManager.backend.RESTFUL_API.execute import make_restful_api_get, make_restful_api_post
from ApartmentManager.backend.config.server_config import HOST, PORT

def test_url_construction():
    print("Testing URL construction...")
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {}
        mock_get.return_value.raise_for_status.return_value = None
        
        path = "/apartments"
        make_restful_api_get(path)
        
        expected_url = f"http://{HOST}:{PORT}/internal{path}"
        mock_get.assert_called_with(expected_url, timeout=10)
        print(f"GET {path} -> {expected_url} : PASS")

    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = {}
        
        path = "/persons"
        payload = {"name": "Test"}
        make_restful_api_post(path, payload)
        
        expected_url = f"http://{HOST}:{PORT}/internal{path}"
        mock_post.assert_called_with(url=expected_url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        print(f"POST {path} -> {expected_url} : PASS")

if __name__ == "__main__":
    try:
        test_url_construction()
        print("All tests passed.")
    except Exception as e:
        print(f"Test failed: {e}")
