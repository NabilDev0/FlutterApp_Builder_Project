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

2.  **Generate Flutter Project**

    ```bash
    POST /api/projects/{id}/generate/
    Authorization: Token <your_token>
    ```

3.  **Download Generated Project**

    ```bash
    GET /api/projects/{id}/download/
    Authorization: Token <your_token>
    ```

4.  **View Generation Logs**

    ```bash
    GET /api/projects/{id}/logs/
    Authorization: Token <your_token>
    ```

## Supported Widgets and Props Reference

This section details all supported widgets and their corresponding properties (`props`) that can be used in the `json_data` payload.

### Layout & Structure Widgets

| Widget Type    | Supported Props                                                                                                   | Description                                                                                                                         |
| :------------- | :---------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| **Scaffold**   | None                                                                                                              | The basic structure for a visual interface. Automatically handles `AppBar` and `body` from children.                                |
| **AppBar**     | `title` (string), `backgroundColor` (hex color), `elevation` (number)                                             | The top bar of the application. Must be a direct child of `Scaffold`.                                                               |
| **Container**  | `backgroundColor` (hex color), `padding` (number), `margin` (number), `borderRadius` (number), `border` (boolean) | A convenience widget that combines common painting, positioning, and sizing widgets.                                                |
| **Row**        | `mainAxisAlignment` (string), `crossAxisAlignment` (string)                                                       | Arranges children horizontally. `mainAxisAlignment` values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`. |
| **Column**     | `mainAxisAlignment` (string), `crossAxisAlignment` (string)                                                       | Arranges children vertically. `mainAxisAlignment` values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`.   |
| **Stack**      | None                                                                                                              | Arranges children on top of each other. Children can be wrapped in `Positioned`.                                                    |
| **Positioned** | `top` (number), `bottom` (number), `left` (number), `right` (number)                                              | Used only inside a `Stack` to position its child absolutely.                                                                        |
| **Expanded**   | `flex` (number, default 1)                                                                                        | Used inside `Row` or `Column` to expand a child to fill the available space.                                                        |
| **SizedBox**   | `width` (number), `height` (number)                                                                               | Creates a box with a specified size. Useful for adding space.                                                                       |
| **Padding**    | `padding` (number, default 8)                                                                                     | Adds uniform padding around its child.                                                                                              |
| **Center**     | None                                                                                                              | Centers its child within itself.                                                                                                    |
| **Card**       | `elevation` (number, default 1)                                                                                   | A material design card with rounded corners and a shadow.                                                                           |
| **ListView**   | `itemCount` (number, default 10)                                                                                  | Creates a scrollable list of items. Requires an `itemTemplate` field instead of `children`.                                         |

### Content & Input Widgets

| Widget Type   | Supported Props                                                                                        | Description                                                                                                                                                                                |
| :------------ | :----------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Text**      | `text` (string), `fontSize` (number), `color` (hex color), `fontWeight` (string), `alignment` (string) | Displays a string of text. `fontWeight` values: `normal`, `bold`. `alignment` values: `left`, `right`, `center`, `justify`, `start`, `end`.                                                |
| **Button**    | `text` (string), **`actions` (array)**                                                                 | An `ElevatedButton`. **The `actions` array is the standard for defining button behavior (see Action Chaining below).**                                                                     |
| **TextField** | `hintText` (string)                                                                                    | A text input field.                                                                                                                                                                        |
| **Icon**      | `icon` (string), `size` (number), `color` (hex color)                                                  | Displays a Material Design icon. `icon` should be the icon name (e.g., `person`, `star`, `arrow_forward_ios`).                                                                             |
| **Image**     | `src` (string), `fit` (string)                                                                         | Displays an image. If `src` starts with `http`, it uses `Image.network`. Otherwise, it uses `Image.asset`. `fit` values: `cover`, `contain`, `fill`, `fitWidth`, `fitHeight`, `scaleDown`. |

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

The following examples illustrate the usage of the \`props\` field for all 18 supported widgets.

#### 1. Text

| Prop         | Type      | Description                                                                                   |
| :----------- | :-------- | :-------------------------------------------------------------------------------------------- |
| `text`       | string    | The content of the text widget.                                                               |
| `fontSize`   | number    | The size of the font.                                                                         |
| `color`      | hex color | The color of the text (e.g., `#FF0000`).                                                      |
| `fontWeight` | string    | The weight of the font. Values: `normal`, `bold`.                                             |
| `alignment`  | string    | How the text should be aligned. Values: `left`, `right`, `center`, `justify`, `start`, `end`. |

```json
{
  "type": "Text",
  "props": {
    "text": "Hello World",
    "fontSize": 20,
    "color": "#FF0000",
    "fontWeight": "bold",
    "alignment": "center"
  }
}
```

#### Button

| Prop      | Type   | Description                                   |
| --------- | ------ | --------------------------------------------- |
| `text`    | string | The text displayed on the button.             |
| `actions` | array  | A list of action objects to execute in order. |

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

| Prop       | Type   | Description                              |
| :--------- | :----- | :--------------------------------------- |
| `hintText` | string | Placeholder text displayed in the field. |

```json
{
  "type": "TextField",
  "props": {
    "hintText": "Enter your email"
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

| Prop  | Type   | Description                                                                                                                 |
| :---- | :----- | :-------------------------------------------------------------------------------------------------------------------------- |
| `src` | string | The source of the image (URL for network, path for asset).                                                                  |
| `fit` | string | How the image should be inscribed into the space. Values: `cover`, `contain`, `fill`, `fitWidth`, `fitHeight`, `scaleDown`. |

```json
{
  "type": "Image",
  "props": {
    "src": "https://picsum.photos/200/300",
    "fit": "cover"
  }
}
```

#### 6. Scaffold

| Prop | Type | Description                                     |
| :--- | :--- | :---------------------------------------------- |
| None | N/A  | Provides the high-level structure for a screen. |

```json
{
  "type": "Scaffold",
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

```json
{
  "type": "AppBar",
  "props": {
    "title": "App Title",
    "backgroundColor": "#FF5722"
  }
}
```

#### 8. Container

| Prop              | Type      | Description                            |
| :---------------- | :-------- | :------------------------------------- |
| `backgroundColor` | hex color | The background color of the container. |
| `padding`         | number    | Uniform padding around the child.      |
| `margin`          | number    | Uniform margin around the container.   |
| `borderRadius`    | number    | Radius for rounded corners.            |
| `border`          | boolean   | Whether to draw a default grey border. |

```json
{
  "type": "Container",
  "props": {
    "backgroundColor": "#E0E0E0",
    "padding": 16,
    "borderRadius": 8
  },
  "children": [{ "type": "Text", "props": { "text": "Box Content" } }]
}
```

#### 9. Row

| Prop                 | Type   | Description                                                                                                       |
| :------------------- | :----- | :---------------------------------------------------------------------------------------------------------------- |
| `mainAxisAlignment`  | string | Horizontal alignment of children. Values: `start`, `end`, `center`, `spaceBetween`, `spaceAround`, `spaceEvenly`. |
| `crossAxisAlignment` | string | Vertical alignment of children. Values: `start`, `end`, `center`, `stretch`, `baseline`.                          |

```json
{
  "type": "Row",
  "props": {
    "mainAxisAlignment": "spaceBetween"
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

```json
{
  "type": "Column",
  "props": {
    "crossAxisAlignment": "start"
  },
  "children": [
    { "type": "Text", "props": { "text": "Item 1" } },
    { "type": "Text", "props": { "text": "Item 2" } }
  ]
}
```

#### 11. Card

| Prop        | Type   | Description                               |
| :---------- | :----- | :---------------------------------------- |
| `elevation` | number | The shadow depth of the card (default 1). |

```json
{
  "type": "Card",
  "props": {
    "elevation": 4
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

| Prop        | Type   | Description                                 |
| :---------- | :----- | :------------------------------------------ |
| `itemCount` | number | The number of items to display in the list. |

**Note:** `ListView` uses an `itemTemplate` field instead of `children` to define the structure of a single list item, which is then repeated `itemCount` times.

```json
{
  "type": "ListView",
  "props": {
    "itemCount": 5
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

```json
{
  "type": "Positioned",
  "props": {
    "top": 10,
    "left": 10
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
    "height": 50
  }
}
```
