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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
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
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

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

# Embeddings: 'local' (default) runs a free ONNX model via fastembed on CPU, no API key
# needed, no torch dependency (kept light for memory-constrained hosts). 'openai' uses
# OpenAI's embeddings API and requires OPENAI_API_KEY (Groq has no embeddings endpoint,
# so it cannot be used here).
EMBEDDING_PROVIDER = env('EMBEDDING_PROVIDER', default='local')
LOCAL_EMBEDDING_MODEL = env('LOCAL_EMBEDDING_MODEL', default='sentence-transformers/all-MiniLM-L6-v2')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_EMBEDDING_MODEL = env('OPENAI_EMBEDDING_MODEL', default='text-embedding-3-small')

CHROMA_PERSIST_DIR = env('CHROMA_PERSIST_DIR', default=str(BASE_DIR / 'chroma_data'))

# Used only by the pgvector backend (vectorstore/pg_backend.py), which is selected
# automatically when DATABASE_URL points at Postgres. Must match the output dimension of
# whichever embedding model is actually active (384 for the default local MiniLM model).
# Changing embedding provider/model in production requires updating this and re-indexing,
# since a pgvector column has a fixed width.
EMBEDDING_DIM = env.int('EMBEDDING_DIM', default=384)

GITHUB_TOKEN = env('GITHUB_TOKEN', default='')

# Password reset emails: defaults to Django's console backend, which just prints the email to
# this server's terminal — works out of the box with zero setup for local development, same
# tradeoff as the optional GITHUB_TOKEN above. Set EMAIL_BACKEND to
# 'django.core.mail.backends.smtp.EmailBackend' plus the EMAIL_HOST_* vars to actually deliver
# real emails in production.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@devinsight.local')

# Optional: sends over Resend's HTTPS API instead of the SMTP settings above. Render's free tier
# blocks outbound SMTP entirely (confirmed via a real "Network is unreachable" error in
# production), but not regular HTTPS, so this is what actually lets password-reset email work
# there. When unset, send_otp_email() falls back to EMAIL_BACKEND above unchanged — local dev
# needs no Resend account at all.
RESEND_API_KEY = env('RESEND_API_KEY', default='')
RESEND_FROM_EMAIL = env('RESEND_FROM_EMAIL', default='DevInsight <onboarding@resend.dev>')

# Ingestion tuning
MAX_FILE_SIZE_BYTES = env.int('MAX_FILE_SIZE_BYTES', default=500_000)
CHUNK_LINES = env.int('CHUNK_LINES', default=40)
CHUNK_OVERLAP_LINES = env.int('CHUNK_OVERLAP_LINES', default=5)
MAX_FILES_TO_INDEX = env.int('MAX_FILES_TO_INDEX', default=800)

# Pre-flight check (repos/services/fetch.fetch_repo_tree), before any download happens: a repo at
# or above either threshold asks the user to pick specific top-level folders to index instead of
# indexing everything. Calibrated against real data: pallets/flask (236 files, ~1.8MB), a repo
# that reliably pushed this app's local-embedding memory usage to the edge of Render's free-tier
# 512MB limit, sits above both thresholds.
MAX_REPO_FILES_BEFORE_SCOPING = env.int('MAX_REPO_FILES_BEFORE_SCOPING', default=150)
MAX_REPO_SIZE_KB_BEFORE_SCOPING = env.int('MAX_REPO_SIZE_KB_BEFORE_SCOPING', default=1000)

# Kept conservative so prompts fit under low-TPM free-tier chat rate limits (e.g. Groq's free
# tier is 12,000 tokens/minute, shared across the whole app). Raise these if you're on a paid
# tier or a provider with a higher limit.
# RAG_CANDIDATE_POOL_SIZE is retrieved for free (local embeddings, no LLM call) and then
# diversity-selected down to RAG_TOP_K before it ever reaches the chat model — a wide pool costs
# nothing but meaningfully improves which files actually make it into the prompt.
RAG_CANDIDATE_POOL_SIZE = env.int('RAG_CANDIDATE_POOL_SIZE', default=20)
RAG_TOP_K = env.int('RAG_TOP_K', default=6)
MAX_PR_FILE_SIZE_BYTES = env.int('MAX_PR_FILE_SIZE_BYTES', default=8_000)
