# Telegram
Will crawl and save all messages from all groups from a linked Telegram account.
Must fill api_id, api_hash, and phone variables.
Once run, a code will be sent to the Telegram app to authorize this app.

Results are saved in group specific csv files.
These files are created on execution and are appended to if re-ran.
Re-running the code will start from last saved message ID and will crawl any new messages.

URLs are extracted using external package URLExtract. Further scrubbing might be needed.

```
urlValidate = True is twice as slow but uses requests to confirm if url is reachable/valid (code 200)
urlValidate = True: ~60 seconds per 1000 messages (Will only save url if status_code is <400)
urlValidate = False: <30 seconds per 1000 messages (Will save any found url without checking status)
```

WARNING: Data will be appended to the .csv file if re-ran.



# telegramHTMLExport
Similar to telegram.py, this script will crawl and save all messages from a Telegram group or channel that has been exported as html files. This allows a user to export the chats from any group or channel without joining. It also doesn't rely on an outside package and is able to 100% accuratly find all URL hrefs.

Using the telegram desktop app, click the three verticle dots on the top-middle of the page and select 'Export Chat History'. Select preferred options, set export path, and click Export.

Export results are saved as .html files. This script ignores all other generated files. (.js .css)

Once crawled the script will run urlValidator.py using the command line arguments.



# urlValidator
Given a .csv with urls, this script will return a .csv with validated urls using requests to determine the status code (200)
It will also return urls in expanded form (Expands bit.ly urls), their domain name, and the top 20 most common domain names.

This file has command line argument support:
```
-c Column index containing urls
-f Input filename path
-h Lists help info and possible arguments

Example:  $python urlValidator.py -c 5 -f filename.csv
```

This is a threaded version of what is baked into telegram.py using the variable urlValidate = True.
The threaded version is much faster and returns a simple .csv with the urls in one column.

WARNING: Data will be appended to the .csv file if re-ran.
