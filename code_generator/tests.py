import json
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from .models import Project
from .serializers import ProjectCreateSerializer
from .generators.project_generator import FlutterProjectGenerator


def build_sample_json():
	"""Return minimal yet valid JSON for generation tests."""
	return {
		"app_name": "sample_app",
		"package_name": "com.example.sample",
		"screens": [
			{
				"id": "home",
				"name": "Home",
				"route": "/",
				"is_home": True,
				"components": [
					{
						"type": "Scaffold",
						"children": [
							{
								"type": "AppBar",
								"props": {"title": "Home"}
							},
							{
								"type": "Center",
								"children": [
									{
										"type": "Text",
										"props": {"text": "Hello"}
									}
								]
							}
						]
					}
				]
			}
		]
	}


class ProjectSerializerTests(TestCase):
	def test_project_create_serializer_accepts_valid_payload(self):
		serializer = ProjectCreateSerializer(
			data={
				"name": "Test Project",
				"description": "",
				"json_data": {"screens": []},
			}
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_project_create_serializer_rejects_missing_screens(self):
		serializer = ProjectCreateSerializer(
			data={
				"name": "Broken Project",
				"description": "",
				"json_data": {"invalid": []},
			}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn("json_data", serializer.errors)

	def test_project_create_serializer_requires_dict_json(self):
		serializer = ProjectCreateSerializer(
			data={
				"name": "Broken Project",
				"description": "",
				"json_data": json.dumps({"screens": []}),
			}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn("json_data", serializer.errors)


class FlutterProjectGeneratorTests(TestCase):
	def test_generate_project_creates_zip_with_main_dart(self):
		sample_json = build_sample_json()

		with TemporaryDirectory() as temp_dir:
			generator = FlutterProjectGenerator(
				output_dir=temp_dir,
				app_name="SmokeApp",
				package_name="com.example.smokeapp",
			)

			zip_path = generator.generate_project(sample_json)

			self.assertTrue(Path(zip_path).exists())

			with zipfile.ZipFile(zip_path) as archive:
				members = archive.namelist()
				self.assertIn("smokeapp/lib/main.dart", members)
				self.assertIn("smokeapp/lib/utils/routes.dart", members)


class ProjectAPITests(TestCase):
	def setUp(self):
		super().setUp()
		self.client = APIClient()
		self.user = User.objects.create_user(
			username="apiuser", email="api@example.com", password="strong-pass"
		)
		token, _ = Token.objects.get_or_create(user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

		self.temp_media = TemporaryDirectory()
		self.override = override_settings(MEDIA_ROOT=self.temp_media.name)
		self.override.enable()

		self.sample_json = build_sample_json()

	def tearDown(self):
		self.override.disable()
		self.temp_media.cleanup()
		super().tearDown()

	def test_project_generation_flow(self):
		create_url = reverse("project-list")
		payload = {
			"name": "My Project",
			"description": "Test description",
			"json_data": self.sample_json,
		}

		create_response = self.client.post(create_url, payload, format="json")
		self.assertEqual(create_response.status_code, 201, create_response.json())

		project_id = create_response.json()["id"]

		generate_url = reverse("project-generate", args=[project_id])
		generate_response = self.client.post(generate_url)
		self.assertEqual(generate_response.status_code, 200, generate_response.json())

		project = Project.objects.get(id=project_id)
		self.assertEqual(project.status, "completed")
		self.assertTrue(project.generated_file)

		generated_path = Path(settings.MEDIA_ROOT) / project.generated_file.name
		self.assertTrue(generated_path.exists())

		download_url = reverse("project-download", args=[project_id])
		download_response = self.client.get(download_url)
		self.assertEqual(download_response.status_code, 200)
		self.assertIn("application/zip", download_response["Content-Type"])

		logs_url = reverse("project-logs", args=[project_id])
		logs_response = self.client.get(logs_url)
		self.assertEqual(logs_response.status_code, 200)
		self.assertGreaterEqual(len(logs_response.json().get("logs", [])), 1)

