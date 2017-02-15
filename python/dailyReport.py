from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
import re


import pprint

client = MongoClient('localhost', 27017)
db = client.dailyAnalysis

#day = '15'
day = str(sys.argv[1])

ids = [11503325699, 107111802663853, 121945384890,16126780553,147484181947465, 134045083337849,186732534837251,39461368738,229885990518845,235334306596863,143548395657271]

tot_post = db.postDaily.count()

pprint.pprint(tot_post)

print "Total posts in db:\t" + str(tot_post)

for x in ids:
	id = str(x)
	regx = re.compile(id+'_*')
	res = db.postDaily.find({'day':day,'id':{'$regex':regx}},{})
#	info = db.dailyPageInfo.find({'day':day,'id':{'$regex':regx}},{})
#	n_fan = info['fan_count']
	print "id:\t" + id + "\tposts:\t" + str(res.count())

