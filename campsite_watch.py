import argparse, logging, datetime, base64, os, pickle, smtplib, time, getpass
from rec_api import rec_client

sites_currently_available = {}
num_available = 0

def get_available_sites(config):
    client = rec_client()
    start_date = config.get("date_tuple")[0]
    end_date = config.get("date_tuple")[1]
    available_sites = {}
    for site_id in config.get("site_ids"):
        availability = client.get_site_availability(site_id, start_date)
        for avail in availability:
            for date_str, avail_str in avail.get("availabilities").items():
                if avail_str == "Available":
                    date_obj = datetime.datetime.strptime(date_str, client.TPARSE)
                    if date_obj <= end_date and date_obj >= start_date:
                        if available_sites.get(site_id):
                            available_sites.get(site_id).append(avail)
                        else:
                            available_sites[site_id] = [avail]
    return available_sites

def get_unavailable(sites):
    global sites_currently_available
    no_longer_available = {}
    for site_id, site_list in sites_currently_available:
        sites_to_compare = sites.get(site_id)
        for s in site_list:
            if s not in sites_to_compare:
                if not no_longer_available.get(site_id):
                    no_longer_available[site_id] = [s]
                else:
                    no_longer_available.get(site_id).append(s)
    sites_currently_available = sites
    return no_longer_available

def alert_on_available(config, sites):
    no_longer_available = get_unavailable(sites)
    if len(sites) != num_available:
        num_available = len(sites)
        email = config["email_tuple"][0]
        pwd = base64.b64decode(config["email_tuple"][1]).decode()
        FROM = "krabagobanjo@gmail.com"
        TO = [config["email_tuple"][0]]
        SUBJECT = "Open Campsites Found"
        TEXT = """Hello,
    We found the following campsites for you:

    %s

    The following sites are no longer available:

    %s

    Please book by using https://www.recreation.gov/camping/campgrounds/[site_id]

    Thanks!
    """ % (str(sites), str(no_longer_available))

        message = """From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(email, pwd)
            server.sendmail(FROM, TO, message)
            server.close()
            print('successfully sent the mail')
        except:
            print("failed to send mail")
        return

def get_site_input():
    client = rec_client()
    outer_prompt = True
    sites_to_return = []
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
                    if site_choice <= 5 or site_choice > 0:
                        sites_to_return.append(top_hits[site_choice - 1].get("entity_id"))
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
    return None

def get_date_input():
    prompt = True
    while prompt:
        start_str = input("Enter Start Date mm/dd/yyyy: (q to quit)")
        if start_str == 'q':
            return
        end_str = input("Enter End Date mm/dd/yyyy: (q to quit)")
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


def make_config():
    sites_to_search = get_site_input()
    if not sites_to_search:
        return
    dates = get_date_input()
    if not dates:
        return
    creds = get_email_input()
    data = {
        "site_ids": sites_to_search,
        "date_tuple": dates,
        "email_tuple": creds
    }
    with open("config.bin", "wb") as writefile:
        pickle.dump(data, writefile)

def make_arg_parser():
    parser = argparse.ArgumentParser(description="Watch for recreation.gov campsites")
    parser.add_argument("-c", "--config", help="Path to configuration file (run this as a background task)")
    return parser

def main():
    parser = make_arg_parser()
    args = parser.parse_args()
    if args.config:
        if os.path.isfile(args.config):
            with open(args.config, 'rb') as readfile:
                data = pickle.load(readfile)
            while True:
                sites = get_available_sites(data)
                if len(sites) > 0:
                    alert_on_available(data, sites)
                time.sleep(60*1) #Run every minute
    else:
        make_config()



if __name__ == "__main__":
    main()