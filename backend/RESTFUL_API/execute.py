from ApartmentManager.backend.AI_API.general.error_texts import ErrorCode, APIError
from ApartmentManager.backend.AI_API.general.logger import log_error
from ApartmentManager.backend.config.server_config import HOST, PORT
import requests
from requests.exceptions import RequestException

def make_restful_api_post(path: str, payload: dict) -> requests.Response:
    """
    Executes a POST query from AI to an endpoint RESTFUL API and returns the status response.
    The data to POST are sent in the request JSON-Body.
    :param payload: Data to add, which are sent in the body of the request.
    :param path: Path to the endpoint RESTFUL API.
    :return: Status JSON response from the endpoint RESTFUL API.
    """
    try:
        if not path:
            raise ValueError("No path provided")

        url = f"http://{HOST}:{PORT}{path}"

        response = requests.post(
            url=url,
            json=payload,  # data to add in the table are sent as JSON-Body
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return response.json()

    except requests.ConnectionError:
        raise
    except requests.HTTPError:
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_DOING_POST_QUERY_TO_AN_ENDPOINT, exception=error)
        raise APIError(ErrorCode.ERROR_DOING_POST_QUERY_TO_AN_ENDPOINT, trace_id) from error



def make_restful_api_get(path: str) -> dict | None:
    """
    Executes a GET query from AI to an endpoint RESTFUL API and returns the response.
    :param path: Path to the endpoint RESTFUL API.
    :return: Data JSON response from the endpoint RESTFUL API.
    """
    try:
        url = f"http://{HOST}:{PORT}{path}"

        # get response from the endpoint of RESTful API
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # raises an HTTPError if the server responds with a failed status code.
        return response.json()

    except RequestException:
        # every HTTP error requests: ConnectionError, Timeout, HTTPError, ...
        raise
    except Exception as error:
        trace_id = log_error(ErrorCode.ERROR_DOING_GET_QUERY_TO_AN_ENDPOINT, exception=error)
        raise APIError(ErrorCode.ERROR_DOING_GET_QUERY_TO_AN_ENDPOINT, trace_id) from error