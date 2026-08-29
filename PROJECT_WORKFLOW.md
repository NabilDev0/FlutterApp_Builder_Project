# Project Workflow and Code Generation

This project is a Django REST API that accepts a JSON description of a mobile app and generates a complete Flutter project ZIP. It can also save projects for authenticated users, download generated ZIP files, start a Flutter web preview, and build Android APK files when Flutter and Android tooling are available on the host machine.

## Main Pieces

| Area | Files | Purpose |
| :--- | :--- | :--- |
| Django project config | `backend/settings.py`, `backend/urls.py` | Configures Django, REST Framework, Swagger docs, media storage, and routes `/api/` to the app. |
| API app | `code_generator/` | Contains models, serializers, views, routes, tests, and generation logic. |
| Project storage | `code_generator/models.py` | Stores projects, legacy screen records, reusable components, generated ZIP/APK paths, preview URLs, logs, and pollable jobs. |
| API views | `code_generator/views.py` | Handles project CRUD, generation, download, preview, APK build, auth, and component endpoints. |
| Flutter generation | `code_generator/generators/` | Converts project JSON into Flutter source files and packages them into a ZIP. |
| Preview support | `code_generator/utils/preview_server.py` | Extracts a generated ZIP and runs `flutter run -d web-server`. |
| APK build support | `code_generator/utils/apk_builder.py` | Extracts a generated ZIP and runs `flutter build apk --release`. |

## API Entry Points

The root URL config exposes the backend under `/api/`.

| Endpoint | Purpose |
| :--- | :--- |
| `POST /api/auth/register/` | Create a user and return an auth token. |
| `POST /api/auth/login/` | Login and return an auth token. |
| `POST /api/auth/logout/` | Delete the current user's auth token. |
| `GET /api/projects/` | List the authenticated user's projects. |
| `POST /api/projects/` | Save a project JSON payload. |
| `POST /api/projects/{id}/generate/` | Queue Flutter ZIP generation; returns `202` and a job. |
| `GET /api/projects/{id}/jobs/` | List the project's queued, running, completed, and failed jobs. |
| `GET /api/projects/{id}/jobs/{job_id}/` | Poll one background job. |
| `GET /api/projects/{id}/download/` | Download the generated Flutter ZIP. |
| `POST /api/projects/{id}/start_preview/` | Queue live-preview startup; returns `202` and a job. |
| `GET /api/projects/{id}/preview_status/` | Poll preview launch progress and readiness. |
| `POST /api/projects/{id}/stop_preview/` | Stop the running preview. |
| `POST /api/projects/{id}/update_preview/` | Temporarily rewrite one preview screen and hot restart. |
| `POST /api/projects/{id}/build_apk/` | Queue a release APK build; returns `202` and a job. |
| `GET /api/projects/{id}/download_apk/` | Download the built APK. |
| `POST /api/generate/quick_generate/` | Generate and download a ZIP directly from JSON without saving a project. |

## Project JSON Shape

The backend expects `json_data` to be a dictionary containing either `screens` or `screen`.

```json
{
  "screens": [
    {
      "id": "home",
      "name": "Home",
      "route": "/",
      "is_home": true,
      "components": [
        {
          "type": "Scaffold",
          "children": [
            {
              "type": "AppBar",
              "props": { "title": "My App" }
            },
            {
              "type": "Center",
              "children": [
                {
                  "type": "Text",
                  "props": { "text": "Hello World" }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

Each component normally has:

| Field | Meaning |
| :--- | :--- |
| `type` | Flutter-like widget name, such as `Text`, `Container`, `Column`, or `Button`. |
| `props` | Widget properties used by the generator. |
| `children` | Nested child components for layout widgets. |
| `items` | Used by `BottomNavigationBar`. |
| `itemTemplate` | Used by `ListView`. |

Supported component names and props are listed in `README.md`.

## Save and Generate Flow

1. The frontend sends project data to `POST /api/projects/`.
2. `ProjectCreateSerializer` validates the complete widget tree against the generator contract.
3. `ProjectViewSet.perform_create()` saves the project with the authenticated user.
4. The frontend calls `POST /api/projects/{id}/generate/` and receives `202 Accepted` with a job ID.
5. The frontend polls `GET /api/projects/{id}/jobs/{job_id}/` until the job is `completed` or `failed`.
6. A bounded background worker builds the project under a unique project/job directory in `MEDIA_ROOT/projects`.
7. The generated project folder is zipped.
8. The temporary project folder is deleted.
9. The project model stores the ZIP path in `generated_file` and sets status to `completed`.
10. The frontend downloads it from `GET /api/projects/{id}/download/`.

## Quick Generate Flow

`POST /api/generate/quick_generate/` skips database storage.

1. The request body includes `json_data`, optional `app_name`, and optional `package_name`.
2. The backend creates a unique directory under `MEDIA_ROOT/temp`.
3. `FlutterProjectGenerator` creates and zips the Flutter project.
4. The response streams the ZIP file directly.

This is useful for quick frontend testing because no authenticated project record is required.

## How Flutter Code Generation Works

## Source of Truth for Screens

`Project.json_data` is the only source used for project generation. The current
`update_preview` endpoint is an intentionally temporary preview-only edit: it
does not write the submitted screen back to `Project.json_data`. The `Screen`
model is legacy storage and is not merged into a project's JSON.

The generation pipeline has three layers:

1. `FlutterProjectGenerator`
2. `ScreenGenerator`
3. `WidgetGenerator`

### 1. FlutterProjectGenerator

`code_generator/generators/project_generator.py` is responsible for creating the complete Flutter project.

It does the following:

1. Creates folders such as `lib/`, `lib/screens/`, `lib/utils/`, `android/`, `web/`, and `test/`.
2. Writes `pubspec.yaml`.
3. Writes `lib/main.dart`.
4. Generates one Dart screen file per screen JSON item.
5. Writes `lib/utils/routes.dart`.
6. Writes Android Gradle, manifest, Kotlin activity, launcher icon, and style files.
7. Writes web files such as `web/index.html` and `web/manifest.json`.
8. Writes Flutter config files such as `.metadata`, `.gitignore`, and `analysis_options.yaml`.
9. Writes a simple widget smoke test.
10. Zips the project folder and deletes the temporary folder.

The ZIP contains one top-level project folder, for example:

```text
my_app/
  pubspec.yaml
  lib/
    main.dart
    screens/
    utils/routes.dart
  android/
  web/
  test/
```

### 2. ScreenGenerator

`code_generator/generators/screen_generator.py` turns each screen JSON object into a Dart screen file.

For a screen named `Home`, it generates:

```dart
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}
```

Then it builds the widget tree in `build(BuildContext context)`.

If the JSON already includes a `Scaffold`, it uses that scaffold. If not, it creates one automatically and puts the provided components in the body.

Special screen-level handling:

| Component | Behavior |
| :--- | :--- |
| `AppBar` | Moved into `Scaffold.appBar`. |
| `BottomNavigationBar` | Moved into `Scaffold.bottomNavigationBar`. |
| `Drawer` | Moved into `Scaffold.drawer`. |
| `ListView` | Used directly as a scrollable body. |
| Other body content | Usually wrapped in `SingleChildScrollView` to reduce overflow errors. |
| Body containing `Expanded` | Kept directly in a bounded `Scaffold.body` so Flutter does not throw unbounded height errors. |

### 3. WidgetGenerator

`code_generator/generators/widget_generator.py` converts each component dictionary into Dart widget code.

Example input:

```json
{
  "type": "Text",
  "props": {
    "text": "Hello",
    "fontSize": 24,
    "color": "#2196F3"
  }
}
```

Generated Dart shape:

```dart
Text(
  'Hello',
  style: TextStyle(
    fontSize: 24,
    color: Color(0xFF2196F3),
  ),
)
```

The dispatcher is `generate_widget()`. It checks the component `type`, validates the child rules, and calls the matching generator method, such as:

| Component type | Generator method |
| :--- | :--- |
| `Text` | `generate_text()` |
| `Container` | `generate_container()` |
| `Row` | `generate_row()` |
| `Column` | `generate_column()` |
| `Button` | `generate_button()` |
| `Image` | `generate_image()` |
| `AppBar` | `generate_appbar()` |
| `Scaffold` | `generate_scaffold()` |
| `ListView` | `generate_listview()` |
| `BottomNavigationBar` | `generate_bottom_navigation_bar()` |
| `Drawer` | `generate_drawer()` |

Unknown component types generate a placeholder `Container()` with a TODO comment.

## Child Rules

The generator validates how children are used before writing Dart code.

| Rule | Components |
| :--- | :--- |
| One child | `Container`, `Center`, `Padding`, `Expanded`, `SizedBox`, `Positioned`, `Card` |
| Multiple children | `Row`, `Column`, `Stack` |
| No children | `Text`, `Image`, `Icon`, `TextField`, `Button`, `ListTile` |
| Special structure | `Scaffold`, `AppBar`, `BottomNavigationBar`, `Drawer`, `ListView` |

If a one-child widget receives multiple children, generation raises a validation error telling the caller to wrap the children in a `Column` or `Row`.

## Actions

Buttons and some interactive widgets can use an `actions` array.

Supported action types:

| Action | Generated behavior |
| :--- | :--- |
| `snackbar` | Calls `ScaffoldMessenger.of(context).showSnackBar(...)`. |
| `dialog` | Calls `showDialog(...)` with an `AlertDialog`. |
| `navigate` | Calls `Navigator.pushNamed(context, route)`. |
| `goBack` | Calls `Navigator.pop(context)`. |

Example:

```json
{
  "type": "Button",
  "props": {
    "text": "Open Details",
    "actions": [
      { "type": "navigate", "route": "/details" }
    ]
  }
}
```

## Routes

Routes are generated in `lib/utils/routes.dart`.

For each screen:

1. The screen name becomes a Dart class name, such as `HomeScreen`.
2. The route uses `screen.route` if provided.
3. If no route is provided, the generator creates one from the class name.

Example:

```dart
class AppRoutes {
  static Map<String, WidgetBuilder> routes = {
    '/': (context) => const HomeScreen(),
    '/details': (context) => const DetailsScreen(),
  };
}
```

## Live Preview Flow

Live preview is implemented in `code_generator/utils/preview_server.py`.

1. `POST /api/projects/{id}/start_preview/` queues startup and returns `202 Accepted` with a `GenerationJob`.
2. The worker checks the generated ZIP's contract marker and regenerates stale or missing artifacts before extracting them under `MEDIA_ROOT/previews/{project_id}`.
3. It finds the generated Flutter project folder and runs `flutter pub get`.
4. It starts:

```bash
flutter run --no-pub --no-web-experimental-hot-reload \
  -d web-server --web-port <port> --web-hostname 0.0.0.0
```

5. The backend drains Flutter output so the process cannot block on full output pipes.
6. It waits for the complete JavaScript bootstrap chain: `main.dart.js`, `main_module.bootstrap.js`, and `web_entrypoint.dart.js`. Every file must have a JavaScript MIME type because the development server returns `index.html` with HTTP 200 for module paths that do not exist yet.
7. It reports `serving` with a URL like `http://localhost:8080`. The generated Flutter app then notifies its iframe parent after its first frame; only that browser signal proves a screen is visible.

Experimental web hot reload is disabled because its injected browser client can crash before the Flutter app mounts on the tested Linux Flutter installation. Preview updates use Flutter hot restart instead.

### Preview Readiness

First poll the returned job until it is `completed` or `failed`:

```http
GET /api/projects/{id}/jobs/{job_id}/
Authorization: Token <token>
```

While that job is running, the frontend can also poll the detailed preview phase:

```http
GET /api/projects/{id}/preview_status/
Authorization: Token <token>
```

Example response:

```json
{
  "status": "success",
  "preview_status": "compiling",
  "ready": false,
  "message": "Compiling Flutter web preview",
  "preview_url": null,
  "port": 8080,
  "error": null,
  "started_at": "2026-07-27T06:00:00+00:00",
  "updated_at": "2026-07-27T06:00:05+00:00"
}
```

`preview_status` can be:

| Value | Client behavior |
| :--- | :--- |
| `idle` | Startup has not reached the backend yet; keep polling while the start request is pending. |
| `starting` | Show that the generated ZIP is being prepared. |
| `getting_dependencies` | Show dependency installation progress. |
| `compiling` | Keep the loading state visible. Do not mount the iframe yet. |
| `serving` | Mount the iframe with `preview_url`, then wait for the generated Flutter app's first-frame message before marking the preview interactive. |
| `error` | Stop polling and show `error` or `message`. |
| `stopped` | Show the preview as inactive. |

The client should treat `serving` as the authoritative server-asset state. Poll every second while startup is pending, stop polling for `serving`, `error`, or an explicitly requested `stopped` state, and assign the iframe `src` only after `serving` returns its URL. The generated Flutter app posts `flutter-preview-ready` after its first frame; that message is the authoritative interactive state.

Preview update flow:

1. Frontend calls `POST /api/projects/{id}/update_preview/` with a `screen` object.
2. The backend regenerates only that extracted preview screen file; the database JSON is unchanged.
3. It sends `R` to the Flutter process stdin.
4. Flutter hot restarts the running preview.

Preview cleanup:

| Mechanism | Behavior |
| :--- | :--- |
| `stop_preview` | Terminates the Flutter process. |
| `preview_heartbeat` | Updates last activity timestamp. |
| Reaper thread | Stops idle previews after `PREVIEW_IDLE_TIMEOUT`. |

Starting a preview again stops the previous process for that project and replaces its extracted preview folder.

## APK Build Flow

APK building is implemented in `code_generator/utils/apk_builder.py`.

1. The project must already have a generated ZIP.
2. `build_apk_from_zip()` extracts the ZIP into a temporary directory.
3. It finds the generated Flutter project folder.
4. It runs `flutter pub get`.
5. It runs:

```bash
flutter build apk --release
```

6. It expects the APK at:

```text
build/app/outputs/flutter-apk/app-release.apk
```

7. It copies the APK into `MEDIA_ROOT/apks`.
8. The project model stores that path in `apk_file`.

## Linux Support

The project is intended to work on Linux as long as Python, Flutter, Java, and Android tooling are installed.

Important Linux behavior:

| Area | Linux behavior |
| :--- | :--- |
| File paths | The code uses `pathlib.Path` and `os.path`, so normal Linux paths work. |
| Flutter binary lookup | Looks for `settings.FLUTTER_SDK_PATH/bin/flutter`, then falls back to `flutter` on PATH. |
| Subprocesses | Uses `shell=False` on Linux, which is the correct default. |
| Live preview | Starts Flutter web server on `0.0.0.0`, returns `localhost` unless `PREVIEW_PUBLIC_HOST` is configured. |
| APK build | Requires Android SDK and Java to be correctly installed. |

Useful environment variables:

```bash
export FLUTTER_SDK_PATH=/path/to/flutter
export ANDROID_HOME=/path/to/android/sdk
export ANDROID_SDK_ROOT=/path/to/android/sdk
export JAVA_HOME=/path/to/java
```

## Current Limitations

| Limitation | Details |
| :--- | :--- |
| Original JSON is not embedded in ZIP | The database stores `project.json_data`, but the generated Flutter ZIP does not include a separate JSON file with the original project schema. |
| Preview state is process-local | Preview status, process handles, and hot-restart input are kept in memory, so multi-worker deployments need shared preview coordination. |
| Preview job and phase polling are separate | Startup is tracked by `GenerationJob`; detailed `preview_status` is a separate process-local state machine. |
| Preview updates are temporary | `update_preview` changes the extracted Dart file only; regenerate or restart from a ZIP to discard it. |
| Preview folders can accumulate | Stopping preview kills the process but does not delete extracted preview folders. |
| Quick generate files can accumulate | Quick-generated ZIPs are stored under `MEDIA_ROOT/temp` and are not automatically cleaned here. |
| Flutter/Android versions matter | APK build depends on the host Flutter, Java, Gradle, and Android SDK setup. |
| Unknown widgets become placeholders | Unsupported component types generate `Container()` with a TODO comment. |

## Testing

Run the backend test suite with:

```bash
venv/bin/python manage.py test code_generator --verbosity=2
```

The tests cover:

1. Project serializer validation.
2. Flutter project ZIP generation.
3. Authenticated project generation/download/log flow.
4. Container width and height behavior.
5. `Expanded` layout safety in generated scaffolds.
6. `BottomNavigationBar.currentIndex` behavior.

For deeper Linux verification, generate a ZIP and run Flutter commands inside the extracted project:

```bash
flutter test
flutter run -d web-server --web-port 8080 --web-hostname 0.0.0.0
flutter build apk --release
```
