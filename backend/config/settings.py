"""
Django settings for config project.
"""

from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-change-me')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'accounts',
    'repos',
    'chat',
    'contrib',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
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
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Project-specific settings ---

CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:5173', 'http://127.0.0.1:5173'],
)

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # Secure by default: every view requires auth unless it explicitly opts out (register/login).
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Long-lived access token, no refresh-token rotation: this is a small single-user-per-account
# tool, not a high-security app, so we trade a little security for a much simpler frontend (no
# silent-refresh flow — a user just logs in again after a week of inactivity).
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
}

# Chat completions: any OpenAI-compatible API (OpenAI itself, or Groq's OpenAI-compatible
# endpoint). LLM_BASE_URL empty = OpenAI's default endpoint.
LLM_API_KEY = env('LLM_API_KEY', default='')
LLM_BASE_URL = env('LLM_BASE_URL', default='')
LLM_CHAT_MODEL = env('LLM_CHAT_MODEL', default='gpt-4o-mini')

# Embeddings: 'local' (default) runs a free sentence-transformers model on CPU, no API key
# needed. 'openai' uses OpenAI's embeddings API and requires OPENAI_API_KEY (Groq has no
# embeddings endpoint, so it cannot be used here).
EMBEDDING_PROVIDER = env('EMBEDDING_PROVIDER', default='local')
LOCAL_EMBEDDING_MODEL = env('LOCAL_EMBEDDING_MODEL', default='all-MiniLM-L6-v2')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_EMBEDDING_MODEL = env('OPENAI_EMBEDDING_MODEL', default='text-embedding-3-small')

CHROMA_PERSIST_DIR = env('CHROMA_PERSIST_DIR', default=str(BASE_DIR / 'chroma_data'))

GITHUB_TOKEN = env('GITHUB_TOKEN', default='')

# Ingestion tuning
MAX_FILE_SIZE_BYTES = env.int('MAX_FILE_SIZE_BYTES', default=500_000)
CHUNK_LINES = env.int('CHUNK_LINES', default=40)
CHUNK_OVERLAP_LINES = env.int('CHUNK_OVERLAP_LINES', default=5)
MAX_FILES_TO_INDEX = env.int('MAX_FILES_TO_INDEX', default=800)

# Kept conservative so prompts fit under low-TPM free-tier chat rate limits (e.g. Groq's free
# tier is 12,000 tokens/minute, shared across the whole app). Raise these if you're on a paid
# tier or a provider with a higher limit.
# RAG_CANDIDATE_POOL_SIZE is retrieved for free (local embeddings, no LLM call) and then
# diversity-selected down to RAG_TOP_K before it ever reaches the chat model — a wide pool costs
# nothing but meaningfully improves which files actually make it into the prompt.
RAG_CANDIDATE_POOL_SIZE = env.int('RAG_CANDIDATE_POOL_SIZE', default=20)
RAG_TOP_K = env.int('RAG_TOP_K', default=6)
MAX_PR_FILE_SIZE_BYTES = env.int('MAX_PR_FILE_SIZE_BYTES', default=8_000)
