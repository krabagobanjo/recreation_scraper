from datetime import datetime
import json
import os
import pytest
import requests_mock

from rec_api import RecClient

TEST_SITE_ID = "20001"

@pytest.fixture
def mock_client() -> RecClient:
    return RecClient()

def test_client_can_instatiate(mock_client: RecClient):
    assert mock_client is not None

def test_can_get_site_availability(mock_client: RecClient):
    with open(os.path.join("api_data", "site_availability_response.json")) as availfile:
        avail_json = json.load(availfile)
    with requests_mock.Mocker(session=mock_client.session) as session_mock:
        session_mock.register_uri("GET",
        f"/api/camps/availability/campground/{TEST_SITE_ID}/month?start_date=2022-05-01T00%3A00%3A00.000Z",
        json=avail_json,
        status_code=200
    )
        availability = mock_client.get_site_availability(TEST_SITE_ID,
            datetime.strptime("05/03/2022", "%m/%d/%Y"))
    assert availability is not None
    assert len(availability) > 0

def test_can_search_sites(mock_client: RecClient):
    pass
