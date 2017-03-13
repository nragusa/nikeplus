# Nike+ API and Amazon Athena

This is a simple script which uses the Nike+ API to retrieve RUNNING activities, update those activities with GPS coordinates (if applicable), writes the information in a single-line, JSON formatted file, then uploads the file to an S3 bucket of your choice. 

## Getting Started

Before you run the script, ensure you have the following:
* An API access token from Nike+. Technically one should use API keys, but as far as I can tell, these are only open to
[partners](https://developer.nike.com/contact-us.html). To work around this, you can simply [log in](https://developer.nike.com/content/nike-developer-cq/us/en_us/index/login.html), then use something like Chrome developer tools to go to Application -> Storage -> Local Storage -> https://api.nike.com/, and look for the *_access_token key and corresponding value. That will be your short lived access_token to use with this script.
* [Create an S3 bucket](http://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html).
* Ensure you have an appropriate AWS [access_key_id and secret_access_key](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html). Also make sure they are [stored properly](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).

### Prerequisites

Create a python [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/), and use the requirements.txt file to install all the necessary components:

```
pip install -r requirements.txt
```

### Example Usage

To execute the script, you'll need to pass the appropriate token, number of previous runs to capture, S3 bucket, and filename to store the data in. 

The following will grab the latest 3 runs from Nike+, gather GPS data for each of the runs, write the run information to a local file, then upload it to the S3 bucket *myS3Bucket* with a key of *running.json*.

```
./update.py --token iou23jk230sdfkj0a032kljasdf0 --runs 3 --bucket myS3Bucket --key running.json
```

## Optional: Query with Amazon Athena

[Amazon Athena](https://aws.amazon.com/athena/) is an interactive, ad-hoc query service which makes it easy to query data stored in S3 using traditional ANSI SQL like syntax. With this data now stored in a single-line, JSON formatted syntax, you can now query it using Amazon Athena. See the [Getting Started](https://docs.aws.amazon.com/athena/latest/ug/getting-started.html) to get going with Amazon Athena.

Average number of miles by terrain:
```
SELECT count(tag.tagValue) AS count,
         avg(cast(metricSummary.distance AS double)) AS average,
         tag.tagValue
FROM activity.running
CROSS JOIN unnest(tags) AS t(tag)
WHERE tag.tagType = 'TERRAIN'
GROUP BY  tag.tagValue
```

Total miles in 2014:
```
SELECT sum(cast(metricSummary.distance AS double))
FROM activity.running
WHERE starttime > varchar '2014-01-01' and starttime < varchar '2014-12-31';
```

Total miles by shoe:
```
SELECT count(tag.tagValue) AS runs,
         sum(cast(metricSummary.distance AS double)) AS miles,
         tag.tagValue AS shoes
FROM activity.running
CROSS JOIN unnest(tags) AS t(tag)
WHERE tag.tagType = 'SHOES'
GROUP BY  tag.tagValue
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details