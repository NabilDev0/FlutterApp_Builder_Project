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


class WidgetGeneratorTests(TestCase):
	def test_container_with_props_width_height(self):
		"""Container should use width and height from props."""
		from code_generator.generators.widget_generator import WidgetGenerator

		generator = WidgetGenerator()
		container_data = {
			"type": "Container",
			"props": {
				"width": 200,
				"height": 100,
				"backgroundColor": "#FF0000",
			},
			"children": [],
		}

		code = generator.generate_container(container_data)
		self.assertIn("width: 200.0", code)
		self.assertIn("height: 100.0", code)
		self.assertIn("Color(0xFFFF0000)", code)

	def test_container_migration_from_layout(self):
		"""Legacy layout w/h should still work as a fallback."""
		from code_generator.generators.widget_generator import WidgetGenerator

		generator = WidgetGenerator()
		container_data = {
			"type": "Container",
			"layout": {"w": 150, "h": 75},
			"props": {"backgroundColor": "#00FF00"},
			"children": [],
		}

		code = generator.generate_container(container_data)
		self.assertIn("width: 150.0", code)
		self.assertIn("height: 75.0", code)
		self.assertIn("Color(0xFF00FF00)", code)

	def test_container_props_override_layout(self):
		"""Props should win when both props and legacy layout dimensions exist."""
		from code_generator.generators.widget_generator import WidgetGenerator

		generator = WidgetGenerator()
		container_data = {
			"type": "Container",
			"layout": {"w": 100, "h": 50},
			"props": {
				"width": 200,
				"height": 150,
				"backgroundColor": "#0000FF",
			},
			"children": [],
		}

		code = generator.generate_container(container_data)
		self.assertIn("width: 200.0", code)
		self.assertIn("height: 150.0", code)
		self.assertNotIn("width: 100.0", code)
		self.assertNotIn("height: 50.0", code)

	def test_container_does_not_mutate_input(self):
		"""Container layout fallback should not mutate the input data."""
		from code_generator.generators.widget_generator import WidgetGenerator

		generator = WidgetGenerator()
		container_data = {
			"type": "Container",
			"layout": {"w": 100, "h": 50},
			"props": {"backgroundColor": "#FF0000"},
			"children": [],
		}
		original_props_keys = set(container_data["props"].keys())

		code = generator.generate_container(container_data)

		self.assertEqual(set(container_data["props"].keys()), original_props_keys)
		self.assertNotIn("width", container_data["props"])
		self.assertNotIn("height", container_data["props"])
		self.assertIn("width: 100.0", code)
		self.assertIn("height: 50.0", code)

	def test_scaffold_body_with_expanded_is_not_scroll_wrapped(self):
		"""Expanded must stay in a bounded Scaffold body."""
		from code_generator.generators.widget_generator import WidgetGenerator

		generator = WidgetGenerator()
		scaffold_data = {
			"type": "Scaffold",
			"children": [
				{
					"type": "Column",
					"children": [
						{"type": "Text", "props": {"text": "Header"}},
						{
							"type": "Expanded",
							"children": [
								{"type": "Container", "props": {"backgroundColor": "#FF0000"}}
							],
						},
					],
				}
			],
		}

		code = generator.generate_widget(scaffold_data)
		self.assertIn("body: Column(", code)
		self.assertIn("Expanded(", code)
		self.assertNotIn("SingleChildScrollView", code)

	def test_auto_scaffold_body_with_expanded_is_not_scroll_wrapped(self):
		"""Auto-created Scaffolds should also keep Expanded bounded."""
		from code_generator.generators.screen_generator import ScreenGenerator

		generator = ScreenGenerator()
		screen_data = {
			"name": "Home",
			"components": [
				{
					"type": "Column",
					"children": [
						{"type": "Text", "props": {"text": "Header"}},
						{
							"type": "Expanded",
							"children": [
								{"type": "Container", "props": {"backgroundColor": "#FF0000"}}
							],
						},
					],
				}
			],
		}

		code = generator.generate_screen(screen_data)
		self.assertIn("body: Column(", code)
		self.assertIn("Expanded(", code)
		self.assertNotIn("SingleChildScrollView", code)

	def test_bottom_navigation_bar_honors_current_index_prop(self):
		"""Explicit currentIndex should not be ignored."""
		from code_generator.generators.widget_generator import WidgetGenerator

		generator = WidgetGenerator()
		bottom_nav_data = {
			"type": "BottomNavigationBar",
			"props": {"currentIndex": 1},
			"items": [
				{"label": "Home", "icon": "home", "route": "/"},
				{"label": "Settings", "icon": "settings", "route": "/settings"},
			],
		}

		code = generator.generate_widget(bottom_nav_data)
		self.assertIn("currentIndex: 1", code)
		self.assertNotIn("currentIndex: ()", code)


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
