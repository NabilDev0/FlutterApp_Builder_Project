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

Once your Django server is running:

## How to use Swagger

```bash
# Assuming you are in the project directory and have activated your virtual environment
python manage.py runserver
```

You can access the Swagger UI at the following URL in your web browser:

**Swagger UI URL:** `http://localhost:8000/api/schema/swagger-ui/`

## API Documentation

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

### Save and Generate

1. **Create Project**

```bash
POST /api/projects/
{
  "name": "My App",
  "description": "A test application",
  "json_data": { ... }
}
```

2. **Generate Flutter Project**

```bash
POST /api/projects/{id}/generate/
```

3. **Download Generated Project**

```bash
GET /api/projects/{id}/download/
```

4. **View Generation Logs**

```bash
GET /api/projects/{id}/logs/
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

| Widget Type   | Supported Props                                                                                        | Description                                                                                                                                                                                                     |
| :------------ | :----------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Text**      | `text` (string), `fontSize` (number), `color` (hex color), `fontWeight` (string), `alignment` (string) | Displays a string of text. `fontWeight` values: `normal`, `bold`. `alignment` values: `left`, `right`, `center`, `justify`, `start`, `end`.                                                                     |
| **Button**    | `text` (string), `onPress` (string), `navigateTo` (string)                                             | An `ElevatedButton`. If `navigateTo` is present, it takes precedence and navigates to the specified route (e.g., `/profile`). Otherwise, it uses the `onPress` string as a function name (e.g., `handlePress`). |
| **TextField** | `hintText` (string)                                                                                    | A text input field.                                                                                                                                                                                             |
| **Icon**      | `icon` (string), `size` (number), `color` (hex color)                                                  | Displays a Material Design icon. `icon` should be the icon name (e.g., `person`, `star`, `arrow_forward_ios`).                                                                                                  |
| **Image**     | `src` (string), `fit` (string)                                                                         | Displays an image. If `src` starts with `http`, it uses `Image.network`. Otherwise, it uses `Image.asset`. `fit` values: `cover`, `contain`, `fill`, `fitWidth`, `fitHeight`, `scaleDown`.                      |

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
                        "navigateTo": "/profile"
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
      "components": [...]
    }
  ]
}
```

### Widget Props Reference

The following examples illustrate the usage of the \`props\` field for all 18 supported widgets.

#### 1. Text

| Prop           | Type      | Description                                                                        |
| :------------- | :-------- | :--------------------------------------------------------------------------------- |
| \`text\`       | string    | The text content.                                                                  |
| \`fontSize\`   | number    | The size of the font.                                                              |
| \`color\`      | hex color | The color of the text (e.g., \`#FF0000\`).                                         |
| \`fontWeight\` | string    | Font weight (\`normal\` or \`bold\`).                                              |
| \`alignment\`  | string    | Text alignment (\`left\`, \`right\`, \`center\`, \`justify\`, \`start\`, \`end\`). |

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

#### 2. Container

| Prop                | Type      | Description                              |
| :------------------ | :-------- | :--------------------------------------- |
| \`backgroundColor\` | hex color | Background color of the container.       |
| \`padding\`         | number    | Padding around the child.                |
| \`margin\`          | number    | Margin around the container.             |
| \`borderRadius\`    | number    | Corner radius for the container.         |
| \`border\`          | boolean   | If \`true\`, adds a default grey border. |
| \`layout.w\`        | number    | Explicit width (optional).               |
| \`layout.h\`        | number    | Explicit height (optional).              |

```json
{
  "type": "Container",
  "props": {
    "backgroundColor": "#2196F3",
    "padding": 16,
    "margin": 8,
    "borderRadius": 10,
    "border": true
  },
  "children": [{ "type": "Text", "props": { "text": "Inside Container" } }]
}
```

#### 3. Row

| Prop                   | Type   | Description                                                                                                            |
| :--------------------- | :----- | :--------------------------------------------------------------------------------------------------------------------- |
| \`mainAxisAlignment\`  | string | Horizontal alignment of children (\`start\`, \`end\`, \`center\`, \`spaceBetween\`, \`spaceAround\`, \`spaceEvenly\`). |
| \`crossAxisAlignment\` | string | Vertical alignment of children (\`start\`, \`end\`, \`center\`, \`stretch\`, \`baseline\`).                            |

```json
{
  "type": "Row",
  "props": {
    "mainAxisAlignment": "spaceEvenly",
    "crossAxisAlignment": "center"
  },
  "children": [
    { "type": "Text", "props": { "text": "Item 1" } },
    { "type": "Text", "props": { "text": "Item 2" } }
  ]
}
```

#### 4. Column

| Prop                   | Type   | Description                                                                                                          |
| :--------------------- | :----- | :------------------------------------------------------------------------------------------------------------------- |
| \`mainAxisAlignment\`  | string | Vertical alignment of children (\`start\`, \`end\`, \`center\`, \`spaceBetween\`, \`spaceAround\`, \`spaceEvenly\`). |
| \`crossAxisAlignment\` | string | Horizontal alignment of children (\`start\`, \`end\`, \`center\`, \`stretch\`, \`baseline\`).                        |

```json
{
  "type": "Column",
  "props": {
    "mainAxisAlignment": "start",
    "crossAxisAlignment": "stretch"
  },
  "children": [
    { "type": "Text", "props": { "text": "Item A" } },
    { "type": "Text", "props": { "text": "Item B" } }
  ]
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

#### 6. Image

| Prop    | Type   | Description                                                                                                                      |
| :------ | :----- | :------------------------------------------------------------------------------------------------------------------------------- |
| \`src\` | string | URL (for network image) or asset path (for local image).                                                                         |
| \`fit\` | string | How the image should be inscribed into the space (\`cover\`, \`contain\`, \`fill\`, \`fitWidth\`, \`fitHeight\`, \`scaleDown\`). |

```json
{
  "type": "Image",
  "props": {
    "src": "https://example.com/image.png",
    "fit": "cover"
  }
}
```

#### 7. AppBar

| Prop                | Type      | Description                      |
| :------------------ | :-------- | :------------------------------- |
| \`title\`           | string    | The title text for the app bar.  |
| \`backgroundColor\` | hex color | Background color of the app bar. |
| \`elevation\`       | number    | Shadow depth below the app bar.  |

```json
{
  "type": "AppBar",
  "props": {
    "title": "My App Bar",
    "backgroundColor": "#4CAF50",
    "elevation": 8
  }
}
```

#### 8. Scaffold

| Prop | Type | Description                                                                |
| :--- | :--- | :------------------------------------------------------------------------- |
| None | N/A  | The basic screen structure. Takes \`AppBar\` and body content as children. |

```json
{
  "type": "Scaffold",
  "children": [
    { "type": "AppBar", "props": { "title": "App Title" } },
    {
      "type": "Center",
      "children": [{ "type": "Text", "props": { "text": "Body Content" } }]
    }
  ]
}
```

#### 9. ListView

| Prop             | Type   | Description                                                        |
| :--------------- | :----- | :----------------------------------------------------------------- |
| \`itemCount\`    | number | The number of items to display in the list.                        |
| \`itemTemplate\` | object | The widget structure for each item (used instead of \`children\`). |

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

#### 10. Card

| Prop          | Type   | Description                |
| :------------ | :----- | :------------------------- |
| \`elevation\` | number | Shadow depth for the card. |

```json
{
  "type": "Card",
  "props": {
    "elevation": 4
  },
  "children": [{ "type": "Text", "props": { "text": "Card Content" } }]
}
```

#### 11. TextField

| Prop         | Type   | Description                                        |
| :----------- | :----- | :------------------------------------------------- |
| \`hintText\` | string | Placeholder text displayed inside the input field. |

```json
{
  "type": "TextField",
  "props": {
    "hintText": "Enter your name"
  }
}
```

#### 12. Icon

| Prop      | Type      | Description                                          |
| :-------- | :-------- | :--------------------------------------------------- |
| \`icon\`  | string    | The Material Icon name (e.g., \`star\`, \`person\`). |
| \`size\`  | number    | The size of the icon.                                |
| \`color\` | hex color | The color of the icon.                               |

```json
{
  "type": "Icon",
  "props": {
    "icon": "star",
    "size": 30,
    "color": "#FFC107"
  }
}
```

#### 13. Padding

| Prop        | Type   | Description                                  |
| :---------- | :----- | :------------------------------------------- |
| \`padding\` | number | Uniform padding value to apply to the child. |

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

| Prop       | Type   | Description                                 |
| :--------- | :----- | :------------------------------------------ |
| \`top\`    | number | Distance from the top edge of the Stack.    |
| \`bottom\` | number | Distance from the bottom edge of the Stack. |
| \`left\`   | number | Distance from the left edge of the Stack.   |
| \`right\`  | number | Distance from the right edge of the Stack.  |

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

| Prop     | Type   | Description                                          |
| :------- | :----- | :--------------------------------------------------- |
| \`flex\` | number | The factor by which to expand the child (default 1). |

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

| Prop       | Type   | Description                 |
| :--------- | :----- | :-------------------------- |
| \`width\`  | number | Explicit width of the box.  |
| \`height\` | number | Explicit height of the box. |

```json
{
  "type": "SizedBox",
  "props": {
    "height": 50
  }
}
```
