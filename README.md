# Flutter Builder - Django Backend

A Django REST API backend that generates complete Flutter mobile applications from JSON specifications

## Requirements

- Python 3.11+
- Django 5.1+
- Django REST Framework

## Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/NabilDev0/FlutterApp_Builder_Project.git
    cd flutter_builder_project
    ```

2. **Create virtual environment**

    ```bash
    python -m venv venv
    #then use this command to activate the env EVERYTIME you open the project
    venv/Scripts/activate
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Run migrations**

    ```bash
    python manage.py migrate
    ```

5. **Start development server**

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

#### 3. Using the Token

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

1. **Create Project**

    ```bash
    POST /api/projects/
    Authorization: Token <your_token>
    {
      "name": "My App",
      "description": "A test application",
      "json_data": { ... }
    }
    ```

2. **Generate Flutter Project**

    ```bash
    POST /api/projects/{id}/generate/
    Authorization: Token <your_token>
    ```

3. **Download Generated Project**

    ```bash
    GET /api/projects/{id}/download/
    Authorization: Token <your_token>
    ```

4. **View Generation Logs**

    ```bash
    GET /api/projects/{id}/logs/
    Authorization: Token <your_token>
    ```

## Supported Widgets and Props Reference

This section details **all** supported widgets and their corresponding properties (`props`) as implemented in the backend.

### Layout & Structure Widgets

| Widget Type    | Supported Props                                                                                                                                                             | Description                                               |
| :------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| **Scaffold**   | `backgroundColor` (hex)                                                                                                                                                     | Basic page structure.                                     |
| **AppBar**     | `title` (string), `backgroundColor` (hex), `elevation` (number), `centerTitle` (bool), `showBackButton` (bool), `automaticallyImplyLeading` (bool)                          | Top navigation bar.                                       |
| **Container**  | `backgroundColor` (hex), `padding` (number), `margin` (number), `borderRadius` (number), `border` (bool), `borderColor` (hex), `borderWidth` (number), `alignment` (string), `width` (number), `height` (number) | Versatile box with width and height in props. |
| **Row**        | `mainAxisAlignment` (string), `crossAxisAlignment` (string), `mainAxisSize` (string)                                                                                        | Horizontal layout.                                        |
| **Column**     | `mainAxisAlignment` (string), `crossAxisAlignment` (string), `mainAxisSize` (string)                                                                                        | Vertical layout.                                          |
| **Stack**      | None                                                                                                                                                                        | Overlapping layout.                                       |
| **Positioned** | `top`, `bottom`, `left`, `right`, `width`, `height` (numbers)                                                                                                               | Absolute positioning in Stack.                            |
| **Expanded**   | `flex` (number)                                                                                                                                                             | Fills available space in Row/Column.                      |
| **SizedBox**   | `width`, `height` (numbers)                                                                                                                                                 | Fixed size box.                                           |
| **Padding**    | `padding` (number)                                                                                                                                                          | Adds space around child.                                  |
| **Center**     | None                                                                                                                                                                        | Centers child.                                            |
| **Card**       | `elevation` (number), `color` (hex), `margin` (number), `borderRadius` (number)                                                                                             | Material Card.                                            |
| **ListView**   | `itemCount` (number), `shrinkWrap` (bool), `padding` (number)                                                                                                               | Scrollable list. Uses `itemTemplate`.                     |

### Content & Input Widgets

| Widget Type   | Supported Props                                                                                                                                                                                                   | Description      |
| :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------- |
| **Text**      | `text` (string), `fontSize` (number), `color` (hex), `fontWeight` (string), `fontStyle` (string), `letterSpacing` (number), `decoration` (string), `alignment` (string), `maxLines` (number), `overflow` (string) | Text display.    |
| **Button**    | `text` (string), `backgroundColor` (hex), `color` (hex), `elevation` (number), `borderRadius` (number), `actions` (array), `onPress` (string)                                                                     | Elevated button. |
| **TextField** | `hintText` (string), `labelText` (string), `obscureText` (bool), `keyboardType` (string), `border` (bool), `prefixIcon` (string)                                                                                  | User input.      |
| **Icon**      | `icon` (string), `size` (number), `color` (hex)                                                                                                                                                                   | Material Icon.   |
| **Image**     | `src` (url/path), `fit` (string), `width` (number), `height` (number)                                                                                                                                             | Image display.   |

### Navigation & Specialized Widgets

| Widget Type             | Supported Props                                                                                                                                            | Description        |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------- |
| **BottomNavigationBar** | `currentIndex` (number), `type` (string), `selectedItemColor` (hex), `unselectedItemColor` (hex), `items` (array of objects with `label`, `icon`, `route`) | Bottom navigation. |
| **Drawer**              | `header` (object with `title`, `subtitle`, `backgroundColor`), `children` (array)                                                                          | Side menu.         |

---

## Exhaustive JSON Examples (All Props)

#### 1. AppBar (Full Props)

```json
{
  "type": "AppBar",
  "props": {
    "title": "Comprehensive AppBar",
    "backgroundColor": "#2196F3",
    "elevation": 4.0,
    "centerTitle": true,
    "showBackButton": true,
    "automaticallyImplyLeading": false
  }
}
```

#### 2. Text (Full Props)

```json
{
  "type": "Text",
  "props": {
    "text": "Full Styled Text",
    "fontSize": 20.0,
    "color": "#FF5722",
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

#### 3. Container (Full Props)

```json
{
  "type": "Container",
  "props": {
    "width": 200,
    "height": 100,
    "backgroundColor": "#E3F2FD",
    "padding": 16,
    "margin": 8,
    "borderRadius": 12,
    "border": true,
    "borderColor": "#1976D2",
    "borderWidth": 2,
    "alignment": "center"
  },
  "children": [{ "type": "Text", "props": { "text": "Inside Container" } }]
}
```

#### 4. Button & Actions (Full Props)

```json
{
  "type": "Button",
  "props": {
    "text": "Action Button",
    "backgroundColor": "#4CAF50",
    "color": "#FFFFFF",
    "elevation": 5.0,
    "borderRadius": 25,
    "actions": [
      { "type": "snackbar", "message": "First Action" },
      { "type": "dialog", "title": "Confirm", "message": "Proceed?" },
      { "type": "navigate", "route": "/details" },
      { "type": "goBack" }
    ]
  }
}
```

#### 5. TextField (Full Props)

```json
{
  "type": "TextField",
  "props": {
    "hintText": "Enter Password",
    "labelText": "Password",
    "obscureText": true,
    "keyboardType": "text",
    "border": true,
    "prefixIcon": "lock"
  }
}
```

#### 6. Row & Column (Full Props)

```json
{
  "type": "Column",
  "props": {
    "mainAxisAlignment": "center",
    "crossAxisAlignment": "stretch",
    "mainAxisSize": "min"
  },
  "children": [
    {
      "type": "Row",
      "props": {
        "mainAxisAlignment": "spaceBetween",
        "crossAxisAlignment": "center",
        "mainAxisSize": "max"
      },
      "children": []
    }
  ]
}
```

#### 7. ListView (Full Props)

```json
{
  "type": "ListView",
  "props": {
    "itemCount": 20,
    "shrinkWrap": false,
    "padding": 12
  },
  "itemTemplate": {
    "type": "Text",
    "props": { "text": "Item Index" }
  }
}
```

#### 8. BottomNavigationBar (Full Props)

```json
{
  "type": "BottomNavigationBar",
  "props": {
    "currentIndex": 0,
    "type": "fixed",
    "selectedItemColor": "#2196F3",
    "unselectedItemColor": "#9E9E9E"
  },
  "items": [
    { "label": "Home", "icon": "home", "route": "/" },
    { "label": "Search", "icon": "search", "route": "/search" },
    { "label": "Profile", "icon": "person", "route": "/profile" }
  ]
}
```

#### 9. Drawer (Full Props)

```json
{
  "type": "Drawer",
  "props": {
    "header": {
      "title": "User Menu",
      "subtitle": "user@example.com",
      "backgroundColor": "#2196F3"
    }
  },
  "children": [
    {
      "type": "ListTile",
      "props": {
        "title": "Settings",
        "icon": "settings",
        "actions": [{ "type": "navigate", "route": "/settings" }]
      }
    }
  ]
}
```

#### 10. Image (Full Props)

```json
{
  "type": "Image",
  "props": {
    "src": "https://example.com/image.png",
    "fit": "cover",
    "width": 300,
    "height": 200
  }
}
```

#### 11. Card (Full Props)

```json
{
  "type": "Card",
  "props": {
    "elevation": 8.0,
    "color": "#FAFAFA",
    "margin": 12,
    "borderRadius": 16
  },
  "children": []
}
```

#### 12. Positioned (Full Props)

```json
{
  "type": "Positioned",
  "props": {
    "top": 10,
    "bottom": 10,
    "left": 20,
    "right": 20,
    "width": 100,
    "height": 50
  },
  "children": []
}
```
