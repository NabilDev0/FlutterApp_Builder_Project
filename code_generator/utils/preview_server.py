import os
import subprocess
import shutil
import threading
import time
import socket
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from django.conf import settings

from ..generators.screen_generator import ScreenGenerator

# How long a preview server can sit idle (no update_screen/heartbeat calls)
# before the reaper kills it, in seconds.
PREVIEW_IDLE_TIMEOUT = getattr(settings, 'PREVIEW_IDLE_TIMEOUT', 10 * 60)
# How often the reaper thread checks for idle previews, in seconds.
PREVIEW_REAP_INTERVAL = getattr(settings, 'PREVIEW_REAP_INTERVAL', 60)
PREVIEW_REQUIRED_JAVASCRIPT_ASSETS = (
    'main.dart.js',
    'main_module.bootstrap.js',
    'web_entrypoint.dart.js',
)
PREVIEW_JAVASCRIPT_CONTENT_TYPES = {
    'application/javascript',
    'application/x-javascript',
    'text/javascript',
}


class PreviewServer:

    def __init__(self, flutter_sdk_path=None, android_sdk_path=None):
        self.flutter_sdk_path = flutter_sdk_path or settings.FLUTTER_SDK_PATH
        self.android_sdk_path = android_sdk_path or getattr(
            settings, 'ANDROID_SDK_PATH', None)
        self.flutter_bin = None  # Lazy initialization
        self.active_servers = {}  # Track running preview servers
        self.preview_states = {}
        self.screen_generator = ScreenGenerator()
        self._lock = threading.Lock()
        self._reaper_started = False

    def _find_flutter_binary(self):
        import platform
        is_windows = platform.system() == 'Windows'

        # Try common locations
        possible_paths = []

        if self.flutter_sdk_path:
            if is_windows:
                possible_paths.append(os.path.join(
                    self.flutter_sdk_path, 'bin', 'flutter.bat'))
                possible_paths.append(os.path.join(
                    self.flutter_sdk_path, 'bin', 'flutter.exe'))
            else:
                possible_paths.append(os.path.join(
                    self.flutter_sdk_path, 'bin', 'flutter'))

        # Also try system PATH
        if is_windows:
            possible_paths.append('flutter.bat')
            possible_paths.append('flutter.exe')

        possible_paths.append('flutter')

        for path in possible_paths:
            found_path = shutil.which(path)
            if found_path:
                return found_path
            if os.path.isfile(path):
                return path

        raise FileNotFoundError(
            f"Flutter SDK not found. Checked paths: {possible_paths}. "
            "Please ensure Flutter is installed and FLUTTER_SDK_PATH is set correctly."
        )

    def _find_free_port(self, start_port=8080, max_attempts=100):
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        raise Exception("No free ports available for preview server")

    def start_preview(self, project_path, port=None, project_id=None):
        project_path = Path(project_path)
        tracking_id = project_id if project_id else str(project_path.name)
        self._stop_active_process(tracking_id)
        self._set_preview_state(
            tracking_id,
            'starting',
            'Preparing Flutter preview',
        )

        process = None
        try:
            # Lazy initialization of Flutter binary
            if self.flutter_bin is None:
                self.flutter_bin = self._find_flutter_binary()

            if not project_path.exists():
                raise FileNotFoundError(
                    f"Project path does not exist: {project_path}")

            if not (project_path / 'pubspec.yaml').exists():
                raise FileNotFoundError(
                    f"Not a valid Flutter project: {project_path}")

            # Find a free port if not specified
            if port is None:
                port = self._find_free_port()

            # Step 1: Get dependencies
            self._set_preview_state(
                tracking_id,
                'getting_dependencies',
                'Getting Flutter dependencies',
            )
            self._run_flutter_command(
                ['pub', 'get'],
                cwd=project_path,
                description="Getting Flutter dependencies"
            )

            # Step 2: Start Flutter web server
            import platform
            is_windows = platform.system() == 'Windows'

            self._set_preview_state(
                tracking_id,
                'compiling',
                'Compiling Flutter web preview',
                port=port,
            )
            process = subprocess.Popen(
                [
                    self.flutter_bin,
                    'run',
                    '--no-pub',
                    '--no-web-experimental-hot-reload',
                    '-d',
                    'web-server',
                    '--web-port',
                    str(port),
                    '--web-hostname',
                    '0.0.0.0',
                ],
                cwd=project_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                shell=is_windows
            )

            output_lines, output_lock = self._capture_process_output(process)
            self._wait_for_preview_ready(
                process,
                port,
                output_lines,
                output_lock,
            )

            # Store server info
            with self._lock:
                self.active_servers[tracking_id] = {
                    'process': process,
                    'port': port,
                    'project_path': str(project_path),
                    'last_active': time.time(),
                    'output_lines': output_lines,
                    'output_lock': output_lock,
                }

            self._ensure_reaper_running()

            preview_url = self._build_preview_url(port)
            self._set_preview_state(
                tracking_id,
                'serving',
                'Compiled Flutter assets are available; waiting for the browser to render.',
                preview_url=preview_url,
                port=port,
            )

            return {
                'status': 'success',
                'preview_status': 'serving',
                'ready': False,
                'preview_url': preview_url,
                'port': port,
                'project_id': tracking_id
            }

        except Exception as e:
            if process is not None and process.poll() is None:
                self._terminate_process(process)
            message = f"Preview server error: {str(e)}"
            self._set_preview_state(
                tracking_id,
                'error',
                'Preview failed to start',
                error=message,
            )
            raise Exception(message)

    def _set_preview_state(
            self, project_id, preview_status, message,
            preview_url=None, port=None, error=None):
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            previous = self.preview_states.get(project_id, {})
            if preview_status == 'starting':
                started_at = now
            elif preview_status == 'stopped':
                started_at = None
            else:
                started_at = previous.get('started_at') or now

            self.preview_states[project_id] = {
                'status': 'success',
                'preview_status': preview_status,
                'ready': False,
                'message': message,
                'preview_url': preview_url,
                'port': port,
                'error': error,
                'started_at': started_at,
                'updated_at': now,
            }

    def get_preview_status(self, project_id):
        with self._lock:
            server_info = self.active_servers.get(project_id)

        if server_info and server_info['process'].poll() is not None:
            with self._lock:
                self.active_servers.pop(project_id, None)
            self._set_preview_state(
                project_id,
                'error',
                'Preview process stopped unexpectedly',
                error='The Flutter preview process is no longer running.',
            )

        with self._lock:
            state = self.preview_states.get(project_id)
            if state:
                return dict(state)

        return {
            'status': 'success',
            'preview_status': 'idle',
            'ready': False,
            'message': 'Preview has not been started',
            'preview_url': None,
            'port': None,
            'error': None,
            'started_at': None,
            'updated_at': None,
        }

    def _capture_process_output(self, process):
        output_lines = deque(maxlen=200)
        output_lock = threading.Lock()

        def drain_output():
            if process.stdout is None:
                return
            for line in iter(process.stdout.readline, ''):
                with output_lock:
                    output_lines.append(line.rstrip())

        thread = threading.Thread(target=drain_output, daemon=True)
        thread.start()
        return output_lines, output_lock

    def _wait_for_preview_ready(
            self, process, port, output_lines, output_lock):
        timeout = getattr(settings, 'PREVIEW_START_TIMEOUT', 120)
        start_time = time.time()

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                details = self._format_output(output_lines, output_lock)
                message = "Preview server exited before the app was ready."
                if details:
                    message = f"{message}\n{details}"
                raise Exception(message)

            # Flutter opens the port before compilation finishes. Waiting for
            # the compiled entrypoint prevents browsers caching an early 404
            # and remaining on a white page.
            if self._is_preview_asset_ready(port):
                return

            time.sleep(0.5)

        details = self._format_output(output_lines, output_lock)
        message = "Preview server timed out while compiling the web app."
        if details:
            message = f"{message}\n{details}"
        raise Exception(message)

    def _is_preview_asset_ready(self, port):
        for asset_name in PREVIEW_REQUIRED_JAVASCRIPT_ASSETS:
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/{asset_name}",
                headers={'Cache-Control': 'no-cache'},
            )
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    content_type = response.headers.get_content_type()
                    if (
                        response.status != 200
                        or content_type not in PREVIEW_JAVASCRIPT_CONTENT_TYPES
                        or not response.read(1)
                    ):
                        return False
            except (urllib.error.URLError, TimeoutError, OSError):
                return False

        return True

    def _format_output(self, output_lines, output_lock):
        with output_lock:
            return '\n'.join(output_lines)

    def _build_preview_url(self, port):

        public_host = getattr(settings, 'PREVIEW_PUBLIC_HOST', None)
        if public_host:
            return f"http://{public_host}:{port}"
        return f"http://localhost:{port}"

    def update_screen(self, project_id, screen_data):

        with self._lock:
            server_info = self.active_servers.get(project_id)

        if not server_info:
            raise Exception(
                f"No active preview server for project {project_id}. "
                "Call start_preview first."
            )

        process = server_info['process']
        if process.poll() is not None:
            # The flutter process died; drop it so callers know to restart.
            with self._lock:
                self.active_servers.pop(project_id, None)
            raise Exception(
                "Preview server is no longer running; restart the preview."
            )

        project_path = Path(server_info['project_path'])
        class_name = self.screen_generator.to_class_name(
            screen_data.get('name', 'Home'))
        screen_file = project_path / 'lib' / \
            'screens' / f'{class_name.lower()}_screen.dart'

        if not screen_file.parent.exists():
            raise Exception(
                f"Screen directory not found in running preview project: {screen_file.parent}"
            )

        code = self.screen_generator.generate_screen(screen_data)
        screen_file.write_text(code, encoding='utf-8')

        try:
            # Experimental web hot reload is disabled because its injected
            # client can crash before Flutter mounts. A hot restart is stable
            # and still updates the existing browser preview.
            process.stdin.write('R\n')
            process.stdin.flush()
        except (BrokenPipeError, ValueError) as e:
            raise Exception(f"Failed to send hot reload signal: {str(e)}")

        with self._lock:
            if project_id in self.active_servers:
                self.active_servers[project_id]['last_active'] = time.time()

        return {
            'status': 'success',
            'reloaded_screen': class_name,
            'reload_mode': 'hot_restart',
        }

    def touch(self, project_id):
        with self._lock:
            if project_id in self.active_servers:
                self.active_servers[project_id]['last_active'] = time.time()
                return True
        return False

    def _ensure_reaper_running(self):
        with self._lock:
            if self._reaper_started:
                return
            self._reaper_started = True
        thread = threading.Thread(target=self._reap_loop, daemon=True)
        thread.start()

    def _reap_loop(self):
        while True:
            time.sleep(PREVIEW_REAP_INTERVAL)
            now = time.time()
            with self._lock:
                idle_ids = [
                    pid for pid, info in self.active_servers.items()
                    if now - info.get('last_active', now) > PREVIEW_IDLE_TIMEOUT
                ]
            for pid in idle_ids:
                try:
                    self.stop_preview(pid)
                except Exception:
                    pass

    def stop_preview(self, project_id):
        success = self._stop_active_process(project_id)
        self._set_preview_state(
            project_id,
            'stopped',
            'Preview has been stopped',
        )
        return success

    def _stop_active_process(self, project_id):
        with self._lock:
            server_info = self.active_servers.pop(project_id, None)

        if not server_info:
            return False

        process = server_info['process']

        self._terminate_process(process)
        return True

    def _terminate_process(self, process):
        try:
            if process.stdin:
                process.stdin.close()
        except Exception:
            pass

        try:
            process.terminate()
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def get_active_previews(self):
        return {
            project_id: {
                'port': info['port'],
                'project_path': info['project_path'],
                'preview_url': self._build_preview_url(info['port']),
                'idle_seconds': round(time.time() - info.get('last_active', time.time())),
            }
            for project_id, info in self.active_servers.items()
        }

    def _run_flutter_command(self, args, cwd, description="Running Flutter command"):
        # Lazy initialization of Flutter binary
        if self.flutter_bin is None:
            self.flutter_bin = self._find_flutter_binary()

        command = [self.flutter_bin] + args

        print(f"{description}...")
        print(f"Command: {' '.join(command)}")

        # Add Android SDK to environment if available
        env = os.environ.copy()
        if self.android_sdk_path:
            env['ANDROID_HOME'] = self.android_sdk_path
            env['ANDROID_SDK_ROOT'] = self.android_sdk_path

        import platform
        is_windows = platform.system() == 'Windows'

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=env,
            shell=is_windows,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            raise subprocess.CalledProcessError(
                result.returncode,
                command,
                output=result.stdout,
                stderr=error_msg
            )

        return result.stdout

    def preview_from_zip(self, zip_path, temp_dir, project_id=None):
        import zipfile

        zip_path = Path(zip_path)

        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        temp_path = Path(temp_dir)
        if project_id:
            self._stop_active_process(project_id)
            self._set_preview_state(
                project_id,
                'starting',
                'Extracting generated Flutter project',
            )
        try:
            if temp_path.exists():
                shutil.rmtree(temp_path)
            temp_path.mkdir(parents=True, exist_ok=True)

            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)

            # Find the project directory
            project_dirs = [
                path.parent
                for path in temp_path.rglob('pubspec.yaml')
                if path.parent.is_dir()
            ]

            if not project_dirs:
                raise Exception("No Flutter project found in ZIP file")

            project_path = min(
                project_dirs,
                key=lambda path: len(path.parts),
            )
        except Exception as e:
            if project_id:
                self._set_preview_state(
                    project_id,
                    'error',
                    'Preview project could not be prepared',
                    error=str(e),
                )
            raise

        # Start preview
        return self.start_preview(project_path, project_id=project_id)


# Global preview server instance
_preview_server_instance = None


def get_preview_server():
    global _preview_server_instance
    if _preview_server_instance is None:
        _preview_server_instance = PreviewServer()
    return _preview_server_instance
