import os
import unittest
from unittest.mock import patch

from data_source import github


class GithubTests(unittest.TestCase):
    def test_public_fetch_works_without_token(self):
        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"login": "maniz-stha"}

        with patch.dict(os.environ, {}, clear=True), patch("data_source.github.requests.get", return_value=Response()) as get:
            self.assertEqual(github.fetch_profile()["login"], "maniz-stha")
        self.assertNotIn("Authorization", get.call_args.kwargs["headers"])

    def test_language_fetch_failure_stops_refresh(self):
        class Response:
            status_code = 503

            def raise_for_status(self):
                raise RuntimeError("GitHub unavailable")

        with patch("data_source.github.requests.get", return_value=Response()):
            with self.assertRaisesRegex(RuntimeError, "GitHub unavailable"):
                github.fetch_languages("maniz-stha/project")
