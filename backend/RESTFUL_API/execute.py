from ApartmentManager.backend.config.server_config import HOST, PORT
import requests

def make_restful_api_query(path: str) -> dict:
    """
    Executes a query from AI to an endpoint RESTFUL API and returns the response.
    :param path: Path to the endpoint RESTFUL API.
    :param filters: Filters to use when executing queries.
    :return: JSON response from the endpoint RESTFUL API.
    """
    try:
        if not path:
            raise ValueError("No path provided")

        url = f"http://{HOST}:{PORT}{path}"

        # get response from the endpoint of RESTful API
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # raises an HTTPError if the server responds with a failed status code.
        return response.json()

    except requests.ConnectionError as error:
        print("Error connecting to the REST API: Flask server is not running.", error)
    except requests.HTTPError as error:
        print(f"Error due returning HTTP error: {error}")
    except ValueError as error:
        print(f"Error due faulty value: {error}")
    except Exception as error:
        print(f"Unexpected error calling endpoints by AI: {error}")
    return None