"""
Client for connecting to AWS S3.
"""

import boto3


class S3Client:
    """
    Client for connecting to AWS S3.
    """

    def __init__(self):
        pass

    def get_enterprise_report(self, report_name, file_handler):
        """
        Download a report file from S3
        report_name <string>: name of the report on S3
        file_handler <file>: file object opened in binary mode
        """
        bucket_name = 'edx-enterprise-reporting'
        s3 = boto3.client('s3')
        s3.download_fileobj(bucket_name, report_name, file_handler)
