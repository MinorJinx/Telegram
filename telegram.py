''' Created for UALR COSMOS Team
	Will crawl and save all messages from all groups from a linked Telegram account.
	Must fill api_id, api_hash, and phone variables.
	Once run, a code will be sent to the Telegram app to authorize this app.
	
	Results are saved in group specific csv files. It will also work for Telegram channels,
	however the 'reply_to_msg_id' and 'from_id' columns will be empty.
	These files are created on execution and are appended to if re-ran.
	Re-running the code will start from last saved message ID and will crawl any new messages.
	
	URLs are extracted using external package URLExtract. Further scrubbing might be needed.
	urlValidate = True is twice as slow but uses requests to confirm if url is reachable/valid (code 200)
	urlValidate = True: ~60 seconds per 1000 messages (Will only save url if status_code is <400)
	urlValidate = False: <30 seconds per 1000 messages (Will save any found url without checking status)
	
	Optionally after crawling, use urlValidator.py for a threaded version of urlValidate.
	This is a far faster approach but the option is included in this file for convenience.
	
	WARNING: Data will be appended to the .csv file if re-ran.
'''

from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerEmpty
from urlextract import URLExtract
import csv, os, requests

groupTitles = []
groupUsernames = []
groupMembers = []
groupTopIDs = []
urlValidate = False
api_id = 1111111
api_hash = 'cb0ce0d6898b519b5fd0f79c890bbfc6'
phone = '12223334444'
client = TelegramClient(phone, api_id, api_hash)

# Uses api info to connect and authorize this app as a .session file.
client.connect()
if not client.is_user_authorized():
	print('Not authorized, sending code to telegram app.')
	client.send_code_request(phone)
	client.sign_in(phone, input('Enter the code: '))

# Queries Telegram client to retrieve group names
result = client(GetDialogsRequest(
	limit=0,
	offset_date=None,
	offset_id=0,
	offset_peer=InputPeerEmpty(),
	hash = 0))

# Extracts group 'title' and 'username' from result.chats
# 'title' is the visible group name, 'username' is the internal reference name
# Exception is for empty result.chats
for chat in result.chats:
	try:
		groupTitles.append(chat.title)
		groupUsernames.append(chat.username)
	except AttributeError:
		pass

# Extracts number of members and messages for each group and prints.
# Extracts the most recent message id. Used to stop main while loop below.
for dialog, username in zip(result.dialogs, groupUsernames):
	channel_full_info = client(GetFullChannelRequest(channel=username))
	memberCount = channel_full_info.full_chat.participants_count
	groupMembers.append(memberCount)
	groupTopIDs.append(dialog.top_message)
	print('Messages:', str(dialog.top_message).ljust(9), 'Members:', str(memberCount).ljust(9), 'Group:', username)

print('URL Validation =', urlValidate)
	
# Loop through all groups
for title, username, members, topID in zip(groupTitles, groupUsernames, groupMembers, groupTopIDs):

	# Creates log file and writes group info and header rows
	# 'offset' or offset_id is the starting message id
	# 'minimm' or min_id is the lowest id to be searched
	# Telethon's request returns id's from high to low (offset_id to min_id) or (100-1)
	logFile = 'telegramGroup_'+username+'.csv'
	if not os.path.exists(logFile):
		writer = csv.writer(open(logFile, 'w', encoding='utf-8', newline=''))
		writer.writerow(['groupTitle', 'groupUsername', 'groupMembers', 'groupMessages'])
		writer.writerow([title, username, members, topID])
		writer.writerow(['id', 'reply_to_msg_id', 'from_id', 'date', 'message', 'url'])
		offset = 101
		minimum = 0
		
	# If log file exists, update the 'groupMembers' and 'groupMessages' cells
	# Also retrieve last message ID and store in 'minimum'
	else:
		with open(logFile, 'r', encoding='utf-8') as f:
			lines = list(csv.reader(f))
			writer = csv.writer(open(logFile, 'w', encoding='utf-8', newline=''))
			for line in lines:
				if line == lines[1]:
					line[2] = members
					line[3] = topID
				writer.writerow(line)
			offset = lines[-1][0]	# First element of last row in csv
			if offset != 'id':		# Checks if csv is empty apart from header row
				minimum = int(offset)
				offset = minimum+100
				
			# If a log file has been created but only has a header row, set minimum to 0
			else:
				offset = 101
				minimum = 0
	
	# Opens csv file and sets group_entity to be used in GetHistoryRequest
	writer = csv.writer(open(logFile, 'a', encoding='utf-8', newline=''))
	group_entity = client.get_input_entity(username)
	print('\nStarting Group', username, 'at ID:', minimum, 'of', topID)
	
	# Loop until topID has been reached
	while True:
		# Queries Telegram client to retrieve messages
		# Will start at offset_id, capture up to 100 messages until min_id
		posts = client(GetHistoryRequest(
			peer=group_entity,
			limit=100,
			offset_date=None,
			offset_id=offset,
			max_id=0,
			min_id=minimum,
			add_offset=0,
			hash=0))
			
		# Check to see if entire block of messages was deleted (spam bots)
		if posts.chats:
			# Loop through every message in reverse order (from 1-100)
			# Check if not empty message, such as sticker
			# Extract urls and write info to csv row
			for m in reversed(posts.messages):
				if m.message:
					date = str(m.date)[:-6]	# Strips timezone: +00:00
					msg = m.message.replace('\n', ' ')
					
					# Uses requests to check if url status_code is <400 (reachable)
					# If urlValidate = False, urls are collected and saved without checking status
					if urlValidate:
						validUrls = []
						extractor = URLExtract()
						for url in extractor.find_urls(msg):
							try:
								if url[:4] != 'http':
									url = 'http://' + url
								request = requests.get(url)
								if int(request.status_code) < 400:
									validUrls.append(request.url)
							except requests.exceptions.ConnectionError:
								pass
							except Exception as e:	# For rare requests.get() errors
								print('CATCH ALL', e.__class__)
						writer.writerow([m.id, m.reply_to_msg_id, m.from_id, date, msg, ','.join(map(str, validUrls))])
					else:
						extractor = URLExtract()
						url = ','.join(map(str, extractor.find_urls(msg)))
						writer.writerow([m.id, m.reply_to_msg_id, m.from_id, date, msg, url])
				offset = m.id+100	# Increments current id += 100 to be used for next request
				minimum = m.id
				if minimum % 1000 == 0:
					print('Group', username, 'at ID:', minimum, 'of', topID)
					
		# If message block was deleted, increment by 100 to next block
		else:
			if not minimum >= topID:
				if round(minimum, -2) % 1000 == 0:
					print('Group', username, 'at ID:', minimum, 'of', topID, 'Skipping Deleted Messages')
				minimum = offset
				offset += 100
			
		# Break while loop if done then move onto next group
		if minimum >= topID:
			print('Finished Group', username, 'at ID:', minimum, 'of', topID, '\n')
			break

# Gracefully closes client and exits (prevents 'Task was destroyed but it is pending' error)
client.disconnect()
