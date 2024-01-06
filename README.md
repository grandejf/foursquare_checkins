# foursquare_checkins

## Instructions
Create a config file called something like foursquare.cfg that looks like:

~~~
user_id = youruserid
oauth_token = youroauthtoken
~~~

To get your User ID, login to Foursquare website (https://foursquare.com/city-guide).
Then click your name->Settings. The User ID toward the bottom and is a number.

To get the  OAuth Token, look at the cookies using the browser's Developer Tools.  The token is stored in the oauth_token cookie.
If there is a trailing "-0", remove it when copying it into the config file.


## Sample Wrapper Script

~~~
#!/bin/sh

cd "$(dirname "$0")"

CONFIGFILE="foursquare.cfg"
JSONFILE="foursquare_checkins.json"
CSVFILE="foursquare_checkins.csv"

./foursquare_checkins.py --config "$CONFIGFILE" --new -j "$JSONFILE"
./foursquare_checkins.py -j "$JSONFILE" --exportcsv > "$CSVFILE"

~~~
