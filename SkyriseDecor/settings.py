from pathlib import Path
import os

# Define the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Quick-start development settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-y*+y4r&@oztgb8!dc=#+k%m+*j357=(!fudn@*h73ri+8t61n=')
DEBUG = True
#ALLOWED_HOSTS = []
ALLOWED_HOSTS = ['127.0.0.1', 'localhost','testserver']

SITE_ID = 2


# Application definition
INSTALLED_APPS = [
    'django_extensions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'adminapp',
    'products',
    'usermanagement',
    'product_cart',
    'wallet',
    'payment',
    'sales_report',
]



# Timezone settings
USE_TZ = True
TIME_ZONE = 'UTC'

# Social account settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
        },
        'OAUTH_PKCE_ENABLED': True,
       
        
    }
}

# In Django admin, set Client ID and Secret Key fields using these environment variables


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
SOCIALACCOUNT_LOGIN_REDIRECT_URL = '/'
#SOCIALACCOUNT_AUTO_SIGNUP = False
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_LOGIN_ON_GET=True

#razorpay

# settings.py
RAZORPAY_KEY_ID = 'rzp_test_EQkCb6St5A2pXy'
RAZORPAY_KEY_SECRET = 'Q97o6aETuZWbaewyNcCwE2gY'


SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    
    
]

ROOT_URLCONF = 'SkyriseDecor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'product_cart.context_processors.cart_count',
                'product_cart.context_processor.wishlist_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'SkyriseDecor.wsgi.application'


# settings.py



# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1200  # 20 minutes
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Authentication backends
AUTHENTICATION_BACKENDS = [
     'django.contrib.auth.backends.ModelBackend',
     'allauth.account.auth_backends.AuthenticationBackend',
     'adminapp.auth_backend.EmailAuthBackend',
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'prad_darsh',
        'USER': 'mysuperuser',
        'PASSWORD': 'mysuperuser',
        'HOST': 'prad-darsh.cj0eo6iqiluo.us-east-2.rds.amazonaws.com',
        'PORT': '5432',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
USE_I18N = True


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'athira174@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'tznr iked zrlw tqyz')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
