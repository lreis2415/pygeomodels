from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import httpx

from pygeomodels.api import restapi_post
from pygeomodels.modelCaller import ModelCaller, ModelSubmissionError


class TestModelSubmission(TestCase):
    def setUp(self):
        self.caller = ModelCaller(
            SimpleNamespace(
                modelmanager_url="http://modelmanager.test",
                api_basename="mbms/v1",
                api_cls_usrprj="user-projects",
                api_uprj_single="single-models",
                api_sprj_run="run",
            ),
            {"model-id": {"model_unique_abbr": "demo_model"}},
        )
        self.request = {
            "inputs": {"input": "in.tif"},
            "outputs": {"output": "out.tif"},
            "access_token": "secret-token",
        }

    def test_returns_project_id_for_successful_submission(self):
        with patch(
            "pygeomodels.modelCaller.restapi_post",
            return_value={"success": True, "data": {"project_id": "project-1"}},
        ) as post:
            result = self.caller.demo_model(self.request)

        self.assertEqual(result, "project-1")
        self.assertTrue(post.call_args.kwargs["raise_on_error"])

    def test_reports_backend_business_rejection(self):
        with patch(
            "pygeomodels.modelCaller.restapi_post",
            return_value={
                "success": False,
                "code": "INVALID_PARAMS",
                "message": "Required input is unavailable",
            },
        ):
            with self.assertRaises(ModelSubmissionError) as raised:
                self.caller.demo_model(self.request)

        error = raised.exception
        self.assertFalse(error.success)
        self.assertEqual(error.code, "INVALID_PARAMS")
        self.assertEqual(error.backend_message, "Required input is unavailable")

    def test_reports_http_failure_with_status_code(self):
        request = httpx.Request("POST", "http://modelmanager.test/run")
        response = httpx.Response(422, request=request)
        upstream_error = httpx.HTTPStatusError(
            "unprocessable", request=request, response=response
        )
        with patch(
            "pygeomodels.modelCaller.restapi_post", side_effect=upstream_error
        ):
            with self.assertRaises(ModelSubmissionError) as raised:
                self.caller.demo_model(self.request)

        self.assertEqual(raised.exception.status_code, 422)

    def test_reports_missing_project_id(self):
        with patch(
            "pygeomodels.modelCaller.restapi_post",
            return_value={"success": "true", "data": {}},
        ):
            with self.assertRaises(ModelSubmissionError) as raised:
                self.caller.demo_model(self.request)

        self.assertTrue(raised.exception.success)
        self.assertIn("omitted project_id", str(raised.exception))

    def test_reports_malformed_success_flag(self):
        with patch(
            "pygeomodels.modelCaller.restapi_post",
            return_value={"success": "pending", "message": "Try later"},
        ):
            with self.assertRaises(ModelSubmissionError) as raised:
                self.caller.demo_model(self.request)

        self.assertIsNone(raised.exception.success)
        self.assertEqual(raised.exception.backend_message, "Try later")

    def test_reports_string_false_business_rejection(self):
        with patch(
            "pygeomodels.modelCaller.restapi_post",
            return_value={"success": "false", "code": "REJECTED"},
        ):
            with self.assertRaises(ModelSubmissionError) as raised:
                self.caller.demo_model(self.request)

        self.assertFalse(raised.exception.success)
        self.assertEqual(raised.exception.code, "REJECTED")

    def test_restapi_post_can_reraise_for_model_caller(self):
        with patch(
            "pygeomodels.api.call_inner_api", side_effect=httpx.ConnectError("down")
        ):
            with self.assertRaises(httpx.ConnectError):
                restapi_post(
                    "http://modelmanager.test",
                    "run",
                    {},
                    raise_on_error=True,
                )

    def test_redacts_tokens_from_backend_message(self):
        with patch(
            "pygeomodels.modelCaller.restapi_post",
            return_value={
                "success": False,
                "message": "Bearer secret-token access_token=another-secret",
            },
        ):
            with self.assertRaises(ModelSubmissionError) as raised:
                self.caller.demo_model(self.request)

        message = str(raised.exception)
        self.assertNotIn("secret-token", message)
        self.assertNotIn("another-secret", message)
        self.assertIn("[REDACTED]", message)
