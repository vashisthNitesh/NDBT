import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'django-insecure-ndbt-lorry-register-dev-key'),
    ALLOWED_HOSTS=(list, ['*']),
)

env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['https://*.onrender.com', 'https://*.localhost', 'http://127.0.0.1', 'http://localhost'])

# Application definition
INSTALLED_APPS = [
    # Django Unfold (must come before django.contrib.admin)
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.import_export',
    'unfold.contrib.simple_history',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'import_export',
    'simple_history',
    'django_otp',
    'django_otp.plugins.otp_totp',

    # Local apps
    'register.apps.RegisterConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')
}
DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True

# Use fast SQLite in-memory database during test runs
import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
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
LANGUAGE_CODE = 'en-in'
TIME_ZONE = env('TIME_ZONE', default='Asia/Kolkata')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage' if not ('test' in sys.argv or DEBUG) else 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Unfold Configuration
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    'SITE_TITLE': 'NDBT Lorry Register',
    'SITE_HEADER': 'NDBT Transport Portal',
    'SITE_SYMBOL': 'local_shipping',
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': False,
    'THEME': 'light',
    'BORDER_RADIUS': '8px',
    'DASHBOARD_CALLBACK': 'register.views.dashboard_callback',
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': _('Operations'),
                'separator': True,
                'collapsible': False,
                'items': [
                    {
                        'title': _('Trip Register (LR)'),
                        'icon': 'local_shipping',
                        'link': reverse_lazy('admin:register_trip_changelist'),
                    },
                    {
                        'title': _('Customer Receipts'),
                        'icon': 'payments',
                        'link': reverse_lazy('admin:register_receipt_changelist'),
                    },
                    {
                        'title': _('Owner Payments'),
                        'icon': 'account_balance_wallet',
                        'link': reverse_lazy('admin:register_ownerpayment_changelist'),
                    },
                    {
                        'title': _('Documents & POD'),
                        'icon': 'description',
                        'link': reverse_lazy('admin:register_tripdocument_changelist'),
                    },
                ],
            },
            {
                'title': _('Reports & Analytics'),
                'separator': True,
                'collapsible': False,
                'items': [
                    {
                        'title': _('Party Outstanding'),
                        'icon': 'pending_actions',
                        'link': reverse_lazy('admin:customer_outstanding_report'),
                    },
                    {
                        'title': _('Transporter Payable'),
                        'icon': 'request_quote',
                        'link': reverse_lazy('admin:transporter_payable_report'),
                    },
                    {
                        'title': _('TDS Register (194C)'),
                        'icon': 'receipt_long',
                        'link': reverse_lazy('admin:tds_register_report'),
                    },
                    {
                        'title': _('Monthly Summary'),
                        'icon': 'analytics',
                        'link': reverse_lazy('admin:monthly_summary_report'),
                    },
                    {
                        'title': _('Pending Operations'),
                        'icon': 'warning',
                        'link': reverse_lazy('admin:pending_work_report'),
                    },
                ],
            },
            {
                'title': _('Master Data'),
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': _('Customers (Consignors)'),
                        'icon': 'business',
                        'link': reverse_lazy('admin:register_customer_changelist'),
                    },
                    {
                        'title': _('Transporters (Owners)'),
                        'icon': 'directions_bus',
                        'link': reverse_lazy('admin:register_transporter_changelist'),
                    },
                    {
                        'title': _('Vehicles (Lorries)'),
                        'icon': 'rv_hookup',
                        'link': reverse_lazy('admin:register_vehicle_changelist'),
                    },
                    {
                        'title': _('Vehicle Types'),
                        'icon': 'category',
                        'link': reverse_lazy('admin:register_vehicletype_changelist'),
                    },
                    {
                        'title': _('Locations / Hubs'),
                        'icon': 'location_on',
                        'link': reverse_lazy('admin:register_location_changelist'),
                    },
                    {
                        'title': _('Lanes / Routes'),
                        'icon': 'alt_route',
                        'link': reverse_lazy('admin:register_lane_changelist'),
                    },
                ],
            },
            {
                'title': _('Administration'),
                'separator': True,
                'collapsible': True,
                'items': [
                    {
                        'title': _('User Accounts'),
                        'icon': 'person',
                        'link': reverse_lazy('admin:auth_user_changelist'),
                    },
                    {
                        'title': _('User Groups & Roles'),
                        'icon': 'group',
                        'link': reverse_lazy('admin:auth_group_changelist'),
                    },
                ],
            },
        ],
    },
}

