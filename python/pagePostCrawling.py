# FB page posts crawling code
# by Alessandro Ortis
# Facebook API Docs
# https://developers.facebook.com/docs/graph-api/using-graph-api#reading


import os, sys
import json
import urllib
import pprint


global_buffer = []
import json
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
#	print "\n\n"
	#print comments
	data = comments['data']
	#for idx, user in enumerate(data):
		#print str(idx+1)+")\t"+user['from']['name']
	count = len(comments['data'])

	if 'next' in comments['paging']:
		url = comments['paging']['next']
#	if len(url)>0:	
		resp = urllib.urlopen(url).read()
		resp = json.loads(resp)
#		print "\n new recursion"
		count = count + processComments(resp)

#	print "Counted comments:\t" + str(count)		
	return count
#	sys.exit(0)

def processReactions(reactions):
	data = reactions['data']
	count = len(reactions['data'])
	if 'next' in reactions['paging']:
		url = reactions['paging']['next']
		resp = urllib.urlopen(url).read()
		resp = json.loads(resp)
		count = count + processReactions(resp)
	return count


def processResponse(pageId,res,n,name=None):
#TODO:	per ogni elemento restituito (post):
#	- controlla che sia di tipo photo
#	- salva i dati in json/pickle e scarica la foto
#	- conta quanti post sono attualmente in memoria (global_buffer)
#	- se non hai raggiunto il numero richiesto e next_url non e' vuoto continua ricorsivamente
	"""
	Prototipo di risposta:

	{u'id': u'107111802663853',
	 u'posts': {u'data': [{u'created_time': u'2017-01-17T09:00:01+0000',
		               u'id': u'107111802663853_1373547282686959',
		               u'message': u'For when you need a little extra coverage, try our DoubleWear Stay-in-Place Concealer! Shop now: http://bit.ly/2iHG2cp'}],
		    u'paging': {u'next':
				u'previous':}}}
	"""
	try:
		if not name:
			name = res['name']
	except:
		print "ERROR"
		pprint.pprint(res)
		sys.exit(0)

	if not 'posts' in res:
		print "Access not allowed!\tuser:\t"+name
#		pprint.pprint(res)
		return -1

	data = res['posts']['data']
	print "\nAnalysing results for the profile:\t" + name
	for post in data:
		if post['type'] == 'photo':
			created_time	=	post['created_time']
			id		=	post['id']
			if 'message' in post:
				message		=	post['message']
			else:
				message = ''
			post_permalink	=	post['permalink_url']
			
			pic_url		=	post['full_picture']
			if 'comments' in post:
				comments_count	=	processComments(post['comments'])
			else:
				comments_count = 0	
			if 'reactions' in post:
				reactions_count	=	processReactions(post['reactions']) 
			else:
				reactions_count = 0	
#			print "\n"
#			print message
#			print "Tot. comments:\t" + str(comments_count)
#			print "Tot. reactions:\t" + str(reactions_count)

			
			global_buffer.append(post)
#			print "Adding post to the global buffer (size\t"+str(len(global_buffer))+")"		
			
			directory = post['id']
			if not os.path.exists(pageId+"/"+directory):
			    os.makedirs(pageId+"/"+directory)

			print "Saving post information..."
			obj ={'postId':{},'postMessage':{}, 'postURL':{},'postComments':{}, 'postReactions':{}}
			obj['postId'] = id
			obj['postMessage'] = message
			obj['postURL'] = post_permalink
			obj['postComments'] = comments_count
			obj['postReactions'] = reactions_count
			ff = open(pageId+"/"+directory+"/"+str(id)+".json",'w')
			ff.write(json.dumps(obj))
			ff.close()
			print "Downloading post picture..."		
			urllib.urlretrieve(pic_url, pageId+"/"+directory+"/post_picture")

	
	

		if len(global_buffer) == n:
			return

	if 'paging' in res['posts']:
		next_url = res['posts']['paging']['next']
		resp = urllib.urlopen(next_url).read()
		resp = json.loads(resp)
		processResponse(pageId,res,n,name)


def getPagePosts(pageID,n=None):

	host = "https://graph.facebook.com/v2.8/"
	post_limit = None # the limit is granted by the checking on the global_buffer size
	if post_limit:
		path = pageID + "?fields=name,posts.limit("+str(post_limit)+"){id,full_picture,type,comments,reactions,permalink_url,created_time,message}"
	else:
		path = pageID + "?fields=name,posts{id,full_picture,type,comments,reactions,permalink_url,created_time,message}"	#{message,full_picture,comments,reactions,permalink_url}"

	params = urllib.urlencode({"access_token": ACCESS_TOKEN})


	url = "{host}{path}&{params}".format(host=host, path=path, params=params)

	# open the URL and read the (first) response
	resp = urllib.urlopen(url).read()
#	print resp
	

	# convert the returned JSON string to a Python datatype 
	respObj = json.loads(resp)
	
	#display the result
#	pprint.pprint(respObj)
	processResponse(pageID,respObj,n)
	return respObj['name']


# get Facebook access token from environment variable
#ACCESS_TOKEN = os.environ['FB_ACCESS_TOKEN']
ACCESS_TOKEN = '1848071075471222|tY-TDMNfqEu5MZC54f22o5siRHM'

# build the URL for the API endpoint
pageID = "runfederun" #federica fontana "741742414" #Alessandra Airo'      #"EsteeLauderUK"

n = 10 #tries to crawl n posts with pictures

f = open('IDs.txt')
id_list = f.read()
f.close()
id_list = id_list.split('\n')
#id_list = ['EsteeLauderUK']
for id in id_list:
	global_buffer = []
	if len(id)>0:
		#print "ID:\t" + id
		
		pageID = id
		r = getPagePosts(pageID,n)
		if r==-1: #access not allowed
			continue;
		print "Processed\t"+str(len(global_buffer))+ "\tposts for the user\t"+r
#	sys.exit(0)

#rinnovaToken(ACCESS_TOKEN)
#sys.exit(0)










