# Flutter Builder - Django Backend

A Django REST API backend that generates complete Flutter mobile applications from JSON specifications

## Requirements

- Python 3.11+
- Django 5.1+
- Django REST Framework

## Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/NabilDev0/FlutterApp_Builder_Project.git
    cd flutter_builder_project
    ```

2.  **Create virtual environment**

    ```bash
    python -m venv venv
    #then use this command to activate the env EVERYTIME you open the project
    venv/Scripts/activate
    ```

3.  **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run migrations**

    ```bash
    python manage.py migrate
    ```

5.  **Start development server**

    ```bash
    python manage.py runserver
    ```

The API will be available at `http://localhost:8000/`

## API Documentation

### Swagger UI

The interactive API documentation, powered by Swagger UI, is available at the following URL:

**Swagger UI URL:** `http://localhost:8000/api/swagger/`

Use this interface to explore all available endpoints, view required parameters, and test API calls directly.

### Authentication

The API uses **Token-based Authentication** via Django REST Framework's `TokenAuthentication`. All project management endpoints (`/api/projects/`, `/api/screens/`, etc.) require a valid token.

#### 1. Register a New User

| Method | Endpoint              | Description                                             |
| :----- | :-------------------- | :------------------------------------------------------ |
| `POST` | `/api/auth/register/` | Creates a new user and returns an authentication token. |

**Request Body Example:**

```json
{
  "username": "testuser",
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Response Body (JSON structure with token):**

```json
{
  "token": "a4b5c6d7e8f901234567890abcdef01234567890",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "user@example.com"
  }
}
```

#### 2. Login and Get Token

| Method | Endpoint           | Description                                            |
| :----- | :----------------- | :----------------------------------------------------- |
| `POST` | `/api/auth/login/` | Authenticates a user and returns their existing token. |

**Request Body Example:**

```json
{
  "username": "testuser",
  "password": "strongpassword123"
}
```

#### 3. Logout

| Method | Endpoint            | Description                                     |
| :----- | :------------------ | :---------------------------------------------- |
| `POST` | `/api/auth/logout/` | Invalidates the user's token and logs them out. |

**Authorization Required:** Token authentication

#### 4. Using the Token

For all authenticated requests, include the token in the `Authorization` header:

```
Authorization: Token a4b5c6d7e8f901234567890abcdef01234567890
```

### Quick Generate (No Database)

Generate and download a Flutter app without saving to database for quick testing:

```bash
POST /api/generate/quick_generate/
Content-Type: application/json

{
  "app_name": "my_app",
  "package_name": "com.example.myapp",
  "json_data": {
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
                "props": {
                  "title": "My App"
                }
              },
              {
                "type": "Center",
                "children": [
                  {
                    "type": "Text",
                    "props": {
                      "text": "Hello World!",
                      "fontSize": 24
                    }
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Response:** ZIP file download containing complete Flutter project

### Save and Generate (Authenticated)

This flow is for authenticated users to save, manage, and generate projects.

1.  **Create Project**

    ```bash
    POST /api/projects/
    Authorization: Token <your_token>
    {
      "name": "My App",
      "description": "A test application",
      "json_data": { ... }
    }
    ```

2.  **List All Projects**

    ```bash
    GET /api/projects/
    Authorization: Token <your_token>
    ```

3.  **Get Project Details**

    ```bash
    GET /api/projects/{id}/
    Authorization: Token <your_token>
    ```

4.  **Update Project**

    ```bash
    PUT /api/projects/{id}/
    Authorization: Token <your_token>
    {
      "name": "Updated App Name",
      "description": "Updated description",
      "json_data": { ... }
    }
    ```

5.  **Delete Project**

    ```bash
    DELETE /api/projects/{id}/
    Authorization: Token <your_token>
    ```

## Flutter Code Generation Workflow

### Step 1: Generate Flutter Project Code

```bash
POST /api/projects/{id}/generate/
Authorization: Token <your_token>
```

**Response:**

```json
{
  "status": "success",
  "message": "Project generated successfully",
  "download_url": "/api/projects/{id}/download/"
}
```

**Project Status Flow:**

- Initial status: `draft`
- During generation: `generating`
- After success: `completed`
- On error: `failed`

**Monitor Generation Progress:**

```bash
GET /api/projects/{id}/logs/
Authorization: Token <your_token>
```

**Download Generated Project:**

```bash
GET /api/projects/{id}/download/
Authorization: Token <your_token>
```

Returns a ZIP file containing the complete Flutter project with:

- `lib/` - Dart source files (main.dart, screens, routes)
- `android/` - Android configuration and build files
- `web/` - Web platform files
- `pubspec.yaml` - Flutter dependencies
- All necessary configuration files

---

### Step 2: Build APK (Android Application Package)

After the Flutter project is generated, build the APK for Android deployment.

**Prerequisites:**

- Flutter SDK must be installed on the server
- Android SDK must be configured
- Project status must be `completed` (code generation finished)

```bash
POST /api/projects/{id}/build_apk/
Authorization: Token <your_token>
```

**Response:**

```json
{
  "status": "success",
  "message": "APK built successfully",
  "download_url": "/api/projects/{id}/download_apk/"
}
```

**APK Build Process:**

1. Extract the generated Flutter project ZIP
2. Run `flutter pub get` - Download dependencies
3. Run `flutter build apk --release` - Build release APK
4. APK saved to `media/apks/` directory

**Monitor APK Build Progress:**

```bash
GET /api/projects/{id}/logs/
Authorization: Token <your_token>
```

**Download Built APK:**

```bash
GET /api/projects/{id}/download_apk/
Authorization: Token <your_token>
```

Returns the APK file ready for installation on Android devices.

**APK Build Time:** Typically 5-15 minutes depending on project complexity and server resources.

---

### Step 3: Live Preview Server

Start a live preview server to test the generated Flutter app in a browser environment.

**Prerequisites:**

- Project status must be `completed` (code generation finished)
- Flutter SDK must be installed on the server

```bash
POST /api/projects/{id}/start_preview/
Authorization: Token <your_token>
```

**Response:**

```json
{
  "status": "success",
  "message": "Preview server started successfully",
  "preview_url": "http://localhost:8080/",
  "port": 8080
}
```

**Access the Preview:**

- Open the `preview_url` in a web browser
- The app will run in web mode (Flutter Web)
- All interactive features work in the preview

**View Active Previews:**

```bash
GET /api/projects/active_previews/
Authorization: Token <your_token>
```

**Stop Preview Server:**

```bash
POST /api/projects/{id}/stop_preview/
Authorization: Token <your_token>
```

**Response:**

```json
{
  "status": "success",
  "message": "Preview server stopped successfully"
}
```

---

## Complete Workflow Example

```bash
# 1. Register/Login
POST /api/auth/login/
{
  "username": "testuser",
  "password": "password123"
}
# Response: { "token": "abc123..." }

# 2. Create Project
POST /api/projects/
Authorization: Token abc123...
{
  "name": "My Flutter App",
  "description": "Test application",
  "json_data": { ... }
}
# Response: { "id": "project-uuid", ... }

# 3. Generate Code
POST /api/projects/project-uuid/generate/
Authorization: Token abc123...
# Wait for status to become "completed"

# 4. Download Generated Project
GET /api/projects/project-uuid/download/
Authorization: Token abc123...
# Returns: my_flutter_app.zip

# 5. Build APK
POST /api/projects/project-uuid/build_apk/
Authorization: Token abc123...
# Wait for APK build to complete

# 6. Download APK
GET /api/projects/project-uuid/download_apk/
Authorization: Token abc123...
# Returns: my_flutter_app.apk

# 7. (Optional) Start Live Preview
POST /api/projects/project-uuid/start_preview/
Authorization: Token abc123...
# Response includes preview_url to access in browser
```

## Supported Widgets and Props Reference

This section details all supported widgets and their corresponding properties (`props`) that can be used in the `json_data` payload.

### Layout & Structure Widgets

| Widget Type    | Supported Props                                                                                                                                                                            | Description                                                                                                                         |
| :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| **Scaffold**   | `backgroundColor` (hex color)                                                                                                                                                              | The basic structure for a visual interface. Automatically handles `AppBar` and `body` from children.                                |
| **AppBar**     | `title` (string), `backgroundColor` (hex color), `elevation` (number), `centerTitle` (boolean)                                                                                             | The top bar of the application. Must be a direct child of `Scaffold`.                                                               |
| **Container**  | `backgroundColor` (hex color), `padding` (number), `margin` (number), `borderRadius` (number), `border` (boolean), `borderColor` (hex color), `borderWidth` (number), `alignment` (string) | A convenience widget that combines common painting, positioning, and sizing widgets.                                                |
| **Row**        | `mainAxisAlignment` (string), `crossAxisAlignment` (string), `mainAxisSize` (string)                                                                                                       | Arranges children horizontally. `mainAxisAlignment` values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`. |
| **Column**     | `mainAxisAlignment` (string), `crossAxisAlignment` (string), `mainAxisSize` (string)                                                                                                       | Arranges children vertically. `mainAxisAlignment` values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`.   |
| **Stack**      | None                                                                                                                                                                                       | Arranges children on top of each other. Children can be wrapped in `Positioned`.                                                    |
| **Positioned** | `top` (number), `bottom` (number), `left` (number), `right` (number), `width` (number), `height` (number)                                                                                  | Used only inside a `Stack` to position its child absolutely.                                                                        |
| **Expanded**   | `flex` (number, default 1)                                                                                                                                                                 | Used inside `Row` or `Column` to expand a child to fill the available space.                                                        |
| **SizedBox**   | `width` (number), `height` (number)                                                                                                                                                        | Creates a box with a specified size. Useful for adding space.                                                                       |
| **Padding**    | `padding` (number, default 8)                                                                                                                                                              | Adds uniform padding around its child.                                                                                              |
| **Center**     | None                                                                                                                                                                                       | Centers its child within itself.                                                                                                    |
| **Card**       | `elevation` (number, default 1), `color` (hex color), `margin` (number), `borderRadius` (number)                                                                                           | A material design card with rounded corners and a shadow.                                                                           |
| **ListView**   | `itemCount` (number, default 10), `padding` (number), `shrinkWrap` (boolean)                                                                                                               | Creates a scrollable list of items. Requires an `itemTemplate` field instead of `children`.                                         |

### Content & Input Widgets

| Widget Type   | Supported Props                                                                                                                                                                                                         | Description                                                                                                                                 |
| :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------ |
| **Text**      | `text` (string), `fontSize` (number), `color` (hex color), `fontWeight` (string), `fontStyle` (string), `letterSpacing` (number), `decoration` (string), `alignment` (string), `maxLines` (number), `overflow` (string) | Displays a string of text. `fontWeight` values: `normal`, `bold`. `alignment` values: `left`, `right`, `center`, `justify`, `start`, `end`. |
| **Button**    | `text` (string), `backgroundColor` (hex color), `color` (hex color), `elevation` (number), `borderRadius` (number), **`actions` (array)**                                                                               | An `ElevatedButton`. **The `actions` array is the standard for defining button behavior (see Action Chaining below).**                      |
| **TextField** | `hintText` (string), `labelText` (string), `obscureText` (boolean), `keyboardType` (string), `border` (boolean), `prefixIcon` (string)                                                                                  | A text input field with customizable appearance and behavior.                                                                               |
| **Icon**      | `icon` (string), `size` (number), `color` (hex color)                                                                                                                                                                   | Displays a Material Design icon. `icon` should be the icon name (e.g., `person`, `star`, `arrow_forward_ios`).                              |
| **Image**     | `src` (string), `fit` (string), `width` (number), `height` (number)                                                                                                                                                     | Displays an image from network URL or asset path. Automatically detects source type.                                                        |

## JSON Schema

### Complete Example

```json
{
  "app_name": "my_app",
  "package_name": "com.example.myapp",
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
              "props": {
                "title": "Home Screen",
                "backgroundColor": "#6200EE"
              }
            },
            {
              "type": "Center",
              "children": [
                {
                  "type": "Column",
                  "props": {
                    "mainAxisAlignment": "center"
                  },
                  "children": [
                    {
                      "type": "Text",
                      "props": {
                        "text": "Welcome!",
                        "fontSize": 24,
                        "fontWeight": "bold"
                      }
                    },
                    {
                      "type": "SizedBox",
                      "props": {
                        "height": 20
                      }
                    },
                    {
                      "type": "Button",
                      "props": {
                        "text": "Go to Profile",
                        "actions": [
                          {
                            "type": "navigate",
                            "route": "/profile"
                          }
                        ]
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "profile",
      "name": "Profile",
      "route": "/profile",
      "is_home": false,
      "components": [
        {
          "type": "Scaffold",
          "children": [
            {
              "type": "AppBar",
              "props": {
                "title": "Profile Screen"
              }
            },
            {
              "type": "Center",
              "children": [
                {
                  "type": "Text",
                  "props": {
                    "text": "User Profile Details",
                    "fontSize": 20
                  }
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

### Widget Props Reference

The following examples illustrate the usage of the `props` field for all 18 supported widgets.

#### 1. Text

| Prop            | Type      | Description                                                                                   |
| :-------------- | :-------- | :-------------------------------------------------------------------------------------------- |
| `text`          | string    | The content of the text widget.                                                               |
| `fontSize`      | number    | The size of the font.                                                                         |
| `color`         | hex color | The color of the text (e.g., `#FF0000`).                                                      |
| `fontWeight`    | string    | The weight of the font. Values: `normal`, `bold`.                                             |
| `fontStyle`     | string    | The style of the font. Values: `normal`, `italic`.                                            |
| `letterSpacing` | number    | The spacing between letters.                                                                  |
| `decoration`    | string    | Text decoration. Values: `underline`, `lineThrough`, `overline`.                              |
| `alignment`     | string    | How the text should be aligned. Values: `left`, `right`, `center`, `justify`, `start`, `end`. |
| `maxLines`      | number    | Maximum number of lines to display.                                                           |
| `overflow`      | string    | How to handle text overflow. Values: `ellipsis`, `clip`, `fade`.                              |

```json
{
  "type": "Text",
  "props": {
    "text": "Hello World",
    "fontSize": 20,
    "color": "#FF0000",
    "fontWeight": "bold",
    "fontStyle": "italic",
    "letterSpacing": 1.5,
    "decoration": "underline",
    "alignment": "center",
    "maxLines": 2,
    "overflow": "ellipsis"
  }
}
```

#### 2. Button

| Prop              | Type      | Description                                   |
| :---------------- | :-------- | :-------------------------------------------- |
| `text`            | string    | The text displayed on the button.             |
| `backgroundColor` | hex color | The background color of the button.           |
| `color`           | hex color | The text color of the button.                 |
| `elevation`       | number    | The shadow depth of the button.               |
| `borderRadius`    | number    | The border radius for rounded corners.        |
| `actions`         | array     | A list of action objects to execute in order. |

#### Button Action Types

| Type       | Config Parameters  | Description                                                      |
| ---------- | ------------------ | ---------------------------------------------------------------- |
| `snackbar` | `message`          | Shows a non-blocking snackbar message.                           |
| `dialog`   | `title`, `message` | Shows a blocking alert dialog. Subsequent actions wait for "OK". |
| `navigate` | `route`            | Navigates to a new screen.                                       |
| `goBack`   | None               | Navigates back to the previous screen.                           |

```json
{
  "type": "Button",
  "props": {
    "text": "Complete Profile",
    "backgroundColor": "#2196F3",
    "color": "#FFFFFF",
    "elevation": 4,
    "borderRadius": 8,
    "actions": [
      { "type": "snackbar", "message": "Saving data..." },
      {
        "type": "dialog",
        "title": "Success",
        "message": "Your profile has been updated."
      },
      { "type": "navigate", "route": "/profile" }
    ]
  }
}
```

#### 3. TextField

| Prop           | Type    | Description                                                                    |
| :------------- | :------ | :----------------------------------------------------------------------------- |
| `hintText`     | string  | Placeholder text displayed in the field.                                       |
| `labelText`    | string  | Label text displayed above the field.                                          |
| `obscureText`  | boolean | Whether to hide the input (for passwords). Default: `false`.                   |
| `keyboardType` | string  | Type of keyboard to display. Values: `text`, `number`, `emailAddress`, `phone` |
| `border`       | boolean | Whether to show an outline border. Default: `false`.                           |
| `prefixIcon`   | string  | Icon name to display before the text (e.g., `person`, `email`).                |

```json
{
  "type": "TextField",
  "props": {
    "hintText": "Enter your email",
    "labelText": "Email Address",
    "keyboardType": "emailAddress",
    "border": true,
    "prefixIcon": "email"
  }
}
```

#### 4. Icon

| Prop    | Type      | Description                                                    |
| :------ | :-------- | :------------------------------------------------------------- |
| `icon`  | string    | The name of the Material Design icon (e.g., `person`, `star`). |
| `size`  | number    | The size of the icon.                                          |
| `color` | hex color | The color of the icon.                                         |

```json
{
  "type": "Icon",
  "props": {
    "icon": "settings",
    "size": 30,
    "color": "#000000"
  }
}
```

#### 5. Image

| Prop     | Type   | Description                                                                                                                 |
| :------- | :----- | :-------------------------------------------------------------------------------------------------------------------------- |
| `src`    | string | The source of the image (URL for network, path for asset).                                                                  |
| `fit`    | string | How the image should be inscribed into the space. Values: `cover`, `contain`, `fill`, `fitWidth`, `fitHeight`, `scaleDown`. |
| `width`  | number | The width of the image.                                                                                                     |
| `height` | number | The height of the image.                                                                                                    |

```json
{
  "type": "Image",
  "props": {
    "src": "https://picsum.photos/200/300",
    "fit": "cover",
    "width": 200,
    "height": 300
  }
}
```

#### 6. Scaffold

| Prop              | Type      | Description                           |
| :---------------- | :-------- | :------------------------------------ |
| `backgroundColor` | hex color | The background color of the scaffold. |

```json
{
  "type": "Scaffold",
  "props": {
    "backgroundColor": "#FFFFFF"
  },
  "children": [
    { "type": "AppBar", "props": { "title": "My Screen" } },
    {
      "type": "Center",
      "children": [{ "type": "Text", "props": { "text": "Body" } }]
    }
  ]
}
```

#### 7. AppBar

| Prop              | Type      | Description                                     |
| :---------------- | :-------- | :---------------------------------------------- |
| `title`           | string    | The text title of the app bar.                  |
| `backgroundColor` | hex color | The background color of the app bar.            |
| `elevation`       | number    | The z-coordinate at which to place the app bar. |
| `centerTitle`     | boolean   | Whether to center the title. Default: `false`.  |

```json
{
  "type": "AppBar",
  "props": {
    "title": "App Title",
    "backgroundColor": "#FF5722",
    "elevation": 4,
    "centerTitle": true
  }
}
```

#### 8. Container

| Prop              | Type      | Description                                                                                                                                             |
| :---------------- | :-------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `backgroundColor` | hex color | The background color of the container.                                                                                                                  |
| `padding`         | number    | Uniform padding around the child.                                                                                                                       |
| `margin`          | number    | Uniform margin around the container.                                                                                                                    |
| `borderRadius`    | number    | Radius for rounded corners.                                                                                                                             |
| `border`          | boolean   | Whether to draw a default grey border.                                                                                                                  |
| `borderColor`     | hex color | The color of the border.                                                                                                                                |
| `borderWidth`     | number    | The width of the border.                                                                                                                                |
| `alignment`       | string    | Alignment of the child. Values: `topLeft`, `topCenter`, `topRight`, `centerLeft`, `center`, `centerRight`, `bottomLeft`, `bottomCenter`, `bottomRight`. |

```json
{
  "type": "Container",
  "props": {
    "backgroundColor": "#E0E0E0",
    "padding": 16,
    "margin": 8,
    "borderRadius": 8,
    "border": true,
    "borderColor": "#999999",
    "borderWidth": 2,
    "alignment": "center"
  },
  "children": [{ "type": "Text", "props": { "text": "Box Content" } }]
}
```

#### 9. Row

| Prop                 | Type   | Description                                                                                                       |
| :------------------- | :----- | :---------------------------------------------------------------------------------------------------------------- |
| `mainAxisAlignment`  | string | Horizontal alignment of children. Values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`. |
| `crossAxisAlignment` | string | Vertical alignment of children. Values: `start`, `end`, `center`, `stretch`, `baseline`.                          |
| `mainAxisSize`       | string | How much space the row should take. Values: `max`, `min`.                                                         |

```json
{
  "type": "Row",
  "props": {
    "mainAxisAlignment": "spaceBetween",
    "crossAxisAlignment": "center",
    "mainAxisSize": "max"
  },
  "children": [
    { "type": "Text", "props": { "text": "Left" } },
    { "type": "Text", "props": { "text": "Right" } }
  ]
}
```

#### 10. Column

| Prop                 | Type   | Description                                                                                                     |
| :------------------- | :----- | :-------------------------------------------------------------------------------------------------------------- |
| `mainAxisAlignment`  | string | Vertical alignment of children. Values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`. |
| `crossAxisAlignment` | string | Horizontal alignment of children. Values: `start`, `end`, `center`, `stretch`, `baseline`.                      |
| `mainAxisSize`       | string | How much space the column should take. Values: `max`, `min`.                                                    |

```json
{
  "type": "Column",
  "props": {
    "mainAxisAlignment": "start",
    "crossAxisAlignment": "start",
    "mainAxisSize": "max"
  },
  "children": [
    { "type": "Text", "props": { "text": "Item 1" } },
    { "type": "Text", "props": { "text": "Item 2" } }
  ]
}
```

#### 11. Card

| Prop           | Type      | Description                               |
| :------------- | :-------- | :---------------------------------------- |
| `elevation`    | number    | The shadow depth of the card (default 1). |
| `color`        | hex color | The background color of the card.         |
| `margin`       | number    | The margin around the card.               |
| `borderRadius` | number    | The border radius of the card.            |

```json
{
  "type": "Card",
  "props": {
    "elevation": 4,
    "color": "#FFFFFF",
    "margin": 8,
    "borderRadius": 12
  },
  "children": [
    {
      "type": "Padding",
      "props": { "padding": 10 },
      "children": [{ "type": "Text", "props": { "text": "Card Content" } }]
    }
  ]
}
```

#### 12. ListView

| Prop         | Type    | Description                                           |
| :----------- | :------ | :---------------------------------------------------- |
| `itemCount`  | number  | The number of items to display in the list.           |
| `padding`    | number  | Padding inside the list.                              |
| `shrinkWrap` | boolean | Whether the list should shrink-wrap. Default: `true`. |

**Note:** `ListView` uses an `itemTemplate` field instead of `children` to define the structure of a single list item, which is then repeated `itemCount` times.

```json
{
  "type": "ListView",
  "props": {
    "itemCount": 5,
    "padding": 8,
    "shrinkWrap": true
  },
  "itemTemplate": {
    "type": "Card",
    "children": [{ "type": "Text", "props": { "text": "List Item" } }]
  }
}
```

#### 13. Padding

| Prop      | Type   | Description                                  |
| :-------- | :----- | :------------------------------------------- |
| `padding` | number | Uniform padding value to apply to the child. |

```json
{
  "type": "Padding",
  "props": {
    "padding": 20
  },
  "children": [{ "type": "Text", "props": { "text": "Padded Text" } }]
}
```

#### 14. Center

| Prop | Type | Description                                   |
| :--- | :--- | :-------------------------------------------- |
| None | N/A  | Centers its child within the available space. |

```json
{
  "type": "Center",
  "children": [{ "type": "Text", "props": { "text": "Centered Text" } }]
}
```

#### 15. Stack

| Prop | Type | Description                             |
| :--- | :--- | :-------------------------------------- |
| None | N/A  | Arranges children on top of each other. |

```json
{
  "type": "Stack",
  "children": [
    { "type": "Container", "props": { "backgroundColor": "#000000" } },
    {
      "type": "Positioned",
      "props": { "top": 10, "left": 10 },
      "children": [{ "type": "Text", "props": { "text": "Layer 2" } }]
    }
  ]
}
```

#### 16. Positioned

| Prop     | Type   | Description                                 |
| :------- | :----- | :------------------------------------------ |
| `top`    | number | Distance from the top edge of the Stack.    |
| `bottom` | number | Distance from the bottom edge of the Stack. |
| `left`   | number | Distance from the left edge of the Stack.   |
| `right`  | number | Distance from the right edge of the Stack.  |
| `width`  | number | The width of the positioned element.        |
| `height` | number | The height of the positioned element.       |

```json
{
  "type": "Positioned",
  "props": {
    "top": 10,
    "left": 10,
    "width": 100,
    "height": 100
  },
  "children": [{ "type": "Text", "props": { "text": "Absolute Position" } }]
}
```

#### 17. Expanded

| Prop   | Type   | Description                                          |
| :----- | :----- | :--------------------------------------------------- |
| `flex` | number | The factor by which to expand the child (default 1). |

```json
{
  "type": "Row",
  "children": [
    {
      "type": "Expanded",
      "props": { "flex": 2 },
      "children": [
        { "type": "Container", "props": { "backgroundColor": "#FF0000" } }
      ]
    },
    {
      "type": "Expanded",
      "props": { "flex": 1 },
      "children": [
        { "type": "Container", "props": { "backgroundColor": "#00FF00" } }
      ]
    }
  ]
}
```

#### 18. SizedBox

| Prop     | Type   | Description                 |
| :------- | :----- | :-------------------------- |
| `width`  | number | Explicit width of the box.  |
| `height` | number | Explicit height of the box. |

```json
{
  "type": "SizedBox",
  "props": {
    "width": 100,
    "height": 50
  }
}
```
