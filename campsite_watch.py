import argparse
import base64
import datetime
import getpass
import logging
import logging.config
import os
import pickle
import smtplib
import sys
import time

from collections import namedtuple

from rec_api import RecClient

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

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

def get_available_sites(config):
    client = RecClient()
    start_date = config.get("date_tuple")[0]
    end_date = config.get("date_tuple")[1]
    available_sites = {}
    for site_id in config.get("site_id_name_map").keys():
        availability = client.get_site_availability(site_id, start_date)
        for avail in availability:
            for date_str, avail_str in avail.get("availabilities").items():
                if avail_str == "Available":
                    date_obj = datetime.datetime.strptime(date_str, client.TPARSE)
                    if start_date <= date_obj <= end_date:
                        site_info = {
                            "campsite_id": avail.get("campsite_id"),
                            "site": avail.get("site"),
                            "loop": avail.get("loop"),
                            "campsite_type": avail.get("campsite_type")
                        }
                        if available_sites.get(site_id):
                            available_sites.get(site_id).append(site_info)
                        else:
                            available_sites[site_id] = [site_info]
    return available_sites

def alert_on_available(config, curr, prev):

    email = config["email_tuple"][0]
    pwd = base64.b64decode(config["email_tuple"][1]).decode()
    fromaddr = email
    toaddr = config["dest_list"]
    subject = "Rec.gov Open Campsites Found"

    url_base = "https://www.recreation.gov/camping/campgrounds/"

    avail = []
    navail = []
    for ground_id, avail_list in curr.items():
        curr_set = {namedtuple("avail", d.keys())(*d.values()) for d in avail_list}
        prev_set = {namedtuple("avail", d.keys())(*d.values()) for d in prev.get("ground_id")} if prev.get("ground_id") else set()
        no_longer_available = prev_set.difference(curr_set)
        url = url_base + ground_id
        header_str = "{}\n{}\n\n".format(config.get("site_id_name_map").get(ground_id), url)
        avail_body = header_str
        navail_body = header_str
        if curr_set:
            for availitem in curr_set:
                avail_body += "site num: {}\nsite loop: {}\nsite type: {}\n".format(availitem.site, availitem.loop, availitem.campsite_type)
        else:
            avail_body += "(None Available)\n"
        if no_longer_available:
            for navailitem in no_longer_available:
                navail_body += "site num: {}\nsite loop: {}\nsite type: {}\n".format(navailitem.site, navailitem.loop, navailitem.campsite_type)
        else:
            navail_body += "(None no longer available)\n"
        avail.append(avail_body)
        navail.append(navail_body)


    msg = """Hello,
We found the following campsites for you:

{}

The following sites are no longer available:

{}

Thanks!
""".format(
    "\n".join(avail),
    "\n".join(navail)
)

    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (fromaddr, toaddr, subject, msg)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(email, pwd)
        server.sendmail(fromaddr, toaddr, message)
        server.close()
        logging.debug("Email Sent!")
    except:
        logging.error("Could not send email", exc_info=True)
    return

def get_site_input():
    client = RecClient()
    outer_prompt = True
    sites_to_return = {}
    while outer_prompt:
        site_name = input("What campsite do you want to book? ")
        site_list = client.search_campsites(site_name)
        if not site_list:
            print("No results found :-(")
            continue
        top_hits = site_list[0:10]
        for i in range(10):
            site = top_hits[i]
            print("(%s) " % (str(i+1)) + site.get("name"))
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
                        sites_to_return[top_hits[site_choice - 1].get("entity_id")] = top_hits[site_choice - 1].get("name")
                        reprompt = True
                        while reprompt:
                            another = input("Add more? (y/n) ")
                            another = another.lower()
                            if another == 'y':
                                inner_prompt = False
                                break
                            elif another == 'n':
                                outer_prompt = False
                                inner_prompt = False
                                return sites_to_return
                            else:
                                print("Invalid option")
                    else:
                        print("Invalid Input")
                        continue
                except:
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
        except:
            print("Invalid Input")
    return (start_date, end_date)

def get_email_input():
    gmail = input("Enter gmail address: ")
    pword = getpass.getpass("Enter gmail password: ")
    pword = base64.b64encode(str.encode(pword))
    return (gmail, pword)

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
    creds = get_email_input()
    data = {
        "site_id_name_map": sites_to_search,
        "date_tuple": dates,
        "email_tuple": creds,
        "dest_list": destemail
    }
    with open("config.bin", "wb") as writefile:
        pickle.dump(data, writefile)

def make_arg_parser():
    parser = argparse.ArgumentParser(description="Watch for recreation.gov campsites")
    parser.add_argument(
        "-c",
        "--config",
        help="Path to configuration file (run this as a background task)"
    )
    return parser

def main():
    parser = make_arg_parser()
    args = parser.parse_args()
    if args.config:
        if os.path.isfile(args.config):
            with open(args.config, 'rb') as readfile:
                data = pickle.load(readfile)
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
    else:
        make_config()



if __name__ == "__main__":
    main()
