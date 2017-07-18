import requests, os, time, json, io, warnings, argparse, sys

from datetime import datetime
from multiprocessing import Pool
from crawler_proto import CrawlerProto, ProfileData

class FacebookCrawler(CrawlerProto):

	def __init__(self, results_directory):
		self.results_directory = results_directory + '/facebook/'

	def query(self, target):
		"""

		Args:
			target: Username to be queried
		Returns:
			Raw data returned by the crawl of a profile.

		"""

	    #Get list of feed id from target.
	    feeds_url = 'https://graph.facebook.com/v2.7/' + target + '/?fields=feed.limit(100).since(' + since + ').until(' + until + '){id}&' + token
	    feed_list = []
	    try:
	        feed_list = self._getFeedIds(self._getRequests(feeds_url), [])
	    except:
	        print("No posts in specified range for "+target+". Please expand the time range to allow for more posts")

	    feed_list = [str(i) for i in feed_list] 	    

	    #Get message, comments and reactions from feed.
	    target_pool = Pool()
	    postList = target_pool.map(self._getFeed, feed_list)

	    followerCount_url = 'https://graph.facebook.com/'+target+'/?fields=fan_count&'+token
	    followerCount = self._getFollowerCount(self._getRequests(followerCount_url))

	    return [target, followerCount, postList]


	def format(self, raw_data):
		"""

		Args:
			raw_data: Raw data returned by the crawl of a profile.
		Returns:
			ProfileData tuple of the formatted profile data.

		"""
		target = raw_data[0]
		followerCount = raw_data[1]
		postList = raw_data[2]

		ProfileData['Artist Name'] = target[0]
		ProfileData['Artist Login'] = target[1]
		ProfileData['File create date/time'] = str(datetime.now())
		ProfileData['Follower Count'] = followerCount
		ProfileData['Posts'] = postList

		return ProfileData




	def _getRequests(self, url):

	    requests_result = requests.get(url, headers={'Connection':'close'}).json()
	    time.sleep(0.01)
	    return requests_result

	def _getFeedIds(self, feeds, feed_list):

	    feeds = feeds['feed'] if 'feed' in feeds else feeds

	    for feed in feeds['data']:
	        feed_list.append(feed['id'])
	    
	    if 'paging' in feeds and 'next' in feeds['paging']:
	        feeds_url = feeds['paging']['next']
	        feed_list = self._getFeedIds(self._getRequests(feeds_url), feed_list)
	    return feed_list

	def _getComments(self, comments, comments_count):

	    # If comments exist.
	    comments = comments['comments'] if 'comments' in comments else comments
	    if 'data' in comments:

	        if not stream:
	            comments_dir = 'comments/'
	            if not os.path.exists(comments_dir):
	                os.makedirs(comments_dir)

	        for comment in comments['data']:

	            comment_content = {
	                'id': comment['id'],
	                'user_id': comment['from']['id'],
	                'user_name': comment['from']['name'] if 'name' in comment['from'] else None,
	                'message': comment['message'],
	                'like_count': comment['like_count'] if 'like_count' in comment else None,
	                'created_time': comment['created_time']
	            }

	            comments_count+= 1

	        # Check comments has next or not.
	        if 'next' in comments['paging']:
	            comments_url = comments['paging']['next']
	            comments_count = self._getComments(self._getRequests(comments_url), comments_count)

	    return comments_count

	def _getFollowerCount(self, followerCount_req):
	    followerCount_req = followerCount_req['followerCount_req'] if 'followerCount_req' in followerCount_req else followerCount_req
	    return followerCount_req['fan_count']

	def _getFeedType(self, feedType_req):
	        feedType_req = feedType_req['feedType_req'] if 'feedType_req' in feedType_req else feedType_req
	        return feedType_req['type']

	def _getMessage(self, message_req):
	        message_req = message_req['message_req'] if 'message_req' in message_req else message_req
	        return message_req['message']

	def _getOptimizedReactions(self, opt_reactions):
	        opt_reactions = opt_reactions['opt_reactions'] if 'opt_reactions' in opt_reactions else opt_reactions
	        like = ((opt_reactions['LIKE'])['summary'])['total_count']
	        love = ((opt_reactions['LOVE'])['summary'])['total_count']
	        haha = ((opt_reactions['HAHA'])['summary'])['total_count']
	        wow = ((opt_reactions['WOW'])['summary'])['total_count']
	        sad = ((opt_reactions['SAD'])['summary'])['total_count']
	        angry =((opt_reactions['ANGRY'])['summary'])['total_count']

	        reactions_count_dict1 = {
	            'like': like,
	            'love': love,
	            'haha': haha,
	            'wow': wow,
	            'sad': sad,
	            'angry': angry
	        }


	        return reactions_count_dict1

	def _getFeed(self, feed_id):

	    feed_url = 'https://graph.facebook.com/v2.7/' + feed_id
	    accessable_feed_url = feed_url + '?' + tokenGlobal
	    message_feed_url = feed_url +'?fields=message&' + tokenGlobal

	    post = dict()
	    feed_type_url = feed_url + '?fields=type&' + tokenGlobal
	    feed_type = self._getFeedType(self._getRequests(feed_type_url))
	    post['type'] = feed_type

	    message = self._getMessage(self._getRequests(message_feed_url))
	    post['message'] = message


	    # For comments.
	    comments_url = feed_url + '?fields=comments.limit(100)&' + token
	    
	    comments_count = self._getComments(self._getRequests(comments_url), 0)
	    post['comment count'] = comments_count


	    reactions_summary_url = feed_url + '?fields=reactions.type(LIKE).limit(0).summary(true).as(LIKE),reactions.type(LOVE).limit(0).summary(true).as(LOVE),\
	    reactions.type(HAHA).limit(0).summary(true).as(HAHA),reactions.type(WOW).limit(0).summary(true).as(WOW),\
	    reactions.type(SAD).limit(0).summary(true).as(SAD),reactions.type(ANGRY).limit(0).summary(true).as(ANGRY)&' + token

	    opt = self._getOptimizedReactions(self._getRequests(reactions_summary_url))

	    post['reactions'] = opt

	    # For feed content.
	    feed = self._getRequests(feed_url + '?' + token)

	    if 'message' in feed:
	        feed_content = {
	            'id': feed['id'],
	            'message': feed['message'],
	            'link': feed['link'] if 'link' in feed else None,
	            'created_time': feed['created_time'],
	            'comments_count': comments_count
	        }

	        if get_reactions:
	            feed_content.update(opt)

	    return post