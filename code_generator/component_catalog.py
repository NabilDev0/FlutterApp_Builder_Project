"""The public component contract supported by :class:`WidgetGenerator`.

This catalog deliberately describes only fields that the generator emits.  It
is returned by the API so clients do not need to maintain a second, drifting
list of widgets, properties, and nesting rules.
"""


def prop(name, value_type, *, required=False, default=None, values=None,
         description=None):
    result = {"name": name, "type": value_type, "required": required}
    if default is not None:
        result["default"] = default
    if values is not None:
        result["values"] = values
    if description:
        result["description"] = description
    return result


# Child handling is intentionally expressed in the same terms used by the
# generator validation: none, child, children, and special.
COMPONENT_CATALOG = [
    {"type": "Text", "category": "content", "child_rule": "none", "props": [
        prop("text", "string", default="Text"), prop("fontSize", "number"),
        prop("color", "hex_color"), prop("fontWeight", "string", values=["normal", "bold", "w100", "w200", "w300", "w400", "w500", "w600", "w700", "w800", "w900"]),
        prop("fontStyle", "enum", values=["normal", "italic"]), prop("letterSpacing", "number"),
        prop("decoration", "enum", values=["none", "underline", "overline", "lineThrough"]),
        prop("alignment", "enum", values=["left", "right", "center", "justify", "start", "end"]),
        prop("maxLines", "integer"), prop("overflow", "enum", values=["clip", "fade", "ellipsis", "visible"]),
    ]},
    {"type": "Image", "category": "content", "child_rule": "none", "props": [
        prop("src", "string", default="https://via.placeholder.com/150"),
        prop("fit", "enum", default="cover", values=["fill", "contain", "cover", "fitWidth", "fitHeight", "none", "scaleDown"]),
        prop("width", "number"), prop("height", "number"),
    ]},
    {"type": "Icon", "category": "content", "child_rule": "none", "props": [
        prop("icon", "string", default="star"), prop("size", "number"), prop("color", "hex_color"),
    ]},
    {"type": "Button", "category": "input", "child_rule": "none", "props": [
        prop("text", "string", default="Button"), prop("backgroundColor", "hex_color"), prop("textColor", "hex_color"),
        prop("color", "hex_color", description="Legacy alias for textColor."), prop("elevation", "number"),
        prop("borderRadius", "number"), prop("onPress", "string", default="handlePress"),
        prop("actions", "action[]", description="Supported actions are snackbar, dialog, navigate, and goBack."),
    ]},
    {"type": "TextField", "category": "input", "child_rule": "none", "props": [
        prop("obscureText", "boolean", default=False), prop("keyboardType", "string", default="text"),
        prop("hintText", "string"), prop("labelText", "string"), prop("border", "boolean"), prop("prefixIcon", "string"),
    ]},
    {"type": "ListTile", "category": "content", "child_rule": "none", "props": [
        prop("icon", "string"), prop("title", "string", default="List Item"), prop("subtitle", "string"),
        prop("trailingIcon", "string"), prop("actions", "action[]"),
    ]},
    {"type": "Container", "category": "layout", "child_rule": "child", "props": [
        prop("width", "number"), prop("height", "number"), prop("alignment", "string"), prop("padding", "number"),
        prop("margin", "number"), prop("backgroundColor", "hex_color"), prop("borderRadius", "number"),
        prop("border", "boolean"), prop("borderColor", "hex_color", default="#000000"), prop("borderWidth", "number", default=1),
    ]},
    {"type": "Padding", "category": "layout", "child_rule": "child", "props": [prop("padding", "number", default=8)]},
    {"type": "Center", "category": "layout", "child_rule": "child", "props": []},
    {"type": "Expanded", "category": "layout", "child_rule": "child", "props": [prop("flex", "integer")]},
    {"type": "SizedBox", "category": "layout", "child_rule": "child", "props": [prop("width", "number"), prop("height", "number")]},
    {"type": "Positioned", "category": "layout", "child_rule": "child", "props": [
        prop("top", "number"), prop("left", "number"), prop("right", "number"), prop("bottom", "number"),
        prop("width", "number"), prop("height", "number"),
    ]},
    {"type": "Card", "category": "layout", "child_rule": "child", "props": [
        prop("elevation", "number"), prop("color", "hex_color"), prop("margin", "number"), prop("borderRadius", "number"),
    ]},
    {"type": "Row", "category": "layout", "child_rule": "children", "props": [
        prop("mainAxisSize", "enum", default="max", values=["min", "max"]), prop("mainAxisAlignment", "string"), prop("crossAxisAlignment", "string"),
    ]},
    {"type": "Column", "category": "layout", "child_rule": "children", "props": [
        prop("mainAxisSize", "enum", default="max", values=["min", "max"]), prop("mainAxisAlignment", "string"), prop("crossAxisAlignment", "string"),
    ]},
    {"type": "Stack", "category": "layout", "child_rule": "children", "props": []},
    {"type": "ListView", "category": "layout", "child_rule": "special", "props": [
        prop("itemCount", "integer", default=10), prop("shrinkWrap", "boolean", default=True), prop("padding", "number", default=0),
    ], "fields": [prop("itemTemplate", "component", required=True)]},
    {"type": "AppBar", "category": "screen", "child_rule": "special", "props": [
        prop("title", "string", default="App"), prop("color", "hex_color"), prop("centerTitle", "boolean", default=False),
        prop("showBackButton", "boolean"), prop("automaticallyImplyLeading", "boolean"), prop("backgroundColor", "hex_color"), prop("elevation", "number"),
    ]},
    {"type": "BottomNavigationBar", "category": "screen", "child_rule": "special", "props": [
        prop("currentIndex", "integer"), prop("type", "enum", values=["fixed", "shifting"]),
        prop("selectedItemColor", "hex_color"), prop("unselectedItemColor", "hex_color"),
    ], "fields": [
        prop("items", "navigation_item[]", required=True,
             description="Each item supports label, icon, and route."),
    ]},
    {"type": "Drawer", "category": "screen", "child_rule": "special", "props": [
        prop("header", "object", description="Supports title, subtitle, and backgroundColor."),
    ]},
    {"type": "Scaffold", "category": "screen", "child_rule": "special", "props": [prop("backgroundColor", "hex_color")]},
]

CATALOG_BY_TYPE = {component["type"]: component for component in COMPONENT_CATALOG}


def validate_component_tree(node, path="template_json"):
    """Return a readable validation error for an unsupported component tree."""
    if not isinstance(node, dict):
        return f"{path} must be an object."

    component_type = node.get("type")
    catalog_entry = CATALOG_BY_TYPE.get(component_type)
    if not catalog_entry:
        return f"{path}.type '{component_type}' is not supported by the code generator."

    children = node.get("children", [])
    if children is None:
        children = []
    if not isinstance(children, list):
        return f"{path}.children must be a list."

    rule = catalog_entry["child_rule"]
    if rule == "none" and children:
        return f"{path} ({component_type}) does not allow children."
    if rule == "child" and len(children) > 1:
        return f"{path} ({component_type}) allows only one child."

    for index, child in enumerate(children):
        error = validate_component_tree(child, f"{path}.children[{index}]")
        if error:
            return error

    if component_type == "ListView":
        template = node.get("itemTemplate")
        if not isinstance(template, dict):
            return f"{path}.itemTemplate is required for ListView."
        return validate_component_tree(template, f"{path}.itemTemplate")

    if component_type == "BottomNavigationBar":
        items = node.get("items")
        if not isinstance(items, list) or not items:
            return f"{path}.items must be a non-empty list for BottomNavigationBar."

    return None


def validate_project_tree(value):
    """Validate the project JSON that is passed to the Flutter generator."""
    if not isinstance(value, dict):
        return 'json_data must be an object.'
    if 'screens' in value:
        screens = value['screens']
    elif 'screen' in value:
        screens = [value['screen']]
    else:
        return "json_data must contain 'screen' or 'screens'."
    if not isinstance(screens, list):
        return 'json_data.screens must be a list.'
    for screen_index, screen in enumerate(screens):
        path = f'json_data.screens[{screen_index}]'
        if not isinstance(screen, dict):
            return f'{path} must be an object.'
        components = screen.get('components', [])
        if not isinstance(components, list):
            return f'{path}.components must be a list.'
        for component_index, component in enumerate(components):
            error = validate_component_tree(component, f'{path}.components[{component_index}]')
            if error:
                return error
    return None
