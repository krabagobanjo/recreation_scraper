import requests, logging, datetime

class rec_api(object):
    
    def __init__(self):
        self.API_BASE = "https://www.recreation.gov/api/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
            'Host': 'www.recreation.gov',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        })

    def _get_json(self, endpoint, params):
        try:
            req = self.session.get(self.API_BASE + endpoint, params=params)
            req.raise_for_status()
            return req.json()
        except requests.exceptions.HTTPError as hterror:
            logging.error(hterror)
        except ValueError as verror:
            logging.error(verror)

    def search_campsites(self, name):
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
            'fq': ["-entity_type:tour", "campsite_type_of_use:Overnight", "campsite_type_of_use:na", "entity_type:campground"],
            'start': 0
        }
        return self._get_json(endpoint, params).get("results")

    def get_site_availability(self, id, start_date):
        """
        Search for campgrounds
        Arguments:
            id (str) - entity_id of campground
            start_date (datetime) - start date from which to search (months)
        Returns:
            (list) - monthly availability for each site in campground
        """
        url = "camps/availability/campground/{}/month".format(id)
        date_string = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
        params = {
            'start_date': date_string
        }
        return self._get_json(url, params).get("campsites").values()



def main():
    test_api = rec_api()
    sites = test_api.search_campsites("pinnacles national park")
    print(sites[0].get("name"))
    print(sites[0].get("description"))
    print(sites[0].get("addresses"))
    print(sites[0].get("entity_id"))
    availability = test_api.get_site_availability(sites[0].get("entity_id"), "2019-03-01T00:00:00.000Z")
    print(availability[list(availability.keys())[0]])

if __name__ == "__main__":
    main()
