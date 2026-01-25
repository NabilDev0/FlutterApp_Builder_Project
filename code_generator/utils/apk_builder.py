import os
import subprocess
import shutil
from pathlib import Path
from django.conf import settings


class APKBuilder:

    def __init__(self, flutter_sdk_path=None, android_sdk_path=None, java_home=None):
        self.flutter_sdk_path = flutter_sdk_path or settings.FLUTTER_SDK_PATH
        self.android_sdk_path = android_sdk_path or getattr(
            settings, 'ANDROID_SDK_PATH', None)
        self.java_home = java_home or getattr(settings, 'JAVA_HOME', None)
        self.flutter_bin = None  # Lazy initialization

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

    def build_apk(self, project_path, output_dir=None):

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
            # Step 1: Get dependencies
            self._run_flutter_command(
                ['pub', 'get'],
                cwd=project_path,
                description="Getting Flutter dependencies"
            )

            # Step 2: Build APK
            self._run_flutter_command(
                ['build', 'apk', '--release'],
                cwd=project_path,
                description="Building APK"
            )

            # Step 3: Locate the built APK
            apk_path = project_path / 'build' / 'app' / \
                'outputs' / 'flutter-apk' / 'app-release.apk'

            if not apk_path.exists():
                raise FileNotFoundError(
                    f"APK file not found at expected location: {apk_path}")

            # Step 4: Copy to output directory if specified
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                app_name = project_path.name
                output_apk = output_dir / f"{app_name}.apk"
                shutil.copy2(apk_path, output_apk)
                return output_apk

            return apk_path

        except subprocess.CalledProcessError as e:
            raise Exception(
                f"Flutter build failed: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        except Exception as e:
            raise Exception(f"APK build error: {str(e)}")

    def _run_flutter_command(self, args, cwd, description="Running Flutter command"):

        # Lazy initialization of Flutter binary
        if self.flutter_bin is None:
            self.flutter_bin = self._find_flutter_binary()

        command = [self.flutter_bin] + args

        print(f"{description}...")
        print(f"Command: {' '.join(command)}")

        # Add Android SDK and Java Home to environment if available
        env = os.environ.copy()
        if self.android_sdk_path:
            env['ANDROID_HOME'] = self.android_sdk_path
            env['ANDROID_SDK_ROOT'] = self.android_sdk_path
        if self.java_home:
            env['JAVA_HOME'] = self.java_home

        import platform
        is_windows = platform.system() == 'Windows'

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=env,
            shell=is_windows,
            timeout=600  # 10 minute timeout
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

    def build_apk_from_zip(self, zip_path, output_dir):

        import zipfile
        import tempfile

        zip_path = Path(zip_path)

        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)

            # Find the project directory (it should be the first directory in the ZIP)
            project_dirs = [d for d in temp_path.iterdir() if d.is_dir()]

            if not project_dirs:
                raise Exception("No project directory found in ZIP file")

            project_path = project_dirs[0]

            # Build APK
            apk_path = self.build_apk(project_path, output_dir)

            return apk_path
