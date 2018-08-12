import pathlib
import shutil
import tempfile
import os

from django.conf import settings
from django.test.runner import DiscoverRunner


class LocalStorageDiscoverRunner(DiscoverRunner):
    """
    Use file storage on the local filesystem in unit tests.

    https://gist.github.com/kemar/5f9290cb6843c98d1699
    """

    def setup_test_environment(self):
        super().setup_test_environment()

        # Keep track of original storages.
        settings._original_media_root = settings.MEDIA_ROOT
        settings._original_file_storage = settings.DEFAULT_FILE_STORAGE

        # Creates a temporary directory.
        temp_root = os.path.join(settings.BASE_DIR, ".tmp")
        pathlib.Path(temp_root).mkdir(exist_ok=True)
        settings._temp_media_dir = tempfile.mkdtemp(dir=temp_root)

        # Use the FileSystemStorage for tests.
        settings.MEDIA_ROOT = settings._temp_media_dir
        settings.DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

    def teardown_test_environment(self):
        super().teardown_test_environment()

        # Delete the temporary directory.
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

        # Restore original storage.
        settings.MEDIA_ROOT = settings._original_media_root
        settings.DEFAULT_FILE_STORAGE = settings._original_file_storage

        del settings._original_media_root
        del settings._original_file_storage
