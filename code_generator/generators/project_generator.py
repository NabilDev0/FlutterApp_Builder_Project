import os
import shutil
import zipfile
from pathlib import Path
from .screen_generator import ScreenGenerator

# Bump this when generated infrastructure changes without requiring different project JSON.
GENERATOR_CONTRACT_FILENAME = '.draggable-generator-version'
GENERATOR_CONTRACT_VERSION = 'first-frame-ready-v2'


def is_generated_archive_current(zip_path):
    """Reject artifacts whose generated runtime predates the current contract."""
    try:
        with zipfile.ZipFile(zip_path) as archive:
            markers = [
                name for name in archive.namelist()
                if Path(name).name == GENERATOR_CONTRACT_FILENAME
            ]
            if len(markers) != 1:
                return False
            return archive.read(markers[0]).decode('utf-8').strip() == GENERATOR_CONTRACT_VERSION
    except (FileNotFoundError, OSError, UnicodeDecodeError, zipfile.BadZipFile):
        return False


class FlutterProjectGenerator:

    def __init__(self, output_dir, app_name="my_app", package_name="com.example.myapp"):
        self.output_dir = Path(output_dir)
        self.app_name = app_name.lower().replace(' ', '_').replace('-', '_')
        self.package_name = package_name
        self.screen_generator = ScreenGenerator()

    def generate_project(self, json_data):
        try:
            project_path = self.output_dir / self.app_name

            if project_path.exists():
                shutil.rmtree(project_path)

            self.create_structure(project_path)
            self.generate_dart_files(project_path, json_data)
            self.generate_android_official(project_path)
            self.generate_android_icons(project_path)
            self.generate_web_files(project_path)
            self.generate_config_files(project_path)
            self.generate_test_files(project_path)
            (project_path / GENERATOR_CONTRACT_FILENAME).write_text(
                GENERATOR_CONTRACT_VERSION,
                encoding='utf-8',
            )

            zip_path = self.create_zip(project_path)
            return zip_path

        except Exception as e:
            if project_path.exists():
                shutil.rmtree(project_path)
            raise Exception(f"Generation failed: {str(e)}")

    def create_structure(self, project_path):
        dirs = [
            'lib', 'lib/screens', 'lib/utils', 'test', 'web',
            'android/app/src/main/kotlin/' +
            self.package_name.replace('.', '/'),
            'android/app/src/main/res/values',
            'android/app/src/main/res/values-night',
            'android/app/src/main/res/drawable',
            'android/app/src/main/res/drawable-v21',
            'android/app/src/main/res/mipmap-anydpi-v26',
            'android/app/src/main/res/mipmap-hdpi',
            'android/app/src/main/res/mipmap-mdpi',
            'android/app/src/main/res/mipmap-xhdpi',
            'android/app/src/main/res/mipmap-xxhdpi',
            'android/app/src/main/res/mipmap-xxxhdpi',
            'android/app/src/debug/res/values',
            'android/app/src/profile/res/values',
            'android/gradle/wrapper',
            '.idea/libraries',
            '.idea/modules',
            '.vscode',
        ]

        for d in dirs:
            (project_path / d).mkdir(parents=True, exist_ok=True)

    def generate_dart_files(self, project_path, json_data):

        # pubspec.yaml
        pubspec = f"""name: {self.app_name}
description: "A new Flutter project."
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: ^3.5.0

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.8
  web: ^1.1.1

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^5.0.0

flutter:
  uses-material-design: true
"""
        (project_path / 'pubspec.yaml').write_text(pubspec, encoding='utf-8')

        # main.dart
        screens = json_data.get('screens', [json_data.get('screen', {})])
        if not screens or (len(screens) == 1 and not screens[0]):
            screens = [{'name': 'Home', 'is_home': True, 'components': []}]

        home_screen = next(
            (screen for screen in screens if screen.get('is_home') is True),
            screens[0],
        )
        home_class_name = self.screen_generator.to_class_name(
            home_screen.get('name', 'Home'))
        initial_route = home_screen.get('route') or f'/{home_class_name.lower()}'
        initial_route = str(initial_route).replace(
            "\\", "\\\\").replace("'", "\\'").replace('$', '\\$')

        main_dart = f"""import 'package:flutter/material.dart';
import 'utils/live_preview_ready.dart';
import 'utils/routes.dart';

void main() {{
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
  WidgetsBinding.instance.addPostFrameCallback((_) {{
    NotifyLivePreviewReady();
  }});
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      routes: AppRoutes.routes,
      initialRoute: '{initial_route}',
    );
  }}
}}
"""
        (project_path / 'lib/main.dart').write_text(main_dart, encoding='utf-8')

        # The preview server can only prove that compiled assets are being served.
        # The browser receives this signal after Flutter has produced its first frame.
        live_preview_ready = """export 'live_preview_ready_stub.dart'
    if (dart.library.html) 'live_preview_ready_web.dart';
"""
        (project_path / 'lib/utils/live_preview_ready.dart').write_text(
            live_preview_ready,
            encoding='utf-8',
        )

        live_preview_ready_stub = """void NotifyLivePreviewReady() {}
"""
        (project_path / 'lib/utils/live_preview_ready_stub.dart').write_text(
            live_preview_ready_stub,
            encoding='utf-8',
        )

        live_preview_ready_web = """import 'dart:js_interop';
import 'package:web/web.dart' as web;

void NotifyLivePreviewReady() {
  web.window.parent?.postMessage(
    'flutter-preview-ready'.toJS,
    '*'.toJS,
  );
}
"""
        (project_path / 'lib/utils/live_preview_ready_web.dart').write_text(
            live_preview_ready_web,
            encoding='utf-8',
        )

        # Generate screens
        for screen in screens:
            code = self.screen_generator.generate_screen(screen)
            name = self.screen_generator.to_class_name(
                screen.get('name', 'Home'))
            (project_path /
             f'lib/screens/{name.lower()}_screen.dart').write_text(code, encoding='utf-8')

        # routes.dart
        imports = [
            f"import '../screens/{self.screen_generator.to_class_name(s.get('name', 'Home')).lower()}_screen.dart';" for s in screens]

        routes = []
        for s in screens:
            screen_name = s.get('name', 'Home')
            class_name = self.screen_generator.to_class_name(screen_name)
            # Use the route from JSON if provided, otherwise generate one
            route_path = s.get('route')
            if not route_path:
                route_path = '/' + class_name.lower()

            routes.append(
                f"    '{route_path}': (context) => const {class_name}Screen(),")

        routes_dart = f"""import 'package:flutter/material.dart';
{chr(10).join(imports)}

class AppRoutes {{
  static Map<String, WidgetBuilder> routes = {{
{chr(10).join(routes)}
  }};
}}
"""
        (project_path / 'lib/utils/routes.dart').write_text(routes_dart, encoding='utf-8')

    def generate_android_official(self, project_path):

        # build.gradle (project level)
        build_gradle = """buildscript {
    ext.kotlin_version = '2.2.20'
    repositories {
        google()
        mavenCentral()
    }

    dependencies {
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.buildDir = '../build'
subprojects {
    project.buildDir = "${rootProject.buildDir}/${project.name}"
}
subprojects {
    project.evaluationDependsOn(':app')
}

tasks.register("clean", Delete) {
    delete rootProject.buildDir
}
"""
        (project_path / 'android/build.gradle').write_text(build_gradle, encoding='utf-8')

        # settings.gradle
        settings_gradle = """pluginManagement {
    def flutterSdkPath = {
        def properties = new Properties()
        file("local.properties").withInputStream { properties.load(it) }
        def flutterSdkPath = properties.getProperty("flutter.sdk")
        assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
        return flutterSdkPath
    }()

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id "dev.flutter.flutter-plugin-loader" version "1.0.0"
    id "com.android.application" version "8.11.1" apply false
    id "org.jetbrains.kotlin.android" version "2.2.20" apply false
}

include ":app"
"""
        (project_path / 'android/settings.gradle').write_text(settings_gradle, encoding='utf-8')

        # gradle.properties
        gradle_props = """org.gradle.jvmargs=-Xmx4G -XX:MaxMetaspaceSize=2G -XX:+HeapDumpOnOutOfMemoryError
android.useAndroidX=true
android.enableJetifier=true
android.nonTransitiveRClass=false
android.defaults.buildfeatures.buildconfig=true
android.nonFinalResIds=false
"""
        (project_path / 'android/gradle.properties').write_text(gradle_props, encoding='utf-8')

        # gradle-wrapper.properties
        wrapper = """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.14-all.zip
"""
        (project_path / 'android/gradle/wrapper/gradle-wrapper.properties').write_text(wrapper, encoding='utf-8')

        # app/build.gradle
        app_build = f"""plugins {{
    id "com.android.application"
    id "kotlin-android"
    id "dev.flutter.flutter-gradle-plugin"
}}

android {{
    namespace "{self.package_name}"
    compileSdk flutter.compileSdkVersion
    ndkVersion flutter.ndkVersion

    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}

    kotlinOptions {{
        jvmTarget = JavaVersion.VERSION_1_8
    }}

    defaultConfig {{
        applicationId "{self.package_name}"
        minSdk flutter.minSdkVersion
        targetSdk flutter.targetSdkVersion
        versionCode flutter.versionCode
        versionName flutter.versionName
    }}

    buildTypes {{
        release {{
            signingConfig signingConfigs.debug
        }}
    }}
}}

flutter {{
    source "../.."
}}
"""
        (project_path / 'android/app/build.gradle').write_text(app_build, encoding='utf-8')

        # AndroidManifest.xml (main)
        manifest = f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:label="{self.app_name}"
        android:name="${{applicationName}}"
        android:icon="@mipmap/ic_launcher">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:taskAffinity=""
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">
            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme"
              />
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
    <uses-permission android:name="android.permission.INTERNET"/>
</manifest>
"""
        (project_path / 'android/app/src/main/AndroidManifest.xml').write_text(manifest, encoding='utf-8')

    def generate_android_icons(self, project_path):

        # ic_launcher.xml (Adaptive Icon definition)
        ic_launcher_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
"""
        (project_path / 'android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml').write_text(
            ic_launcher_xml, encoding='utf-8')
        (project_path / 'android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml').write_text(
            ic_launcher_xml, encoding='utf-8')

        # ic_launcher_background.xml (Simple background drawable)
        ic_launcher_background = """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#000000"/>
</shape>
"""
        (project_path / 'android/app/src/main/res/drawable/ic_launcher_background.xml').write_text(
            ic_launcher_background, encoding='utf-8')

        # ic_launcher_foreground.xml (Simple foreground drawable - a placeholder circle)
        ic_launcher_foreground = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M54,54m-48,0a48,48 0,1 1,96 0a48,48 0,1 1,-96 0"/>
</vector>
"""
        (project_path / 'android/app/src/main/res/drawable/ic_launcher_foreground.xml').write_text(
            ic_launcher_foreground, encoding='utf-8')

        # AndroidManifest.xml (debug)
        manifest_debug = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET"/>
</manifest>
"""
        (project_path / 'android/app/src/debug/AndroidManifest.xml').write_text(
            manifest_debug, encoding='utf-8')

        # AndroidManifest.xml (profile)
        (project_path / 'android/app/src/profile/AndroidManifest.xml').write_text(
            manifest_debug, encoding='utf-8')

        # MainActivity.kt
        pkg_path = self.package_name.replace('.', '/')
        main_activity = f"""package {self.package_name}

import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity()
"""
        (project_path / f'android/app/src/main/kotlin/{pkg_path}/MainActivity.kt').write_text(
            main_activity, encoding='utf-8')

        # styles.xml
        styles = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="LaunchTheme" parent="@android:style/Theme.Light.NoTitleBar">
        <item name="android:windowBackground">@android:color/white</item>
    </style>
    <style name="NormalTheme" parent="@android:style/Theme.Light.NoTitleBar">
        <item name="android:windowBackground">?android:colorBackground</item>
    </style>
</resources>
"""
        (project_path / 'android/app/src/main/res/values/styles.xml').write_text(styles, encoding='utf-8')

        # styles.xml (night)
        styles_night = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="LaunchTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">@android:color/white</item>
    </style>
    <style name="NormalTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">?android:colorBackground</item>
    </style>
</resources>
"""
        (project_path / 'android/app/src/main/res/values-night/styles.xml').write_text(
            styles_night, encoding='utf-8')

        # launch_background.xml
        launch = """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@android:color/white" />
</layer-list>
"""
        (project_path / 'android/app/src/main/res/drawable/launch_background.xml').write_text(launch, encoding='utf-8')

        # launch_background.xml (v21)
        launch_v21 = """<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="?android:colorBackground" />
</layer-list>
"""
        (project_path / 'android/app/src/main/res/drawable-v21/launch_background.xml').write_text(launch_v21, encoding='utf-8')

        # Debug styles
        debug_styles = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name" translatable="false">{self.app_name}</string>
</resources>
"""
        (project_path / 'android/app/src/debug/res/values/strings.xml').write_text(
            debug_styles, encoding='utf-8')
        (project_path / 'android/app/src/profile/res/values/strings.xml').write_text(
            debug_styles, encoding='utf-8')

    def generate_web_files(self, project_path):
        index_html = f"""<!DOCTYPE html>
<html>
<head>
  <base href="/">
  <meta charset="UTF-8">
  <meta content="IE=Edge" http-equiv="X-UA-Compatible">
  <meta name="description" content="A new Flutter project.">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black">
  <meta name="apple-mobile-web-app-title" content="{self.app_name}">
  <title>{self.app_name}</title>
  <link rel="manifest" href="manifest.json">
</head>
<body>
  <script src="flutter_bootstrap.js" async></script>
</body>
</html>
"""
        (project_path / 'web/index.html').write_text(index_html, encoding='utf-8')

        manifest_json = f"""{{
    "name": "{self.app_name}",
    "short_name": "{self.app_name}",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#ffffff",
    "description": "A new Flutter project.",
    "orientation": "portrait-primary",
    "prefer_related_applications": false,
    "icons": [
        {{
            "src": "icons/Icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        }}
    ]
}}
"""
        (project_path / 'web/manifest.json').write_text(manifest_json, encoding='utf-8')

    def generate_test_files(self, project_path):
        """Generate test files"""
        widget_test = f"""import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:{self.app_name}/main.dart';

void main() {{
  testWidgets('App smoke test', (WidgetTester tester) async {{
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify that the app starts
    expect(find.byType(MaterialApp), findsOneWidget);
  }});
}}
"""
        (project_path / 'test/widget_test.dart').write_text(widget_test, encoding='utf-8')

    def generate_config_files(self, project_path):

        # .metadata (Fixed YAML formatting)
        metadata = """# This file tracks properties of this Flutter project.
# Used by Flutter tool to assess capabilities and perform upgrades etc.

version:
  revision: 5dcb86f68f239346676ceb1ed1ea385bd215fba1
  channel: stable

project_type: app

migration:
  platforms:
    - platform: root
      create_revision: 5dcb86f68f239346676ceb1ed1ea385bd215fba1
      base_revision: 5dcb86f68f239346676ceb1ed1ea385bd215fba1
    - platform: android
      create_revision: 5dcb86f68f239346676ceb1ed1ea385bd215fba1
      base_revision: 5dcb86f68f239346676ceb1ed1ea385bd215fba1
"""
        (project_path / '.metadata').write_text(metadata, encoding='utf-8')

        # .gitignore
        gitignore = """# Miscellaneous
*.class
*.log
*.pyc
*.swp
.DS_Store
.atom/
.buildlog/
.history
.svn/
migrate_working_dir/

# IntelliJ
*.iml
*.ipr
*.iws
.idea/

# VS Code
.vscode/

# Flutter/Dart/Pub
**/doc/api/
**/ios/Flutter/.last_build_id
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.pub-cache/
.pub/
/build/

# Android
/android/app/debug
/android/app/profile
/android/app/release
"""
        (project_path / '.gitignore').write_text(gitignore, encoding='utf-8')

        # analysis_options.yaml
        analysis = """include: package:flutter_lints/flutter.yaml

linter:
  rules:
    prefer_const_constructors: false
"""
        (project_path / 'analysis_options.yaml').write_text(analysis, encoding='utf-8')

        # README.md
        readme = f"""# {self.app_name}

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
"""
        (project_path / 'README.md').write_text(readme, encoding='utf-8')

        # .vscode/settings.json
        vscode = """{
  "java.import.gradle.enabled": false,
  "java.configuration.updateBuildConfiguration": "disabled"
}
"""
        (project_path / '.vscode/settings.json').write_text(vscode, encoding='utf-8')

    def create_zip(self, project_path):
        zip_path = self.output_dir / f"{self.app_name}.zip"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if d not in [
                    'build', '.dart_tool', '.gradle']]
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(project_path.parent)
                    zipf.write(file_path, arcname)

        if not zip_path.exists():
            raise Exception("Zip file creation failed")

        shutil.rmtree(project_path)
        return zip_path
