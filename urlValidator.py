''' Created for UALR COSMOS Team
	Given a .csv with urls, this script will return a .csv with
	validated urls using requests to determine the status code (200)
	It will also return urls in expanded form, their domain name,
	and the top 20 most common domain names.
	
	Enter the input filename and column that contains the urls.
	
	WARNING: Data in .csv will be overwritten if re-ran.
'''

import argparse, requests, csv
from collections import Counter
from itertools import zip_longest
from queue import Queue
from threading import Thread
from urllib.parse import urlparse

def readFile(filename, col): # Opens input file, appends all items to jobs[], calls validate()
	file = open(filename, encoding='utf-8')
	reader = csv.reader(file)
	for item in reader:
		try:
			if item[col]:
				for url in item[col].split(','):
					jobs.append(url)
		except:
			pass
	file.close()
	
	print(str(len(jobs)) + " URLs found.\n")
	
	for i in range(8):		# Start threads, each one will process one job from the jobs[] queue
		t = Thread(target = validate, args = (queue,))
		t.setDaemon(True)
		t.start()
		
	for job in jobs:		# For each item in jobs[], put each into the queue in FIFO sequence
		queue.put(job)
	queue.join()			# Wait until all jobs are processed before quitting

def validate(queue):
	while True:
		url = queue.get()	# Retrieves item from queue
		try:
			if url[:4] != 'http':
				url = 'http://' + url
			request = requests.get(url, timeout=30)
			if int(request.status_code) < 400:
				validUrls.append(request.url)	# Expands url to be unshortened
				global count
				count += 1
				if count % 100 == 0:
					print('Valid Urls:', count)
			queue.task_done()
			
		except requests.HTTPError:
			print('HTTP Error 500:', url)
			queue.task_done()
			
		except requests.ConnectionError:
			# print('HTTP Connection Error:', url)	# Can be verbose
			queue.task_done()
			
		except requests.Timeout:
			print('Timeout Error:', url)
			queue.task_done()
			
		except Exception as e:	# For rare requests.get() errors
			print('Catch All Error:', url)
			print(e.__class__)
			queue.task_done()

def saveOutput(validUrls, urlDomains, topDomainNames, topDomainNumbers):
	# Finds the domain name and extension (.com .net) using urlparse
	for url in validUrls:
		urlDomains.append('.'.join(urlparse(url).netloc.split('.')[-2:]))
		
	# Finds the top 20 most common domain names
	for item in Counter(urlDomains).most_common(20):
		topDomainNames.append(item[0])
		topDomainNumbers.append(item[1])
		
	# Writes header row and saves to csv
	with open(output, 'w', encoding='utf-8', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['url', 'domain_name', 'top_domain', 'top_domain_num'])
		for url, domain, topUrl, topNum in zip_longest(validUrls, urlDomains, topDomainNames, topDomainNumbers):
			writer.writerow([url, domain, topUrl, topNum])

# Creates arguments to be used when running the file ($python urlValidator.py -c 5 -f filename.csv)
parser = argparse.ArgumentParser(description='Validates all urls in a csv column.')
parser.add_argument('-c', required=True, type=int, help='Column index containing urls')
parser.add_argument('-f', required=True, type=str, help='Input filename path')
args = parser.parse_args()

input = args.f
# input = 'telegramGroup_groupName.csv'
output = input[:-4] + '_validUrls.csv'
col = args.c
# col = 5
count = 0
jobs = []
validUrls = []
urlDomains = []
topDomainNames = []
topDomainNumbers = []
queue = Queue()

readFile(input, col)
saveOutput(validUrls, urlDomains, topDomainNames, topDomainNumbers)
print('Valid Urls:', count)
