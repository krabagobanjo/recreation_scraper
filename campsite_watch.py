import argparse, logging, datetime, base64, os, pickle, smtplib, time
from rec_api import rec_client

def get_available_sites(config):
    client = rec_client()
    site_id = 0
    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now()
    availability = client.get_site_availability(site_id, start_date)
    available_sites = []
    for avail in availability:
        for date_str, avail_str in avail.get("availabilities").items():
            if avail_str == "Available":
                date_obj = datetime.datetime.strptime(date_str, client.TPARSE)
                if date_obj <= end_date and date_obj >= start_date:
                    available_sites.append(avail)
    return available_sites

def alert_on_available(config, sites):
    email = config["email_tuple"][0]
    pwd = base64.b64decode(config["email_tuple"][1]).decode()
    FROM = "krabagobanjo@gmail.com"
    TO = [config["email_tuple"][0]]
    SUBJECT = "Open Campsites Found"
    TEXT = """Hello,
We found the following campsites for you:

%s

Please book on the recreation.gov website.

Thanks!
""" % (str(sites))

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
    while outer_prompt:
        site_name = input("What campsite do you want to book? ")
        site_list = client.search_campsites(site_name)
        top_hits = site_list[0:5]
        for i in range(5):
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
                        outer_prompt = False
                        inner_prompt = False
                        #get dates
                        return top_hits[site_choice - 1].get("entity_id")
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
    pword = input("Enter gmail password: ")
    pword = base64.b64encode(str.encode(pword))
    return (gmail, pword)


def make_config():
    site_to_search = get_site_input()
    if not site_to_search:
        return
    dates = get_date_input()
    if not dates:
        return
    creds = get_email_input()
    data = {
        "site_id": site_to_search,
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
            with open(args.config) as readfile:
                data = pickle.load(readfile)
            while True:
                sites = get_available_sites(data)
                if len(sites) > 0:
                    alert_on_available(data, sites)
                time.sleep(60*5) #Run every 5 mins
    else:
        make_config()



if __name__ == "__main__":
    main()