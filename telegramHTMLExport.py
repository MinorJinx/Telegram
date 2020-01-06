''' Created for UALR COSMOS Team
	Will crawl and save all messages from a Telegram group or channel
	that has been exported as html files.
	
	Using the telegram desktop app, click the three verticle dots on the top-middle of the page
	and select 'Export Chat History'. Select preferred options, set export path, and click Export.
	Export results are saved as .html files. This script ignores all other generated files. (.js .css)
	
	Results are saved in a group specific csv file. It will also work for Telegram channels,
	however the 'reply_to_msg_id' column will be empty.
	This file is created on execution and is appended to if re-ran.
	
	URLs are extracted by identifying the <a> tags. Further scrubbing might be needed.
	urlValidate = True uses requests to confirm if url is reachable/valid (code 200)
	This uses urlValidator.py and python threading to quickly validate the urls.
	Results are saved in a second .csv titled, 'original_filename_validUrls.csv'
	
	WARNING: Data will be appended to the .csv file if re-ran.
'''

from bs4 import BeautifulSoup
from pathlib import Path
from tkinter import Tk
from tkinter import filedialog
import csv, datetime, glob, os, re, sys

# Choose directory that contains the .html files
print('Choose the input directory...')
Tk().withdraw()
inputDir = filedialog.askdirectory(initialdir=os.getcwd(), title='Select Folder')+'/'
print('Input Dir:', inputDir, '\n')

urlValidate = True
print('URL Validation =', urlValidate)

# Check for 'messages.html' and rename file to 'messages1.html'
for file in glob.glob(inputDir + '/*.html'):
	if file[-6:-5] == 's':
		os.rename(file, file[:-5] + '1' + '.html')	# Appends '1' before '.html'

# Sorts files in natural order by the number before '.html'
for file in sorted(glob.glob(inputDir + '/*.html'), key=lambda f: int(f[len(inputDir)+8:-5])):
	with open(file, 'r', encoding='utf-8') as f:
		soup = BeautifulSoup(f, 'html.parser')
		
	# Saves 'groupName' and finds all chat messages
	groupName = soup.find('div', {'class': 'text bold'}).text.strip()
	chatHistory = soup.find_all('div', {'class': ['message default clearfix', 'message default clearfix joined']})
	logFile = 'telegramGroup_'+groupName+'.csv'
	
	# Creates log file and writes header row, then reopens for main loop below
	if not os.path.exists(logFile):
		writer = csv.writer(open(logFile, 'w', encoding='utf-8', newline=''))
		writer.writerow(['message_id', 'reply_to_msg_id', 'username', 'timestamp', 'message', 'url'])
		
	writer = csv.writer(open(logFile, 'a', encoding='utf-8', newline=''))
	
	# Supports consoles that can't display non ascii characters
	# Uses pathlib to easily truncate path names
	try:
		print('Group:', groupName, 'File:', Path(*Path(file).parts[-3:]))
	except:
		print('Unknown_Group_Name', 'File:', Path(*Path(file).parts[-3:]))
		
	# Main loop that gathers info about each message
	for div in chatHistory:
		messageDiv = div.find('div', {'class': 'text'})
		urls = []
		if messageDiv:
			message = messageDiv.text.strip()	# strip() removes html tags
			messageId = div.get('id')
			replyToDiv = div.find('div', {'class': 'reply_to details'})
			if replyToDiv:
				replyTo = 'message' + re.sub('.*?([0-9]*)$',r'\1', replyToDiv.select('a')[0]['href'])
			else:
				replyTo = None
			timestampDiv = div.find('div', {'class': 'pull_right date details'})
			timestamp = datetime.datetime.strptime(timestampDiv.get('title'), '%d.%m.%Y %H:%M:%S')
			urlDiv = messageDiv.find_all('a')
			for a in urlDiv:
				if a['href']:
					urls.append(a['href'])
			usernameDiv = div.find('div', {'class': 'from_name'})
			if not len(div.get('class')) == 4:
				username = usernameDiv.text.strip()
				
			writer.writerow([messageId, replyTo, username, timestamp, message, ','.join(map(str, urls))])

# Runs 'urlValidator.py' with arguments -c and -f
if urlValidate:
	print('\nValidating URLs...\n')
	os.system(sys.executable + ' urlValidator.py -c 5 -f ' + logFile)