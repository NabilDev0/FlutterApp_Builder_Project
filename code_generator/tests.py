import io
import json
import subprocess
import threading
import zipfile
from collections import deque
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from .models import Project, Component, GenerationJob
from .jobs import run_job
from .serializers import ProjectCreateSerializer
from .generators.project_generator import FlutterProjectGenerator
from .generators.widget_generator import WidgetGenerator
from .utils.preview_server import PreviewServer


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


class PreviewServerTests(TestCase):
	def test_unknown_preview_status_is_idle(self):
		result = PreviewServer().get_preview_status("not-started")

		self.assertEqual(result["preview_status"], "idle")
		self.assertFalse(result["ready"])
		self.assertIsNone(result["preview_url"])

	def test_start_preview_waits_for_compiled_app_without_experimental_hot_reload(self):
		with TemporaryDirectory() as temp_dir:
			project_path = Path(temp_dir)
			(project_path / "pubspec.yaml").write_text(
				"name: preview_test\n",
				encoding="utf-8",
			)

			process = Mock()
			process.poll.return_value = None
			process.stdout = io.StringIO("")
			process.stdin = Mock()

			server = PreviewServer()
			server.flutter_bin = "/usr/bin/flutter"
			observed_statuses = []

			def record_dependencies(*args, **kwargs):
				observed_statuses.append(
					server.get_preview_status("project-1")["preview_status"]
				)

			def record_compilation(*args, **kwargs):
				observed_statuses.append(
					server.get_preview_status("project-1")["preview_status"]
				)

			with (
				patch("code_generator.utils.preview_server.subprocess.Popen", return_value=process) as popen,
				patch.object(server, "_run_flutter_command", side_effect=record_dependencies),
				patch.object(server, "_find_free_port", return_value=8123),
				patch.object(
					server,
					"_wait_for_preview_ready",
					side_effect=record_compilation,
				) as wait_for_ready,
			):
				result = server.start_preview(
					project_path,
					project_id="project-1",
				)

			command = popen.call_args.args[0]
			self.assertIn("--no-web-experimental-hot-reload", command)
			self.assertIn("--no-pub", command)
			self.assertEqual(popen.call_args.kwargs["stderr"], subprocess.STDOUT)
			wait_for_ready.assert_called_once()
			self.assertEqual(result["preview_url"], "http://localhost:8123")
			self.assertEqual(result["preview_status"], "ready")
			self.assertTrue(result["ready"])
			self.assertEqual(
				observed_statuses,
				["getting_dependencies", "compiling"],
			)
			self.assertEqual(
				server.get_preview_status("project-1")["preview_status"],
				"ready",
			)

			server.stop_preview("project-1")
			stopped = server.get_preview_status("project-1")
			self.assertEqual(stopped["preview_status"], "stopped")
			self.assertFalse(stopped["ready"])

	def test_failed_preview_reports_error_status(self):
		with TemporaryDirectory() as temp_dir:
			project_path = Path(temp_dir)
			(project_path / "pubspec.yaml").write_text(
				"name: preview_test\n",
				encoding="utf-8",
			)

			server = PreviewServer()
			server.flutter_bin = "/usr/bin/flutter"
			with (
				patch.object(server, "_find_free_port", return_value=8123),
				patch.object(
					server,
					"_run_flutter_command",
					side_effect=RuntimeError("pub get failed"),
				),
				self.assertRaisesRegex(Exception, "pub get failed"),
			):
				server.start_preview(project_path, project_id="project-1")

			result = server.get_preview_status("project-1")
			self.assertEqual(result["preview_status"], "error")
			self.assertFalse(result["ready"])
			self.assertIn("pub get failed", result["error"])

	def test_wait_for_preview_ready_checks_compiled_entrypoint(self):
		server = PreviewServer()
		process = Mock()
		process.poll.return_value = None
		output_lines = deque()
		output_lock = threading.Lock()

		with (
			patch.object(
				server,
				"_is_preview_asset_ready",
				side_effect=[False, True],
			) as is_ready,
			patch("code_generator.utils.preview_server.time.sleep"),
		):
			server._wait_for_preview_ready(
				process,
				8123,
				output_lines,
				output_lock,
			)

		self.assertEqual(is_ready.call_count, 2)

	def test_update_screen_uses_hot_restart(self):
		with TemporaryDirectory() as temp_dir:
			project_path = Path(temp_dir)
			(project_path / "lib" / "screens").mkdir(parents=True)

			process = Mock()
			process.poll.return_value = None
			process.stdin = Mock()

			server = PreviewServer()
			server.active_servers["project-1"] = {
				"process": process,
				"port": 8123,
				"project_path": str(project_path),
				"last_active": 0,
			}

			with patch.object(
				server.screen_generator,
				"generate_screen",
				return_value="// generated screen",
			):
				result = server.update_screen(
					"project-1",
					{"name": "Home", "components": []},
				)

			process.stdin.write.assert_called_once_with("R\n")
			process.stdin.flush.assert_called_once()
			self.assertEqual(
				(project_path / "lib" / "screens" / "home_screen.dart").read_text(
					encoding="utf-8",
				),
				"// generated screen",
			)
			self.assertEqual(result["reload_mode"], "hot_restart")

	def test_preview_from_zip_replaces_stale_extracted_project(self):
		with TemporaryDirectory() as temp_dir:
			temp_path = Path(temp_dir)
			extract_path = temp_path / "preview"
			extract_path.mkdir()
			(extract_path / "stale.txt").write_text("old", encoding="utf-8")

			zip_path = temp_path / "project.zip"
			with zipfile.ZipFile(zip_path, "w") as archive:
				archive.writestr("flutter_app/pubspec.yaml", "name: flutter_app\n")
				archive.writestr("flutter_app/lib/main.dart", "void main() {}\n")

			server = PreviewServer()
			with (
				patch.object(server, "_stop_active_process") as stop_preview,
				patch.object(
					server,
					"start_preview",
					return_value={"status": "success"},
				) as start_preview,
			):
				result = server.preview_from_zip(
					zip_path,
					extract_path,
					project_id="project-1",
				)

			stop_preview.assert_called_once_with("project-1")
			self.assertFalse((extract_path / "stale.txt").exists())
			start_preview.assert_called_once_with(
				extract_path / "flutter_app",
				project_id="project-1",
			)
			self.assertEqual(result, {"status": "success"})


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


class ComponentAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username="component-owner", password="strong-pass"
		)
		self.other_user = User.objects.create_user(
			username="other-component-user", password="strong-pass"
		)
		token, _ = Token.objects.get_or_create(user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

	def component_payload(self, **overrides):
		payload = {
			"name": "Reusable heading",
			"description": "A heading used on several screens.",
			"template_json": {
				"type": "Padding",
				"props": {"padding": 16},
				"children": [{"type": "Text", "props": {"text": "Heading"}}],
			},
		}
		payload.update(overrides)
		return payload

	def test_available_components_match_widget_generator_contract(self):
		response = self.client.get(reverse("component-available"))

		self.assertEqual(response.status_code, 200, response.json())
		components = response.json()["components"]
		by_type = {component["type"]: component for component in components}
		self.assertEqual(set(by_type), set(WidgetGenerator().widget_rules))
		self.assertEqual(by_type["Container"]["child_rule"], "child")
		self.assertIn("width", {prop["name"] for prop in by_type["Container"]["props"]})
		self.assertEqual(by_type["ListView"]["fields"][0]["name"], "itemTemplate")

	def test_user_can_create_list_update_and_delete_own_custom_component(self):
		create_response = self.client.post(
			reverse("component-list"), self.component_payload(), format="json"
		)

		self.assertEqual(create_response.status_code, 201, create_response.json())
		component_id = create_response.json()["id"]
		self.assertEqual(create_response.json()["type"], "custom")
		self.assertNotIn("is_public", create_response.json())
		self.assertEqual(create_response.json()["created_by"], self.user.pk)

		list_response = self.client.get(reverse("component-list"))
		self.assertEqual(list_response.status_code, 200, list_response.json())
		self.assertEqual(
			{item["id"] for item in list_response.json()},
			{str(component_id)},
		)

		detail_url = reverse("component-detail", args=[component_id])
		update_response = self.client.patch(
			detail_url, {"name": "Updated heading"}, format="json"
		)
		self.assertEqual(update_response.status_code, 200, update_response.json())
		self.assertEqual(update_response.json()["name"], "Updated heading")

		delete_response = self.client.delete(detail_url)
		self.assertEqual(delete_response.status_code, 204)
		self.assertFalse(Component.objects.filter(id=component_id).exists())

	def test_user_cannot_see_or_change_another_users_custom_component(self):
		component = Component.objects.create(
			name="Private card",
			type="custom",
			template_json={"type": "Card", "children": []},
			created_by=self.other_user,
		)

		self.assertEqual(
			self.client.get(reverse("component-detail", args=[component.id])).status_code,
			404,
		)
		self.assertEqual(
			self.client.patch(
				reverse("component-detail", args=[component.id]),
				{"name": "Stolen"}, format="json",
			).status_code,
			404,
		)

	def test_custom_component_template_must_use_supported_generator_components(self):
		response = self.client.post(
			reverse("component-list"),
			self.component_payload(template_json={"type": "UnsupportedWidget"}),
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("not supported by the code generator", str(response.json()))


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
		with patch("code_generator.jobs._executor.submit"):
			generate_response = self.client.post(generate_url)
		self.assertEqual(generate_response.status_code, 202, generate_response.json())
		job_id = generate_response.json()["id"]
		self.assertEqual(generate_response.json()["status"], "queued")
		run_job(job_id)
		self.assertEqual(GenerationJob.objects.get(id=job_id).status, "completed")

		project = Project.objects.get(id=project_id)
		self.assertEqual(project.status, "completed")
		self.assertTrue(project.generated_file)

		generated_path = Path(settings.MEDIA_ROOT) / project.generated_file.name
		self.assertTrue(generated_path.exists())
		self.assertIn(str(project_id), project.generated_file.name)
		self.assertIn(str(job_id), project.generated_file.name)

		job_response = self.client.get(
			reverse("project-job-status", args=[project_id, job_id])
		)
		self.assertEqual(job_response.status_code, 200, job_response.json())
		self.assertEqual(job_response.json()["status"], "completed")

		download_url = reverse("project-download", args=[project_id])
		download_response = self.client.get(download_url)
		self.assertEqual(download_response.status_code, 200)
		self.assertIn("application/zip", download_response["Content-Type"])

		logs_url = reverse("project-logs", args=[project_id])
		logs_response = self.client.get(logs_url)
		self.assertEqual(logs_response.status_code, 200)
		self.assertGreaterEqual(len(logs_response.json().get("logs", [])), 1)

	def test_preview_status_endpoint_returns_client_ready_state(self):
		project = Project.objects.create(
			user=self.user,
			name="Preview Project",
			json_data=self.sample_json,
			status="completed",
		)
		preview_server = Mock()
		preview_server.get_preview_status.return_value = {
			"status": "success",
			"preview_status": "ready",
			"ready": True,
			"message": "Preview is ready to interact with",
			"preview_url": "http://localhost:8080",
			"port": 8080,
			"error": None,
			"started_at": "2026-07-27T06:00:00+00:00",
			"updated_at": "2026-07-27T06:00:20+00:00",
		}

		with patch(
			"code_generator.views.get_preview_server",
			return_value=preview_server,
		):
			response = self.client.get(
				reverse("project-preview-status", args=[project.id])
			)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["preview_status"], "ready")
		self.assertTrue(response.json()["ready"])
		self.assertEqual(
			response.json()["preview_url"],
			"http://localhost:8080",
		)
		preview_server.get_preview_status.assert_called_once_with(
			str(project.id)
		)

	def test_project_api_rejects_unsupported_component_tree(self):
		response = self.client.post(
			reverse("project-list"),
			{
				"name": "Invalid app",
				"json_data": {"screens": [{"name": "Home", "components": [{"type": "NotAWidget"}]}]},
			},
			format="json",
		)
		self.assertEqual(response.status_code, 400)
		self.assertIn("not supported by the code generator", str(response.json()))

	@override_settings(MAX_QUEUED_JOBS_PER_USER=1, MAX_ACTIVE_JOBS_PER_USER=1)
	def test_generation_jobs_are_rate_limited_and_project_scoped(self):
		project = Project.objects.create(
			user=self.user, name="Queued", json_data=self.sample_json,
		)
		generate_url = reverse("project-generate", args=[project.id])
		with patch("code_generator.jobs._executor.submit"):
			first = self.client.post(generate_url)
			second = self.client.post(generate_url)

		self.assertEqual(first.status_code, 202, first.json())
		self.assertEqual(second.status_code, 429, second.json())
		jobs_response = self.client.get(reverse("project-jobs", args=[project.id]))
		self.assertEqual(jobs_response.status_code, 200, jobs_response.json())
		self.assertEqual(len(jobs_response.json()), 1)
