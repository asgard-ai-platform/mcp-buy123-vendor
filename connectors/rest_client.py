"""REST API connector with retry, pagination, and rate limiting."""

import time
import requests
from config.settings import get_headers, get_url, DEFAULT_PER_PAGE


class ServiceAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, message: str, endpoint: str = ""):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"[{status_code}] {endpoint}: {message}")


def api_request(
    method: str,
    endpoint_key: str,
    params: dict | None = None,
    json_body: dict | None = None,
    path_params: dict | None = None,
    retries: int = 3,
    timeout: int = 60,
    require_auth: bool = True,
) -> dict:
    """Make an HTTP request with exponential backoff retry.

    On 401 responses, invalidates the cached access token, refreshes (or re-logs
    in), and retries the request once before giving up.
    """
    url = get_url(endpoint_key, **(path_params or {}))

    auth_retry_used = False

    for attempt in range(retries):
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=get_headers(require_auth=require_auth),
                params=params,
                json=json_body,
                timeout=timeout,
            )

            if response.status_code == 401 and require_auth and not auth_retry_used:
                # Token expired / invalid — refresh or re-login and retry once.
                from auth.vendor_login import invalidate_access_token

                invalidate_access_token()
                auth_retry_used = True
                continue

            if response.status_code >= 400:
                raise ServiceAPIError(
                    status_code=response.status_code,
                    message=response.text[:500],
                    endpoint=endpoint_key,
                )

            return response.json()

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < retries - 1:
                wait = 2**attempt
                time.sleep(wait)
            else:
                raise ServiceAPIError(
                    status_code=0,
                    message="Request failed after all retries (timeout/connection error)",
                    endpoint=endpoint_key,
                )


def api_get(
    endpoint_key: str,
    params: dict | None = None,
    path_params: dict | None = None,
    retries: int = 3,
    require_auth: bool = True,
) -> dict:
    """Convenience wrapper for GET requests."""
    return api_request(
        "GET",
        endpoint_key,
        params=params,
        path_params=path_params,
        retries=retries,
        require_auth=require_auth,
    )


def api_post(
    endpoint_key: str,
    json_body: dict | None = None,
    params: dict | None = None,
    path_params: dict | None = None,
    require_auth: bool = True,
) -> dict:
    """Convenience wrapper for POST requests."""
    return api_request(
        "POST",
        endpoint_key,
        params=params,
        json_body=json_body,
        path_params=path_params,
        require_auth=require_auth,
    )


def api_put(
    endpoint_key: str,
    json_body: dict | None = None,
    params: dict | None = None,
    path_params: dict | None = None,
    require_auth: bool = True,
) -> dict:
    """Convenience wrapper for PUT requests."""
    return api_request(
        "PUT",
        endpoint_key,
        params=params,
        json_body=json_body,
        path_params=path_params,
        require_auth=require_auth,
    )


def api_delete(
    endpoint_key: str,
    params: dict | None = None,
    path_params: dict | None = None,
    require_auth: bool = True,
) -> dict:
    """Convenience wrapper for DELETE requests."""
    return api_request(
        "DELETE",
        endpoint_key,
        params=params,
        path_params=path_params,
        require_auth=require_auth,
    )


def fetch_all_pages(
    endpoint_key: str,
    params: dict | None = None,
    path_params: dict | None = None,
    max_pages: int = 100,
    items_key: str = "items",
    rate_limit_delay: float = 0.2,
) -> list:
    """Fetch all pages of a paginated endpoint (page-based).

    Args:
        endpoint_key: Key from ENDPOINTS dict.
        params: Base query parameters.
        path_params: Path parameters for URL substitution.
        max_pages: Maximum number of pages to fetch.
        items_key: Key in response JSON that contains the item list.
        rate_limit_delay: Seconds to wait between page requests.

    Returns:
        Combined list of all items across pages.
    """
    all_items = []
    params = dict(params or {})
    params.setdefault("per_page", DEFAULT_PER_PAGE)

    for page in range(1, max_pages + 1):
        params["page"] = page
        data = api_get(endpoint_key, params=params, path_params=path_params)

        items = data.get(items_key, [])
        if not items:
            break

        all_items.extend(items)

        if len(items) < params["per_page"]:
            break

        if page < max_pages:
            time.sleep(rate_limit_delay)

    return all_items


def fetch_all_pages_cursor(
    endpoint_key: str,
    params: dict | None = None,
    path_params: dict | None = None,
    max_pages: int = 100,
    items_key: str = "items",
    cursor_key: str = "next_cursor",
    cursor_param: str = "cursor",
    rate_limit_delay: float = 0.2,
) -> list:
    """Fetch all pages of a cursor-based paginated endpoint.

    Args:
        endpoint_key: Key from ENDPOINTS dict.
        params: Base query parameters.
        path_params: Path parameters for URL substitution.
        max_pages: Maximum number of pages to fetch.
        items_key: Key in response JSON that contains the item list.
        cursor_key: Key in response JSON that contains the next cursor.
        cursor_param: Query parameter name for the cursor.
        rate_limit_delay: Seconds to wait between page requests.

    Returns:
        Combined list of all items across pages.
    """
    all_items = []
    params = dict(params or {})
    params.setdefault("per_page", DEFAULT_PER_PAGE)

    for _ in range(max_pages):
        data = api_get(endpoint_key, params=params, path_params=path_params)

        items = data.get(items_key, [])
        all_items.extend(items)

        next_cursor = data.get(cursor_key)
        if not next_cursor or not items:
            break

        params[cursor_param] = next_cursor
        time.sleep(rate_limit_delay)

    return all_items


def fetch_all_pages_by_date_segments(
    endpoint_key: str,
    start_date: str,
    end_date: str,
    params: dict | None = None,
    path_params: dict | None = None,
    items_key: str = "items",
    date_start_param: str = "created_after",
    date_end_param: str = "created_before",
    segment_days: int = 30,
) -> list:
    """Fetch large datasets by breaking into date segments.

    Useful when APIs have result count limits (e.g., 10,000 max).

    Args:
        endpoint_key: Key from ENDPOINTS dict.
        start_date: Start date (ISO format YYYY-MM-DD).
        end_date: End date (ISO format YYYY-MM-DD).
        params: Additional query parameters.
        path_params: Path parameters for URL substitution.
        items_key: Key in response JSON that contains the item list.
        date_start_param: Query parameter name for start date.
        date_end_param: Query parameter name for end date.
        segment_days: Number of days per segment.

    Returns:
        Combined list of all items across date segments.
    """
    from datetime import datetime, timedelta

    all_items = []
    params = dict(params or {})

    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current < end:
        segment_end = min(current + timedelta(days=segment_days), end)

        params[date_start_param] = current.strftime("%Y-%m-%d")
        params[date_end_param] = segment_end.strftime("%Y-%m-%d")

        items = fetch_all_pages(
            endpoint_key, params=params, path_params=path_params, items_key=items_key
        )
        all_items.extend(items)

        current = segment_end

    return all_items
