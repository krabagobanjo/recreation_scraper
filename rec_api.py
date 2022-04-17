import datetime
import logging
from typing import List
import requests

class RecClient:

    TPARSE = "%Y-%m-%dT00:00:00Z"

    def __init__(self):
        self.api_base = "https://www.recreation.gov/api/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
            'Host': 'www.recreation.gov',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        })

    def _get_json(self, endpoint: str, params: dict):
        try:
            req = self.session.get(self.api_base + endpoint, params=params)
            req.raise_for_status()
            return req.json()
        except requests.exceptions.HTTPError as hterror:
            logging.error(hterror, exc_info=True)

    def search_campsites(self, name: str) -> List[dict]:
        """
        Search for campgrounds
        Arguments:
            name (str) - name of campground
        Returns:
            (list) - campground results
        """
        endpoint = "search"
        params = {
            'q': name,
            'entity_type': 'recarea',
            'exact': False,
            'size': 20,
            'fq': "-entity_type:(tour OR timedentry_tour)",
            'start': 0
        }
        return self._get_json(endpoint, params).get("results")

    def get_site_availability(self, siteid: str, start_date: datetime) -> List[dict]:
        """
        Return a month of availabilities from a given start date
        Arguments:
            siteid (str) - entity_id of campground
            start_date (datetime) - start date from which to search (months)
        Returns:
            (list) - monthly availability for each site in campground
        """
        url = f"camps/availability/campground/{siteid}/month"
        #Must be first of any month
        date_string = start_date.strftime("%Y-%m-01T00:00:00.000Z")
        params = {
            'start_date': date_string
        }
        #Useful data: site, loop, campsite_reserve_type, max_num_people, availabilities
        return self._get_json(url, params).get("campsites").values()

    def get_timed_entry_tickets(self, facility_id: str) -> List[dict]:
        url = f"api/timedentrycontent/facility/{facility_id}/"
        params = {
            "includeFieldSalesOnly": False,
            "filterCommTours": True
        }
        return self._get_json(url, params)

    def get_timed_entry_availability_summary(self, facility_id: str, tour_id: str,
            start_date: datetime.datetime) -> List[dict]:
        url = f"api/timedentry/availability/facility/{facility_id}"
        params = {
            "year": start_date.year,
            "month": start_date.month,
            "inventoryBucket": "FIT",
            "tourID": tour_id
        }
        return self._get_json(url, params)



def main():
    # Examples
    test_api = RecClient()
    sites = test_api.search_campsites("pinnacles national park")
    for i in range(1):
        site = sites[i]
        print("(%s) " % (str(i+1)) + site.get("name"))
        print(site.get("description"))
        print(site.get("addresses"))
        print("\n")
    # print(sites[0].get("name"))
    # print(sites[0].get("description"))
    # print(sites[0].get("addresses"))
    print(sites[0].get("entity_id"))
    availability = test_api.get_site_availability(sites[0].get("entity_id"), datetime.date(year=2020, month=9, day=20))
    for item in availability:
        print(item)
        break

if __name__ == "__main__":
    main()
