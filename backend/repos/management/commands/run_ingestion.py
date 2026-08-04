from django.core.management.base import BaseCommand, CommandError

from repos.models import Repository
from repos.services.ingest import run_ingestion


class Command(BaseCommand):
    help = (
        'Runs the fetch/chunk/embed/store pipeline for one repository. Invoked as its own '
        'subprocess (see repos/views.py:_start_ingestion) so ingestion gets a fresh memory '
        'baseline instead of running inside the long-lived web process, which accumulates '
        'memory from ordinary request handling over its lifetime.'
    )

    def add_arguments(self, parser):
        parser.add_argument('repo_id', type=int)

    def handle(self, *args, **options):
        try:
            repository = Repository.objects.get(id=options['repo_id'])
        except Repository.DoesNotExist:
            raise CommandError(f'Repository {options["repo_id"]} does not exist')

        run_ingestion(repository)
