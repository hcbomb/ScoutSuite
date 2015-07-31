#!/usr/bin/env python2

# Import opinel
from opinel.utils import *
from opinel.utils_cloudtrail import *

# Import Scout2 tools
from AWSScout2.utils import *
from AWSScout2.filters import *
from AWSScout2.findings import *


########################################
##### CloudTrails functions
########################################

def analyze_cloudtrail_config(cloudtrail_info, force_write):
    analyze_config(cloudtrail_finding_dictionary, cloudtrail_filter_dictionary, cloudtrail_info, 'CloudTrail', force_write)

def get_cloudtrail_info(key_id, secret, session_token, selected_regions, fetch_ec2_gov):
    cloudtrail_info = {}
    cloudtrail_info['regions'] = {}
    print 'Fetching CloudTrail data...'
    for region in build_region_list('cloudtrail', selected_regions, fetch_ec2_gov):
        cloudtrail_info['regions'][region] = {}
        cloudtrail_info['regions'][region]['name'] = region
    thread_work((key_id, secret, session_token), cloudtrail_info, cloudtrail_info['regions'], get_region_trails)
    return cloudtrail_info

def get_region_trails(connection_info, q, params):
    key_id, secret, session_token = connection_info
    while True:
      try:
        cloudtrail_info, region = q.get()
        manage_dictionary(cloudtrail_info['regions'][region], 'trails', {})
        cloudtrail_client = connect_cloudtrail(key_id, secret, session_token, region)
        trails = cloudtrail_client.describe_trails()
        cloudtrail_info['regions'][region]['trails_count'] = len(trails['trailList'])
        for trail in trails['trailList']:
            trail_info = {}
            for key in trail:
                trail_info[key] = trail[key]
            trail_details = cloudtrail_client.get_trail_status(Name = trail['Name'])
            for key in ['IsLogging', 'LatestDeliveryTime', 'LatestDeliveryError', 'StartLoggingTime', 'StopLoggingTime', 'LatestNotificationTime', 'LatestNotificationError', 'LatestCloudWatchLogsDeliveryError', 'LatestCloudWatchLogsDeliveryTime']:
                trail_info[key] = trail_details[key] if key in trail_details else None
            cloudtrail_info['regions'][region]['trails'][trail['Name']] = trail_info
      except Exception, e:
          print ':('
          printException(e)
      finally:
        q.task_done()
