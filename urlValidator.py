''' Created for UALR COSMOS Team
	Given a .csv with urls, this script will return a .csv with
	validated urls using requests to determine the status code (200)
	It will also return urls in expanded form.
	
	Enter the input filename and column that contains the urls.
	
	WARNING: Data will be appended to the .csv file if re-ran.
'''

import requests, csv
from queue import Queue
from threading import Thread

def readFile(filename, col): # Opens input file, appends all items to jobs[], calls validate()
	file = open(filename, encoding='utf-8')
	reader = csv.reader(file)
	for item in reader:
		if item[col]:
			for url in item[col].split(','):
				jobs.append(url)
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
			request = requests.get(url)
			if int(request.status_code) < 400:
				validUrls.append(request.url)	# Expands url to be unshortened
				global count
				count += 1
				if count % 10 == 0:
					print('Valid Urls:', count)
			queue.task_done()
			
		except requests.HTTPError:
			print("HTTP Error 500")
			queue.task_done()
			
		except requests.ConnectionError:
			# print("HTTP Connection Error")
			queue.task_done()
			
		except requests.Timeout:
			print("Timeout Error")
			queue.task_done()
			
		except Exception as e:
			print('CATCH ALL')
			print(e.__class__)
			queue.task_done()

def saveOutput(validUrls):
	with open(output, 'a', encoding='utf-8', newline='') as file:
		writer = csv.writer(file)
		for url in validUrls:
			writer.writerow([url])

input = 'telegramGroup_groupName.csv'
output = input[:-4] + '_validUrls.csv'
col = 5		# Which column are the urls in
count = 0
jobs = []
validUrls = []
queue = Queue()

readFile(input, col)

saveOutput(validUrls)