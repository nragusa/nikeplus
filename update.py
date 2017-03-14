#!/usr/bin/env python
"""This program takes in a Nike access token and a total number of runs
to retrieve from Nike, starting with the most recent run first. It will
then call the Nike API a second time to retrieve GPS coordinates for
each run, write this run data to a file, then upload the file to an S3
bucket. This resulting file is formatted in such a way that it can be
queried by Amazon Athena.
"""
__version__ = '0.1'
__author__ = 'Nick Ragusa'

import argparse
import json
import sys

import boto3
import requests
from pygeocoder import Geocoder

PARSER = argparse.ArgumentParser()
PARSER.add_argument("-t", "--token", help="nike access token", type=str, required=True)
PARSER.add_argument("-r", "--runs", help="number of runs back", type=int, required=True)
PARSER.add_argument("-b", "--bucket", help="S3 bucket", type=str, required=True)
PARSER.add_argument("-k", "--key", help="The S3 key for the file", type=str, required=True)
ARGS = PARSER.parse_args()
KM_TO_MILES = 0.621371

def get_gps(aid, token):
    """Returns lattitude, longitude, and elevation coordinates
    of the beginning and end of a run.

    Keyword arguments:
    aid -- unique activity ID of the run
    token -- nike API access token
    """
    url = 'https://api.nike.com/v1/me/sport/activities/{}/gps?access_token={}'.format(aid, token)
    try:
        response = requests.get(url)
    except requests.exceptions.HTTPError as error:
        print 'Problem calling Nike API: {}'.format(error)
        sys.exit(1)
    else:
        try:
            data = json.loads(response.text)
        except ValueError:
            print 'Problem loading Nike response into JSON'
            sys.exit(1)
        if response.status_code != 200:
            return ({'latitude': 0, 'longitude': 0, 'elevation': 0},
                    {'latitude': 0, 'longitude': 0, 'elevation': 0})
        else:
            return data['waypoints'][0], data['waypoints'][-1]

def main():
    """Runs the main program"""
    access_token = ARGS.token
    runs = ARGS.runs
    s3_bucket = ARGS.bucket
    s3_key = ARGS.key
    url = ('https://api.nike.com/v1/me/sport/activities/RUNNING?count={}'
           '&access_token={}'.format(runs, access_token))
    try:
        response = requests.get(url)
    except requests.exceptions.HTTPError as error:
        print 'Problem calling Nike API: {}'.format(error)
        sys.exit(1)
    else:
        if response.status_code != 200:
            print 'Non-200 code returned from Nike API'
            sys.exit(1)
        try:
            run_data = json.loads(response.text)
        except ValueError:
            print 'Problem loading Nike response into JSON'
            sys.exit(1)

    with open(s3_key, 'a') as running_file:
        for run in run_data['data']:
            gps_start, gps_end = get_gps(run['activityId'], access_token)
            if gps_start['latitude'] != 0:
                geo = Geocoder.reverse_geocode(gps_start['latitude'], gps_start['longitude'])
                run['postal'] = geo.postal_code
                run['city'] = geo.city
                run['state'] = geo.state
            else:
                run['postal'] = 'Unknown'
                run['city'] = 'Unknown'
                run['state'] = 'Unknown'
            run['gpsStart'] = gps_start
            run['gpsEnd'] = gps_end
            run['metricSummary']['distance'] = str(float(run['metricSummary']['distance'])
                                                   * KM_TO_MILES)
            json.dump(run, running_file)
            running_file.write('\n')

    with open(s3_key, 'r') as running_file:
        s3_client = boto3.resource('s3')
        s3_client.Bucket(s3_bucket).put_object(Key=s3_key, Body=running_file)

if __name__ == '__main__':
    main()
