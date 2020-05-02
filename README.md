# Recreation.gov Campsite Alerter
## Components
`rec_api.py` - lightweight recreation.gov API client
`campsite_watch.py` - script to handle user input, querying, and alerting
## Usage
`python campsite_watch.py` (no args) - creates config file from user input
`python campsite_watch.py -c [config_file].bin` - initiate alerting based off config (intended to run in background)
## Known Issues
- Script successfully notifies on change in availability, but the no longer available section is not populated
- Config is not human editable
- Only Gmail is supported for send address at this time
