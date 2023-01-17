# logistique-agepoly-bot
A Telegram bot to ease the daily business of AGEPoly's Logistic team


# How to create a test environment ?
### The following instructions have not been tested yet and are more likely not really functionnal since the has too much interdependencies. Don't hesitate to reach out to @eliorpap on Telegram for setup help!
* Clone the repository
* Create a virtual environment
* Install the requirements
* Add a .env file
  * Add ENV=TEST
* Create a test bot on Telegram
  * Add the token to the .env file (TOKEN=your_token)
* If you want to dev truffe related methods, ask for a truffe token and add it to the .env file (TRUFFE_TOKEN=your_token)
* If you want to dev Google calendar related methods, create a Google Cloud project and a service account. You can then add the credentials to the .env file (GSERVICE_CREDENTIALS=your_credentials)
  * You also have to create a calendar and share it with the service account. Then add the calendar ID to the .env file (CALENDAR_ID=your_calendar_id)
* If you want to dev database related methods, create a MongoDB project, database and service account and add the credentials to the .env file (MONGO_URI=your_uri_provided_by_mongo)
  * You have to open the database to the web in the network settings of MongoDB (0.0.0.0/0)
* If you want to dev support group related methods, create a support group and add the ID to the .env file (SUPPORT_GROUP_ID=your_group_id)

# How to run the bot ?
Run the bot with the following command: python3 main.py
You can also run it from an IDE like PyCharm

# What else can I run ?
You can run the following commands to execute standalone actions
* python3 main.py refresh_calendar
* python3 main.py expire_accreds