# To run this repeatedly using launchd enter the following in the terminal:
# launchctl load ~/Library/LaunchAgents/com.ps.billscrapers.plist 
source /Users/schlueter/PycharmProjects/bills/venv/bin/activate && /Users/schlueter/PycharmProjects/bills/venv/bin/python /Users/schlueter/PycharmProjects/bills/scrapers.py && deactivate