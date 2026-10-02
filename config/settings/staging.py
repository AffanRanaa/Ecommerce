from .base import *
from decouple import config

DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in config('ALLOWED_HOSTS', default='').split(',')
    if host.strip()
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Stripe TEST keys for staging/evaluator deployment
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Vercel serves the application over HTTPS.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Supabase Storage
# Used only in staging/deployment. Local development continues
# using Django's normal local filesystem storage.
AWS_ACCESS_KEY_ID = config('SUPABASE_S3_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('SUPABASE_S3_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('SUPABASE_STORAGE_BUCKET', default='media')

AWS_S3_ENDPOINT_URL = config('SUPABASE_S3_ENDPOINT')
AWS_S3_REGION_NAME = config('SUPABASE_S3_REGION')
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_S3_SIGNATURE_VERSION = 's3v4'

# Files are publicly readable because the Supabase "media"
# bucket is configured as a public bucket.
AWS_QUERYSTRING_AUTH = False

# Prevent overwriting an existing uploaded file with the same name.
AWS_S3_FILE_OVERWRITE = False

# Generate browser-facing URLs through Supabase's public
# Storage URL instead of the S3 API endpoint.
SUPABASE_PROJECT_URL = config('SUPABASE_PROJECT_URL')

AWS_S3_CUSTOM_DOMAIN = (
    f'{SUPABASE_PROJECT_URL.removeprefix("https://").removeprefix("http://")}'
    f'/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}'
)

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
