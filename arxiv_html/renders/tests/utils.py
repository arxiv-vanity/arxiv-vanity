from django.conf import settings
import shutil
import os


TEST_MEDIA_ROOT = os.path.join(settings.BASE_DIR, "media-test")


class TempMediaRootMixin(object):
    def setUp(self):
        self._MEDIA_ROOT = settings.MEDIA_ROOT
        self._DEFAULT_FILE_STORAGE = settings.DEFAULT_FILE_STORAGE
        settings.MEDIA_ROOT = TEST_MEDIA_ROOT
        settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
        settings.MEDIA_ROOT = self._MEDIA_ROOT
        settings.DEFAULT_FILE_STORAGE = self._DEFAULT_FILE_STORAGE
