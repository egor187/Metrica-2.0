from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Custom storage class to serve uploaded by users media file on AWS S3
    """
    location = 'media'
    file_overwrite = False
