import argparse, logging, datetime, base64, os, pickle
from rec_api import rec_client

def scrape_and_notify(config):
    client = rec_client()
    site_id = 0
    start_date = datetime.datetime.now()
    availability = client.get_site_availability(site_id, start_date)
    #TODO - parse availability
    #TODO - send email on hit

def get_user_input():
    client = rec_client()
    site_name = input("What campsite do you want to book? ")
    site_list = client.search_campsites(site_name)
    #TODO - print list of top 5 hits, r to try again
    site_choice = input("Which one do you want? (r to try again, q to quit) ")
    if int()

def make_arg_parser():
    parser = argparse.ArgumentParser(description="Watch for recreation.gov campsites")
    parser.add_argument("-c", "--config", help="Path to configuration file")
    return parser

def main():
    parser = make_arg_parser()
    args = parser.parse_args()
    if args.config:
        if os.path.isfile(args.config):
            with open(args.config) as readfile:
                config = pickle.load(readfile)
            
    


if __name__ == "__main__":
    main()