''' Created for UALR COSMOS Team
	Given a .csv with text, this script will return a .csv with translated text.
	It requires the input language to be defined as a country code: ('uk' is Ukranian)
	
	Once run, the messages are sent to a .html file and loaded into Chrome using Selenium.
	It waits for a user to click 'Translate' on Chrome and then press enter in the console.
	If the page auto translates and says 'Show original' then press enter in the console.
	It then slowly scrolls through the page and translates the text fields.
	After scrolling through the document, the now translated text is saved to a .csv
	
	Lower 'scrollAmount' if your screen is less than 1080px in height.
	Enter the column to translate, language, and input filename.
	
	WARNING: Data in .csv will be overwritten if re-ran.
'''

# Links to chromedriver

import argparse, csv, os, time
from bs4 import BeautifulSoup
from selenium import webdriver
	
# Creates arguments to be used when running the file ($python seleniumTranslate.py -c 5 -l uk -f filename.csv)
parser = argparse.ArgumentParser(description='Validates all urls in a csv column.')
parser.add_argument('-c', required=True, type=int, help='Column index containing urls')
parser.add_argument('-l', required=True, type=str, help='Input language ("uk" for Ukranian)')
parser.add_argument('-f', required=True, type=str, help='Input filename path')
args = parser.parse_args()

col = args.c
fromLang = args.l
inputFile = args.f

# col = 5
# inputFile = 'telegramGroup_groupName.csv'
output = inputFile[:-4] + '_translated.csv'
toTranslate = inputFile[:-4] + '_toTranslate.html'
# fromLang = 'uk'
toLang = 'en'

# Reads input file and saves each .csv row as an html paragraph
with open(inputFile, encoding='utf-8') as inputFile:
	reader = csv.reader(inputFile)
	with open(toTranslate, 'w', encoding='utf-8') as f:
		for row in reader:
			f.write('<p>' + row[col] + '</p>')

# Sets Selenium options for Chrome Browser
options = webdriver.ChromeOptions()
prefs = {'translate_whitelists': {fromLang:toLang}, 'translate':{'enabled':'true'}}
options.add_experimental_option('prefs', prefs)
options.add_experimental_option('excludeSwitches', ['enable-logging'])	# Prevents console logging
driver = webdriver.Chrome(chrome_options = options)
driver.get(os.path.realpath(toTranslate))

print('\nClick Translate in Google Chrome if it has not been done already')
input('Once clicked, press Enter to continue...')

# Lower this if your screen height is below 1080px
scrollAmount = 700
pageHeight = round(driver.execute_script('return document.body.scrollHeight')/scrollAmount) + 1

for i in range(0, pageHeight):
	driver.execute_script('window.scrollTo(0, '+str(scrollAmount)+')')
	scrollAmount += 700
	time.sleep(1)

print('\nReached EOF')
time.sleep(2)

# Finds each paragraph and writes to output file
writer = csv.writer(open(output, 'w', encoding='utf-8', newline=''))
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
messages = soup.find_all('p')

for p in messages:
	writer.writerow([str(p.text.strip())])

# Exit gracefully and delete .html file
driver.quit()
os.remove(toTranslate)
print('Translation Complete')
