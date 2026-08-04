import os
import sys

from django.apps import AppConfig


class ReposConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repos'

    def ready(self):
        # Ingestion runs in its own short-lived process (see services/ingest.py and the
        # run_ingestion management command), which does not survive a server restart. Any
        # repository left in a non-terminal state when the *web* process starts belongs to a
        # process that no longer exists, so mark it failed instead of leaving the frontend
        # polling forever.
        uses_autoreloader = 'runserver' in sys.argv and '--noreload' not in sys.argv
        if uses_autoreloader and os.environ.get('RUN_MAIN') != 'true':
            return  # this is the autoreloader's watcher process, not the one serving requests
        if 'run_ingestion' in sys.argv:
            return  # an ingestion subprocess's own startup — not the long-lived web process

        try:
            from django.db.models import Q
            from .models import Repository

            stale = Repository.objects.filter(
                Q(status='pending') | Q(status='fetching') | Q(status='chunking') | Q(status='embedding')
            )
            count = stale.update(
                status='failed',
                error_message='Ingestion was interrupted by a server restart. Please re-submit this repository.',
            )
            if count:
                print(f'[repos] Reset {count} stale ingestion job(s) left over from a previous run.')
        except Exception:
            pass  # database may not be migrated yet (e.g. during `migrate` itself)
