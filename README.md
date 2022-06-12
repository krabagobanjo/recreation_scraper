# Recreation.gov Campsite Alerter
## Components
`rec_api.py` - lightweight recreation.gov API client

`campsite_watch.py` - script to handle user input, querying, and alerting
## Usage
`python campsite_watch.py` (no args) - creates config file from user input

`python campsite_watch.py -c [config_file].json` - initiate alerting based off config (intended to run in background)

`python campsite_watch.py -s` - set password for a particular sender email

`python campsite_watch.py -d [email_address]` - delete password for a particular sender email



Works best if you have some kind of system keyring. For headless Linux systems, follow this: https://github.com/jaraco/keyring#using-keyring-on-headless-linux-systems


Encrypted-file keyrings can also be used, with the interactive prompt overridden using `python campsite_watch -k [keyring-password]`

## Known Issues
- Only Gmail is supported for send address at this time
- Timed entry permits are not yet supported
