import json
import requests


NYT_key = '58c51755a97d4f11abf74fb99d3ffb40'

class Article():
	"""object representing one article"""
	def __init__(self, article_dict={}):
		if 'title' in article_dict:
			self.title = article_dict['title']
		else:
			self.title = ""
		
		if 'byline' in article_dict:
			self.author = article_dict['byline']
		else:
			self.author = ""

		if 'published_date' in article_dict:
			self.published_date = article_dict['published_date']
		else:
			self.published_date = ""	
		
		if 'abstract' in article_dict:
			self.abstract = article_dict['abstract']
		else:
			self.abstract = ""

		if 'section' in article_dict:
			self.section = article_dict['section']
		else:
			self.section = ""


	def show_author(self):
		return self.author

	def show_title(self):
		return self.title

	def show_date(self):
		return self.published_date		

	def __str__(self):
		return "%s, Written by %s, Published by the NYT on %s in the %s section. %s" % (self.title, self.author, self.published_date, self.section, self.abstract)		


##Returns a list of top stories on NYTimes website OVERALL.
def nytTop():
	article_lst = []
	headlines = []
	style = ".json"
	key = NYT_key
	url = "https://api.nytimes.com/svc/topstories/v2/home.json"
	data = requests.get(url, params={'api-key':key}).json()
	for article in data['results']:
		section = article['section']
		title = article['title']
		summary = article['abstract']
		author = article['byline']
		date = article['published_date']
		article_dic = {'title':title, 'byline':author, 'published_date': date}
		final = Article(article_dic)
		article_lst.append(final)
	return article_lst


def sectionTop(section):
	article_lst = []
	style = ".json"
	key = NYT_key
	url = "https://api.nytimes.com/svc/topstories/v2/arts.json"
	data = requests.get(url, params={'api-key':key}).json()
	for article in data['results']:
		section = article['section']
		title = article['title']
		summary = article['abstract']
		author = article['byline']
		date = article['published_date']
		article_dic = {'title':title, 'byline': author, 'published_date': date, 'section':section, 'abstract': summary}
		final = Article(article_dic)
		article_lst.append(final)
	return article_lst


def nytSearch(q):
	article_lst = []
	key = NYT_key
	url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
	data = requests.get(url, params={'api-key':key, 'q':q}).json()
	for item in data['response']['docs']:
		title = item['headline']['main']
		author = item['byline']['original']
		summary = item['snippet']
		date = item['pub_date']
		#section = item['section_name']
		#uri = item['uri']
		web_url = item['web_url']
		article_dic = {'title':title, 'byline':author, 'published_date': date, 'abstract': summary}
		final = Article(article_dic)
		article_lst.append(final)
	return article_lst

#for item in sectionTop('Arts'):
#	print(item)

for item in nytSearch('Drake'):
	print(item)
	print(""" 


		""")

