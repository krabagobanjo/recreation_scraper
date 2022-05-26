import argparse
import datetime
import getpass
import json
import logging
import logging.config
import os
import smtplib
import sys
import time
import keyring

from keyrings.cryptfile.cryptfile import CryptFileKeyring

from rec_api import RecClient

# TODO - log to an actual log file
# This config just sends to stdout
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

# This ensures an unhandled exception is logged
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class SiteInfo:
    def __init__(self):
        self.site_id = None
        self.site = None
        self.loop = None
        self.site_type = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SiteInfo):
            return self.site_id == other.site_id
        return False

    def __key(self):
        return tuple(self.site_id)

    def __hash__(self):
        return hash(self.__key())

def get_available_sites(config: dict) -> dict:
    # available_sites_schema = {
    #     "ground_id" : {
    #         "date_available" : [
    #                 SiteInfo()
    #         ]
    #     }
    # }

    client = RecClient()
    start_date_str = config.get("dates")[0]
    end_date_str = config.get("dates")[1]
    start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y")
    end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%Y")
    available_sites = {}
    for site_id in config.get("site_id_name_map").keys():
        availability = client.get_site_availability(site_id, start_date)
        for avail in availability:
            for date_str, avail_str in avail.get("availabilities").items():
                if avail_str == "Available":
                    date_obj = datetime.datetime.strptime(date_str, client.TPARSE)
                    if start_date <= date_obj < end_date:
                        site_info = SiteInfo()
                        site_info.site_id = avail.get("site_id")
                        site_info.site = avail.get("site")
                        site_info.loop = avail.get("loop")
                        site_info.site_type = avail.get("site_type")
                        if available_sites.get(site_id):
                            available_sites.get(site_id).append(site_info)
                        else:
                            available_sites[site_id] = [site_info]
    return available_sites

def alert_on_available(config: dict, curr: dict, prev: dict):
    email = config["send_email"]
    pwd = keyring.get_password("gmail", email)
    fromaddr = email
    toaddr = config["dest_list"]
    subject = "Rec.gov Open sites Found"

    url_base = "https://www.recreation.gov/camping/campgrounds/"

    avail = []
    navail = []
    for ground_id, avail_list in curr.items():
        curr_set = set(avail_list)
        prev_set = set(prev.get("ground_id", []))
        no_longer_available = prev_set.difference(curr_set)
        url = url_base + ground_id
        header_str = f"{config.get('site_id_name_map').get(ground_id)}\n{url}\n\n"
        avail_body = header_str
        navail_body = header_str
        if curr_set:
            for availitem in curr_set:
                avail_body += f"site num: {availitem.site}\nsite loop: {availitem.loop}\nsite type: {availitem.site_type}\n"
        else:
            avail_body += "(None Available)\n"
        if no_longer_available:
            for navailitem in no_longer_available:
                navail_body += f"site num: {navailitem.site}\nsite loop: {navailitem.loop}\nsite type: {navailitem.site_type}\n"
        else:
            navail_body += "(None no longer available)\n"
        avail.append(avail_body)
        navail.append(navail_body)


    msg = """Hello,
We found the following sites for you:

{}

The following sites are no longer available:

{}

Thanks!
""".format(
    "\n".join(avail),
    "\n".join(navail)
)

    message = f"From: {fromaddr}\nTo: {toaddr}\nSubject: {subject}\n\n{msg}"
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(email, pwd)
        server.sendmail(fromaddr, toaddr, message)
        server.close()
        logging.debug("Email Sent!")
    except: #pylint:disable=bare-except
        logging.error("Could not send email", exc_info=True)

def get_site_input():
    client = RecClient()
    outer_prompt = True
    sites_to_return = {}
    while outer_prompt:
        site_name = input("What site do you want to book? ")
        site_list = client.search_sites(site_name)
        if not site_list:
            print("No results found :-(")
            continue
        top_hits = site_list[0:10]
        for i in range(10):
            site = top_hits[i]
            print(f"{str(i+1)}{site.get('name')}")
            print(site.get("description"))
            print(site.get("addresses"))
            print("\n")
        inner_prompt = True
        while inner_prompt:
            site_choice = input("Which one do you want? (r to try again, q to quit) ")
            if site_choice == 'r':
                break
            elif site_choice == 'q':
                outer_prompt = False
                break
            else:
                try:
                    site_choice = int(site_choice)
                    if 0 < site_choice <= 10:
                        sites_to_return[top_hits[site_choice - 1].get("entity_id")] = \
                            top_hits[site_choice - 1].get("name")
                        reprompt = True
                        while reprompt:
                            another = input("Add more? (y/n) ")
                            another = another.lower()
                            if another == 'y':
                                inner_prompt = False
                                break
                            if another == 'n':
                                outer_prompt = False
                                inner_prompt = False
                                return sites_to_return
                            print("Invalid option")
                    else:
                        print("Invalid Input")
                        continue
                except: #pylint:disable=bare-except
                    print("Invalid Input")
                    continue

def get_date_input():
    prompt = True
    while prompt:
        start_str = input("Enter Start Date mm/dd/yyyy: (q to quit) ")
        if start_str == 'q':
            return
        end_str = input("Enter End Date mm/dd/yyyy: (q to quit) ")
        if end_str == 'q':
            return
        try:
            start_date = datetime.datetime.strptime(start_str, "%m/%d/%Y")
            end_date = datetime.datetime.strptime(end_str, "%m/%d/%Y")
            prompt = False
        except: #pylint:disable=bare-except
            print("Invalid Input")
    return (start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y"))

def get_email_input():
    gmail = input("Enter gmail address (for sending alerts): ")
    stored_credential = keyring.get_password("gmail", gmail)
    if stored_credential:
        print("Credentials already saved")
        return gmail
    pword = getpass.getpass("Enter gmail password: ")
    keyring.set_password("gmail", gmail, pword)
    return gmail

def get_destination():
    destemail = input("Enter destination emails (comma separated): ")
    return str(destemail).split(",")

def make_config():
    sites_to_search = get_site_input()
    if not sites_to_search:
        print("No sites to search. Exiting...")
        return
    dates = get_date_input()
    if not dates:
        print("No dates to search. Exiting...")
    destemail = get_destination()
    if not destemail:
        print("No destination emails. Exiting...")
        return
    send_email = get_email_input()
    data = {
        "site_id_name_map": sites_to_search,
        "dates": dates,
        "send_email": send_email,
        "dest_list": destemail
    }
    with open("config.json", "w", encoding="utf-8") as writefile:
        json.dump(data, writefile)

def make_arg_parser():
    parser = argparse.ArgumentParser(description="Watch for recreation.gov sites")
    parser.add_argument(
        "-c",
        "--config",
        help="Path to configuration file (run this as a background task)"
    )
    parser.add_argument(
        "-s",
        "--set-password",
        action="store_true",
        help="Set credentials for gmail account"
    )
    parser.add_argument(
        "-d",
        "--delete-password",
        help="Delete password for gmail account (requires the correct gmail account)"
    )
    parser.add_argument(
        "-k",
        "--keyring-password",
        help="Supply a keyring password (for systems using cryptfile backend)"
    )
    return parser

def main():
    parser = make_arg_parser()
    args = parser.parse_args()
    if args.keyring_password:
        ring = CryptFileKeyring()
        ring.keyring_key = args.keyring_password
        keyring.set_keyring(ring)
    if args.config:
        if os.path.isfile(args.config):
            with open(args.config, 'r', encoding="utf-8") as readfile:
                data = json.load(readfile)
            # keyring.get_password("gmail", data.get("send_email")) # Unlock keyring
            curr = {}
            while True:
                logging.info("Getting sites...")
                prev = curr
                curr = get_available_sites(data)
                for ground_id, avail_list in curr.items():
                    if prev.get(ground_id) != avail_list:
                        logging.info("Found open sites! Alerting...")
                        alert_on_available(data, curr, prev)
                        break
                time.sleep(60*1) #Run every minute
    elif args.set_password:
        get_email_input()
    elif args.delete_password:
        stored_credential = keyring.get_password("gmail", args.delete_password)
        if stored_credential:
            keyring.delete_password("gmail", args.delete_password)
    else:
        make_config()



if __name__ == "__main__":
    main()
