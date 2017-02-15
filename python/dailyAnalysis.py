# FB page posts crawling code for past user behaviour analysis
# by Alessandro Ortis
# Facebook API Docs
# 
# This script takes an user/page ID and crawl the information of the posts within the last 30 days
#
# FB API reference:
# https://developers.facebook.com/docs/graph-api/using-graph-api#reading


import os, sys
import json
import urllib
import pprint
import datetime

from pymongo import MongoClient
from bson.objectid import ObjectId
from errorCodes import *

import time, datetime
import json

date_format = '%Y-%m-%d %H:%M:%S'
client = MongoClient('localhost', 27017)
db = client.dailyAnalysis
#db = client.pastBehaviour

def rinnovaToken(old_token):
	# TOFIX: QUESTO METODO NON FUNZIONA	
	"""
		PER OTTENERE UN TOKEN DI 60 GIORNI SEGUIRE QUESTA GUIDA   https://www.slickremix.com/facebook-60-day-user-access-token-generator
	"""

	
	app_id		=	u'1848071075471222'
	secret		=	u'67bbbbebfd1191090a27ea5ad8c6e45f'
	client_id	=	u'1848071075471222'

	app_token = '1848071075471222|tY-TDMNfqEu5MZC54f22o5siRHM'
	#user_token = 'EAAaQz5P5H3YBAEbRKP4Gg4JBHrd38gy3aBgEwagz6axE6onuUXOVLLWJHCji6mfCRqfOnCeivI5zlOe18B1SEb2vnsBy7YQu4cklXIVRhahQnFsg0iIfT3exyDmSWzXWc78cHUuunDqZANk89sK64zQybZCNzwFDg192fkCQZDZD'

	old_token = app_token
	url = "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id="+app_id+"&client_secret="+secret+"&fb_exchange_token="+old_token#+"$user_token="+user_token
	

	print "https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id={"+app_id+"}&client_secret={"+secret+"}&fb_exchange_token={"+old_token+"}"
	print "\n\nhttps://graph.facebook.com/oauth/client_code?access_token="+old_token+"&client_secret="+secret+"&redirect_uri=http://yoda.dmi.unict.it/sentiment/callback.php&client_id="+app_id

	resp = urllib.urlopen(url).read()
	print "\n"
	print resp



def processComments(comments):

	data = []
	if not'data' in comments:
		return data
		
	data = comments['data']
	count = len(comments['data'])

	if 'paging' in comments:
		if 'next' in comments['paging']:
			url = comments['paging']['next']
			resp = urllib.urlopen(url).read()
			resp = json.loads(resp)
			data = data + processComments(resp)

	return data

def processReactions(reactions):

	data = []
	if not'data' in reactions:
		return data

	data = reactions['data']

	if 'paging' in reactions:
		if 'next' in reactions['paging']:
			url = reactions['paging']['next']
			resp = urllib.urlopen(url).read()
			resp = json.loads(resp)
			data = data + processReactions(resp)

	return data

def alreadyExist(ID):
	
	X = db.postDaily.find({'id': ID})
	#print X.count()
	#print X.explain()
	return X.count()>0
	
	
def processFriends(friends):

	data = []
	if not'data' in friends:
		return data
		
	data = friends['data']
	count = len(friends['data'])

	if 'paging' in friends:
		if 'next' in friends['paging']:
			url = friends['paging']['next']
			resp = urllib.urlopen(url).read()
			resp = json.loads(resp)
			data = data + processFriends(resp)

	return data
	
def saveFanInfo(ID):
	global day

	fan_path = ID + "?fields=id,name,fan_count"
	print "FanPath:"
	print fan_path
	params = urllib.urlencode({"access_token": ACCESS_TOKEN})
	host = "https://graph.facebook.com/v2.8/"

	url = "{host}{path}&{params}".format(host=host, path=fan_path, params=params)
	try:
		
		
		try:
			info = urllib.urlopen(url).read()
			info = json.loads(info)
		except:
			fan_path = ID + "?fields=id,name,friends{id,name}"
			url = "{host}{path}&{params}".format(host=host, path=fan_path, params=params)
			info = urllib.urlopen(url).read()
			info = json.loads(info)

			all_friends = []
			if 'friends' in info:
				print "Friends processing"
				all_friends	= processFriends(info['friends'])
			info['friends'] = all_friends		# add the list of friends in the case of profile page
			info['fan_count'] = len(all_friends)

			

		if 'fan_count' in info:
			info['day'] = day		# day of analysis (progressive int)
			id = info['id']
			print(info)
			print "Saving fan count information..."
			insertResult = db.dailyPageInfo.insert(info)

	except:
			print "ERROR during page info request"
			id = -2
	return id
	


def processResponse(pageId,res):
	global global_buffer
	global day
	
	try:
		posts_ls = res['data']
	except:
		print "\n\nres content:"
		pprint.pprint(res)
		print "\n\n"
		sys.exit(-1)
		
	print "Posts in this bunch:\t" +str(len(posts_ls))
	for p_idx, post in enumerate(posts_ls):
	
		created_time	=	post['created_time']
		id		=	post['id']
		post['date_down'] = str(datetime.datetime.now())
		post['day'] = day		# day of analysis (progressive int)
		
		full_pic_url = ''
		if 'full_picture' in post:
			full_pic_url		=	post['full_picture']
		pic_url = ''
		if 'picture' in post:
			pic_url			=	post['picture']

		all_comments = []
		if 'comments' in post:
			print "Comments processing"
			all_comments	=	processComments(post['comments'])
		post['comments'] = all_comments
	
		all_reactions = []
		if 'reactions' in post:
			print "Reactions processing"
			all_reactions	=	processReactions(post['reactions']) 
		post['reactions'] = all_reactions

	#	if 'updated_time' in post:
	#		updated_time		=	post['updated_time']

	#	if 'shares' in post:
	#		shares			=	post['shares']
		
		directory = post['id']	
			
		# Evito di scaricare le immagini se gia' esistono	
		if not alreadyExist(id):
			if not os.path.exists(pageId+"/"+directory):
				os.makedirs(pageId+"/"+directory)
			print "Downloading post pictures..."		
			
			if not full_pic_url == '':
				urllib.urlretrieve(full_pic_url, pageId+"/"+directory+"/"+str(post['id']))
			if not pic_url == '':
				urllib.urlretrieve(pic_url, pageId+"/"+directory+"/thumb_"+str(post['id']))


		print "Adding post to the global buffer (size\t"+str(len(global_buffer))+")"		
		global_buffer.append(post)
		global tot_posts
		tot_posts += 1
		print "Total posts processed:\t"+str(tot_posts)
		if len(global_buffer)==buffer_limit:
			print "Saving posts information..."

			insertResult = db.postDaily.insert_many(global_buffer)
			
			print "\nInsert result:"
			pprint.pprint(insertResult)
			global_buffer = []
			print "waiting "+str(1)+" secs..."
			time.sleep(1)
			print "\n"
	
	

	
	if 'paging' in res and 'next' in res['paging']:
		next_url = res['paging']['next']
		resp = urllib.urlopen(next_url).read()
		resp = json.loads(resp)
		processResponse(pageId,resp)
	elif len(global_buffer)>0:
		print "Saving posts information..."
		insertResult = db.postDaily.insert_many(global_buffer)
		print "\nInsert result:"
		pprint.pprint(insertResult)
		global_buffer = []
		print "waiting "+str(1)+" secs..."
		time.sleep(1)
		print "\n"
	

#global NOT_ALLOWED
#NOT_ALLOWED = False
#global ALTERNATIVE_TOKEN
#ALTERNATIVE_TOKEN = '???'


# Useful for debugging
def FAKE_getPagePosts(ID):
	ID = str(ID)

#Save the number of fans at the moment of crawling
	fan_path = ID + "?fields=id,name,fan_count"
	print "FanPath:"
	print fan_path
	#print "\n"
	params = urllib.urlencode({"access_token": ACCESS_TOKEN})

	url = "{host}{path}&{params}".format(host=host, path=path, params=params)
	try:
		resp = urllib.urlopen(url).read()
		if 'data' in resp:
			if 'fan_count' in resp['data']:
				info = resp['data']
				info['day'] = day		# day of analysis (progressive int)
				id = info['id']
				print "Saving fan count information..."
				pprint.pprint(info)
				insertResult = db.pageInfoDaily.insert(info)

	except:
			print "ERROR during page info request"

	return id

def getPagePosts(ID):

	ID = str(ID)

	host = "https://graph.facebook.com/v2.8/"

	path = ID + "/posts?fields=id,full_picture,shares,picture,type,permalink_url,message,created_time,caption,description,updated_time,targeting,feed_targeting,comments{from,comment_count,id,message,created_time,like_count,user_likes},reactions{type,name,id}&since=" + str(since) +	"&until=" + str(until)

	print "Path:"
	print path
	#print "\n"
	params = urllib.urlencode({"access_token": ACCESS_TOKEN})

	url = "{host}{path}&{params}".format(host=host, path=path, params=params)
#	print "\n\n\t"+path
#	foo = ID + "hello"
#	print foo
#	print ID+"hello"
#	sys.exit(0)

	# open the URL and read the response
	tryflag = True
	countDown = 10
	wait_for = 10
	while tryflag:
		try:
			resp = urllib.urlopen(url).read()
			tryflag = False
		except:
			if countDown == 0:
				print "Not possible to retrieve data from Facebook"
				return ERR_NO_RESPONSE
				break
			countDown -= 1
			print "Sleeping (new attempt after "+str(wait_for)+ " seconds)..."
			time.sleep(wait_for)
			print "Awake .. attempt\t#" + str(countDown)
	if countDown == 0:
		return ERR_NO_RESPONSE


			
	# convert the returned JSON string to a Python datatype 
	respObj = json.loads(resp)
#	respObj = respObj['data']	# keep the response data (list of posts)

	processResponse(ID,respObj)
	id = 2; #means end of data or data empty
	if 'data' in respObj:
		if len(respObj['data'])>0:
			if 'id' in respObj['data']:
				if len(id = respObj['data'][0]['id'].split('_'))>0:
					id = respObj['data'][0]['id'].split('_')[0]

	#Save the number of fans at the moment of crawling
	id = saveFanInfo(ID)

	return id



# get Facebook access token from environment variable
#ACCESS_TOKEN = os.environ['FB_ACCESS_TOKEN']
ACCESS_TOKEN = '1848071075471222|tY-TDMNfqEu5MZC54f22o5siRHM'

if len(sys.argv)<2:
	print "Behaviour Analysis:\tspecify a fb page ID"
	print "EXITING with\t"+str(ERR_INPUT)
	sys.exit(ERR_INPUT)

pageID =sys.argv[1]
global day
day = 0
if len(sys.argv)>2:
	day = sys.argv[2]
	
	
#pageID = 'EsteeLauderUK'
print "\n" + datetime.datetime.now().strftime(date_format)
print "Behaviour Analysis:\t starting crawling from page ID\t-\t" + str(pageID)

global tot_posts
tot_posts = 0
global buffer_limit 
buffer_limit = 10 #number of posts to collect before writing the DB
global global_buffer
global_buffer = []

#print alreadyExist("11503325699_10154628330430700")

# 1485475200	27 Jan 2017 00:00:00 (12 am UCT)
until = time.time()
until =      int(until)  # Midnight at the day of the script run
#until = 1486598400

since =	1485388800  # Thu, 26 Jan 2017 00:00:00 (12 am Europe/London)
since = 	1485385200  # Thu, 26 Jan 2017 00:00:00 (12 am Europe/Zurich)

print "Crawling posts since:\t" + datetime.datetime.fromtimestamp(since).strftime(date_format)
print "Crawling posts until:\t" + datetime.datetime.fromtimestamp(until).strftime(date_format)

print "\n" + datetime.datetime.now().strftime(date_format)

#try:
r = getPagePosts(pageID)
#except:
#	print "Behaviour Analysis:\tUnexpected error", sys.exc_info()[0]
#	sys.exit(ERR_UNEXPECT)

if r==-1: #access not allowed
	print "Behaviour Analysis:\taccess not allowed"
	print "EXITING with\t"+str(ERR_FB_ACCESS)
	sys.exit(ERR_FB_INPUT)
if r<0:
	print "EXITING with\t"+str(r)
	sys.exit(r)
	
print "Behaviour Analysis:\tProcessed\t"+str(tot_posts)+ "\tposts for the user\t"+str(r)
print "(2 if the response is empty)"










