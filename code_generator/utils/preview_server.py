import os
import subprocess
import shutil
import threading
import time
import socket
from pathlib import Path
from django.conf import settings


class PreviewServer:

    def __init__(self, flutter_sdk_path=None, android_sdk_path=None):
        self.flutter_sdk_path = flutter_sdk_path or settings.FLUTTER_SDK_PATH
        self.android_sdk_path = android_sdk_path or getattr(
            settings, 'ANDROID_SDK_PATH', None)
        self.flutter_bin = None  # Lazy initialization
        self.active_servers = {}  # Track running preview servers

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
        # Lazy initialization of Flutter binary
        if self.flutter_bin is None:
            self.flutter_bin = self._find_flutter_binary()

        project_path = Path(project_path)

        if not project_path.exists():
            raise FileNotFoundError(
                f"Project path does not exist: {project_path}")

        if not (project_path / 'pubspec.yaml').exists():
            raise FileNotFoundError(
                f"Not a valid Flutter project: {project_path}")

        try:
            # Find a free port if not specified
            if port is None:
                port = self._find_free_port()

            # Step 1: Get dependencies
            self._run_flutter_command(
                ['pub', 'get'],
                cwd=project_path,
                description="Getting Flutter dependencies"
            )

            # Step 2: Start Flutter web server
            import platform
            is_windows = platform.system() == 'Windows'

            process = subprocess.Popen(
                [self.flutter_bin, 'run', '-d', 'web-server',
                    '--web-port', str(port), '--web-hostname', '0.0.0.0'],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=is_windows
            )

            # Wait for server to start (check for "Running on" message)
            start_time = time.time()
            timeout = 120  # 2 minutes timeout
            server_started = False

            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    # Process ended unexpectedly
                    stdout, stderr = process.communicate()
                    raise Exception(
                        f"Preview server failed to start: {stderr}")

                # Check if server is responding
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        s.connect(('localhost', port))
                        server_started = True
                        break
                except (socket.timeout, ConnectionRefusedError):
                    time.sleep(2)

            if not server_started:
                process.terminate()
                raise Exception("Preview server timed out while starting")

            # Store server info
            tracking_id = project_id if project_id else str(project_path.name)
            self.active_servers[tracking_id] = {
                'process': process,
                'port': port,
                'project_path': str(project_path)
            }

            preview_url = f"http://localhost:{port}"

            return {
                'status': 'success',
                'preview_url': preview_url,
                'port': port,
                'project_id': tracking_id
            }

        except Exception as e:
            raise Exception(f"Preview server error: {str(e)}")

    def stop_preview(self, project_id):
        if project_id not in self.active_servers:
            return False

        server_info = self.active_servers[project_id]
        process = server_info['process']

        try:
            process.terminate()
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

        del self.active_servers[project_id]
        return True

    def get_active_previews(self):
        return {
            project_id: {
                'port': info['port'],
                'project_path': info['project_path'],
                'preview_url': f"http://localhost:{info['port']}"
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
        temp_path.mkdir(parents=True, exist_ok=True)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_path)

        # Find the project directory
        project_dirs = [d for d in temp_path.iterdir() if d.is_dir()]

        if not project_dirs:
            raise Exception("No project directory found in ZIP file")

        project_path = project_dirs[0]

        # Start preview
        return self.start_preview(project_path, project_id=project_id)


# Global preview server instance
_preview_server_instance = None


def get_preview_server():
    global _preview_server_instance
    if _preview_server_instance is None:
        _preview_server_instance = PreviewServer()
    return _preview_server_instance
