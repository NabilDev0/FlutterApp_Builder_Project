class WidgetValidationError(Exception):
    pass


class WidgetGenerator:

    def __init__(self):
        # Define widget rules: 'child', 'children', 'none', or 'special'
        self.widget_rules = {
            'Container': 'child',
            'Center': 'child',
            'Padding': 'child',
            'Expanded': 'child',
            'SizedBox': 'child',
            'Positioned': 'child',
            'Card': 'child',
            'Drawer': 'special',
            'Row': 'children',
            'Column': 'children',
            'Stack': 'children',
            'ListView': 'special',  # Uses itemTemplate
            'Text': 'none',
            'Image': 'none',
            'Icon': 'none',
            'TextField': 'none',
            'Button': 'none',
            'AppBar': 'special',
            'BottomNavigationBar': 'special',
            'Scaffold': 'special',
            'ListTile': 'none',
        }

    def _validate_widget(self, widget_type, data):
        """Validate widget structure before generation."""
        rule = self.widget_rules.get(widget_type)
        if not rule:
            return  # Unknown widget, skip validation

        children = data.get('children', [])

        # Check for 'child' in props as well (some JSON might use it)
        if not children and data.get('props', {}).get('child'):
            children = [data.get('props', {}).get('child')]
            # Normalize to children list for internal use
            data['children'] = children

        if rule == 'child':
            if len(children) > 1:
                raise WidgetValidationError(
                    f"Widget '{widget_type}' can only have ONE child, but {len(children)} were provided. "
                    f"Wrap them in a Column or Row if multiple children are needed."
                )
        elif rule == 'children':
            # Multiple children are allowed, no specific count validation needed here
            pass
        elif rule == 'none':
            if children:
                raise WidgetValidationError(
                    f"Widget '{widget_type}' does not support children, but {len(children)} were provided."
                )

    def generate_widget(self, widget_data, indent_level=0):
        """Main widget generation dispatcher."""
        widget_type = widget_data.get('type', '')

        # Validate before generating
        self._validate_widget(widget_type, widget_data)

        generators = {
            'Text': self.generate_text,
            'Container': self.generate_container,
            'Row': self.generate_row,
            'Column': self.generate_column,
            'Button': self.generate_button,
            'Image': self.generate_image,
            'AppBar': self.generate_appbar,
            'Scaffold': self.generate_scaffold,
            'ListView': self.generate_listview,
            'Card': self.generate_card,
            'TextField': self.generate_textfield,
            'Icon': self.generate_icon,
            'Padding': self.generate_padding,
            'Center': self.generate_center,
            'Stack': self.generate_stack,
            'Positioned': self.generate_positioned,
            'Expanded': self.generate_expanded,
            'SizedBox': self.generate_sizedbox,
            'BottomNavigationBar': self.generate_bottom_navigation_bar,
            'Drawer': self.generate_drawer,
            'ListTile': self.generate_listtile,
        }

        generator = generators.get(widget_type, self.generate_unknown)
        return generator(widget_data, indent_level)

    def indent(self, code, level):
        """Indent code by specified level."""
        if not code:
            return code
        spaces = ' ' * (level * 2)
        lines = code.split('\n')
        return '\n'.join(spaces + line if line.strip() else line for line in lines)

    def _parse_color(self, color_str):
        """Parse hex color string to Flutter Color format."""
        if not color_str:
            return None
        color = color_str.lstrip('#')

        # Handle 3-digit hex (e.g., #f00 -> #ff0000)
        if len(color) == 3:
            color = ''.join([c*2 for c in color])

        # Add alpha channel if not present
        if len(color) == 6:
            color = 'FF' + color

        # Validate hex string
        try:
            int(color, 16)
        except ValueError:
            return None

        return f"Color(0x{color})"

    def generate_text(self, data, indent_level=0):
        """Generate Text widget with all supported props."""
        props = data.get('props', {})
        text = props.get('text', 'Text').replace(
            "'", "\\'").replace('$', '\\$')

        code = "Text(\n"
        code += f"  '{text}',\n"

        # Style properties
        style_props = []

        if props.get('fontSize'):
            style_props.append(f"fontSize: {props['fontSize']}")

        color_code = self._parse_color(props.get('color'))
        if color_code:
            style_props.append(f"color: {color_code}")

        if props.get('fontWeight'):
            # Support both 'bold', 'normal' and 'w300', 'w400', etc.
            fw = props['fontWeight']
            if fw in ['bold', 'normal']:
                style_props.append(f"fontWeight: FontWeight.{fw}")
            elif fw.startswith('w'):
                style_props.append(f"fontWeight: FontWeight.{fw}")
            else:
                style_props.append(f"fontWeight: FontWeight.{fw}")

        if props.get('fontStyle'):
            style_props.append(f"fontStyle: FontStyle.{props['fontStyle']}")

        if props.get('letterSpacing'):
            style_props.append(f"letterSpacing: {props['letterSpacing']}")

        if props.get('decoration'):
            style_props.append(
                f"decoration: TextDecoration.{props['decoration']}")

        if style_props:
            code += "  style: TextStyle(\n"
            for prop in style_props:
                code += f"    {prop},\n"
            code += "  ),\n"

        # Text alignment
        if props.get('alignment'):
            code += f"  textAlign: TextAlign.{props['alignment']},\n"

        # Max lines
        if props.get('maxLines'):
            code += f"  maxLines: {props['maxLines']},\n"

        # Overflow
        if props.get('overflow'):
            code += f"  overflow: TextOverflow.{props['overflow']},\n"

        code += ")"
        return code

    def generate_container(self, data, indent_level=0):
        """Generate Container widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])
        
        # Migration logic: lift layout.w and layout.h into props if present
        layout = data.get('layout', {})
        if layout:
            if 'w' in layout and 'width' not in props:
                props['width'] = layout['w']
            if 'h' in layout and 'height' not in props:
                props['height'] = layout['h']

        code = "Container(\n"

        # Width and height from props only
        width = props.get('width')
        height = props.get('height')

        # Only add width if it's a valid number (not "auto")
        if width and width != "auto":
            if isinstance(width, (int, float)):
                code += f"  width: {float(width)},\n"
            elif isinstance(width, str) and width.replace('.', '').replace('-', '').isdigit():
                code += f"  width: {float(width)},\n"

        # Only add height if it's a valid number (not "auto")
        if height and height != "auto":
            if isinstance(height, (int, float)):
                code += f"  height: {float(height)},\n"
            elif isinstance(height, str) and height.replace('.', '').replace('-', '').isdigit():
                code += f"  height: {float(height)},\n"
        # Alignment
        if props.get('alignment'):
            code += f"  alignment: Alignment.{props['alignment']},\n"

        # Padding
        if props.get('padding'):
            padding = props['padding']
            code += f"  padding: EdgeInsets.all({padding}),\n"

        # Margin
        if props.get('margin'):
            margin = props['margin']
            code += f"  margin: EdgeInsets.all({margin}),\n"

        # Decoration (border, borderRadius, backgroundColor, etc.)
        has_decoration = any(props.get(k) for k in [
            'borderRadius', 'border', 'backgroundColor', 'boxShadow', 'gradient'
        ])

        if has_decoration:
            code += "  decoration: BoxDecoration(\n"

            # Background color
            color_code = self._parse_color(props.get('backgroundColor'))
            if color_code:
                code += f"    color: {color_code},\n"

            # Border radius
            if props.get('borderRadius'):
                code += f"    borderRadius: BorderRadius.circular({props['borderRadius']}),\n"

            # Border
            if props.get('border'):
                border_color = self._parse_color(
                    props.get('borderColor', '#000000'))
                if not border_color:
                    border_color = "Colors.grey"
                border_width = props.get('borderWidth', 1)
                code += f"    border: Border.all(color: {border_color}, width: {border_width}),\n"

            code += "  ),\n"
        elif props.get('backgroundColor'):
            # If only backgroundColor without other decoration
            color_code = self._parse_color(props.get('backgroundColor'))
            if color_code:
                code += f"  color: {color_code},\n"

        # Child
        if children:
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

        code += ")"
        return code

    def generate_row(self, data, indent_level=0):
        """Generate Row widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Row(\n"

        # Main axis size
        main_axis_size = props.get('mainAxisSize', 'max')
        code += f"  mainAxisSize: MainAxisSize.{main_axis_size},\n"

        # Main axis alignment
        if props.get('mainAxisAlignment'):
            code += f"  mainAxisAlignment: MainAxisAlignment.{props['mainAxisAlignment']},\n"

        # Cross axis alignment
        if props.get('crossAxisAlignment'):
            code += f"  crossAxisAlignment: CrossAxisAlignment.{props['crossAxisAlignment']},\n"

        # Children
        code += "  children: [\n"
        for child in children:
            child_code = self.generate_widget(child, indent_level + 2)
            code += f"    {child_code},\n"
        code += "  ],\n"
        code += ")"
        return code

    def generate_column(self, data, indent_level=0):
        """Generate Column widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Column(\n"

        # Main axis size
        main_axis_size = props.get('mainAxisSize', 'max')
        code += f"  mainAxisSize: MainAxisSize.{main_axis_size},\n"

        # Main axis alignment
        if props.get('mainAxisAlignment'):
            code += f"  mainAxisAlignment: MainAxisAlignment.{props['mainAxisAlignment']},\n"

        # Cross axis alignment
        if props.get('crossAxisAlignment'):
            code += f"  crossAxisAlignment: CrossAxisAlignment.{props['crossAxisAlignment']},\n"

        # Children
        code += "  children: [\n"
        for child in children:
            child_code = self.generate_widget(child, indent_level + 2)
            code += f"    {child_code},\n"
        code += "  ],\n"
        code += ")"
        return code

    def generate_button(self, data, indent_level=0):
        """Generate ElevatedButton widget with all supported props."""
        props = data.get('props', {})
        text = props.get('text', 'Button').replace(
            "'", "\\'").replace('$', '\\$')
        actions = props.get('actions', [])

        # Button style
        style_parts = []

        # Background color
        bg_color = self._parse_color(props.get('backgroundColor'))
        if bg_color:
            style_parts.append(
                f"backgroundColor: WidgetStateProperty.all({bg_color})")

        # Text/Foreground color
        text_color_hex = props.get('textColor') or props.get('color')
        fg_color = self._parse_color(text_color_hex)
        if fg_color:
            style_parts.append(
                f"foregroundColor: WidgetStateProperty.all({fg_color})")

        # Elevation
        if props.get('elevation') is not None:
            style_parts.append(
                f"elevation: WidgetStateProperty.all({props['elevation']})")

        # Border radius
        if props.get('borderRadius'):
            style_parts.append(
                f"shape: WidgetStateProperty.all(RoundedRectangleBorder(borderRadius: BorderRadius.circular({props['borderRadius']})))"
            )

        code = "ElevatedButton(\n"

        if style_parts:
            code += "  style: ButtonStyle(\n"
            for part in style_parts:
                code += f"    {part},\n"
            code += "  ),\n"

        # onPressed handler
        code += "  onPressed: () {\n"
        code += f"    debugPrint('Button pressed: {text}');\n"

        if actions:
            code += self.generate_action_chain(actions, indent_level + 2)
        else:
            on_press = props.get('onPress', 'handlePress')
            code += f"    debugPrint('Action: {on_press}');\n"

        code += "  },\n"
        code += f"  child: Text('{text}'),\n"
        code += ")"
        return code

    def generate_action_chain(self, actions, indent_level=0):
        """Generate action chain for buttons and interactive elements."""
        if not actions:
            return ""

        current_action = actions[0]
        remaining_actions = actions[1:]
        action_type = current_action.get('type', '')
        indent = "  " * indent_level
        code = ""

        if action_type == 'snackbar':
            message = current_action.get('message', 'Action completed').replace(
                "'", "\\'").replace('$', '\\$')
            code += f"{indent}ScaffoldMessenger.of(context).showSnackBar(\n"
            code += f"{indent}  SnackBar(content: Text('{message}')),\n"
            code += f"{indent});\n"
            if remaining_actions:
                code += self.generate_action_chain(
                    remaining_actions, indent_level)

        elif action_type == 'dialog':
            title = current_action.get('title', 'Notification').replace(
                "'", "\\'").replace('$', '\\$')
            message = current_action.get('message', '').replace(
                "'", "\\'").replace('$', '\\$')
            code += f"{indent}showDialog(\n"
            code += f"{indent}  context: context,\n"
            code += f"{indent}  builder: (context) => AlertDialog(\n"
            code += f"{indent}    title: Text('{title}'),\n"
            code += f"{indent}    content: Text('{message}'),\n"
            code += f"{indent}    actions: [\n"
            code += f"{indent}      TextButton(\n"
            code += f"{indent}        onPressed: () {{\n"
            code += f"{indent}          Navigator.pop(context);\n"
            if remaining_actions:
                code += self.generate_action_chain(
                    remaining_actions, indent_level + 5)
            code += f"{indent}        }},\n"
            code += f"{indent}        child: Text('OK'),\n"
            code += f"{indent}      ),\n"
            code += f"{indent}    ],\n"
            code += f"{indent}  ),\n"
            code += f"{indent});\n"

        elif action_type == 'navigate':
            route = current_action.get('route', '/')
            code += f"{indent}Navigator.pushNamed(context, '{route}');\n"
            code += self.generate_action_chain(remaining_actions, indent_level)

        elif action_type == 'goBack' or current_action.get('go_back'):
            code += f"{indent}Navigator.pop(context);\n"
            code += self.generate_action_chain(remaining_actions, indent_level)

        return code

    def generate_image(self, data, indent_level=0):
        """Generate Image widget with all supported props."""
        props = data.get('props', {})
        src = props.get('src', 'https://via.placeholder.com/150')
        fit = props.get('fit', 'cover')
        width = props.get('width')
        height = props.get('height')

        # Determine image source type
        img_method = "network" if src.startswith('http') else "asset"

        code = f"Image.{img_method}(\n"
        code += f"  '{src}',\n"
        code += f"  fit: BoxFit.{fit},\n"

        if width:
            code += f"  width: {width},\n"
        if height:
            code += f"  height: {height},\n"

        code += ")"
        return code

    def generate_appbar(self, data, indent_level=0):
        """Generate AppBar widget with all supported props."""
        props = data.get('props', {})
        title = props.get('title', 'App').replace(
            "'", "\\'").replace('$', '\\$')

        code = "AppBar(\n"

        # Title with optional color
        title_color = self._parse_color(props.get('color'))
        if title_color:
            code += f"  title: Text('{title}', style: TextStyle(color: {title_color})),\n"
        else:
            code += f"  title: Text('{title}'),\n"

        # Center title
        code += f"  centerTitle: {str(props.get('centerTitle', False)).lower()},\n"

        # Back button
        if props.get('showBackButton'):
            code += "  leading: IconButton(\n"
            code += "    icon: const Icon(Icons.arrow_back),\n"
            code += "    onPressed: () => Navigator.of(context).pop(),\n"
            code += "  ),\n"
        elif props.get('automaticallyImplyLeading') is False:
            code += "  automaticallyImplyLeading: false,\n"

        # Background color
        bg_color = self._parse_color(props.get('backgroundColor'))
        if bg_color:
            code += f"  backgroundColor: {bg_color},\n"

        # Elevation
        if props.get('elevation') is not None:
            code += f"  elevation: {props['elevation']},\n"

        code += ")"
        return code

    def generate_scaffold(self, data, indent_level=0):
        """Generate Scaffold widget with all supported props and automatic overflow prevention."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Scaffold(\n"

        # Extract special components (don't modify original children list yet)
        appbar = next((c for c in children if c.get('type') == 'AppBar'), None)
        bottom_nav = next((c for c in children if c.get(
            'type') == 'BottomNavigationBar'), None)
        drawer = next((c for c in children if c.get('type') == 'Drawer'), None)

        # Filter out the special components to get body components
        body_children = [c for c in children if c.get(
            'type') not in ['AppBar', 'BottomNavigationBar', 'Drawer']]

        # AppBar
        if appbar:
            code += f"  appBar: {self.generate_widget(appbar, indent_level + 1)},\n"

        # Background color
        bg_color = self._parse_color(props.get('backgroundColor'))
        if bg_color:
            code += f"  backgroundColor: {bg_color},\n"

        # Drawer
        if drawer:
            code += f"  drawer: {self.generate_widget(drawer, indent_level + 1)},\n"

        # Body - ALWAYS wrap in SingleChildScrollView to prevent overflow errors
        if body_children:
            body_widget = None

            if len(body_children) > 1:
                # Multiple children - wrap in a Column
                body_widget = {
                    'type': 'Column',
                    'children': body_children,
                    'props': {'crossAxisAlignment': 'start'}
                }
            else:
                body_widget = body_children[0]

            # Check if body is already a scrollable widget
            body_type = body_widget.get('type', '')
            scrollable_widgets = ['ListView', 'GridView',
                                  'CustomScrollView', 'SingleChildScrollView']

            if body_type in scrollable_widgets:
                # Already scrollable, don't double-wrap
                code += f"  body: {self.generate_widget(body_widget, indent_level + 1)},\n"
            else:
                # Wrap using LayoutBuilder + ConstrainedBox(minHeight) instead of a bare
                # SingleChildScrollView, which gives its child UNBOUNDED height and
                # silently breaks Center/Expanded/anything that needs to fill space
                inner = self.generate_widget(body_widget, indent_level + 3)
                code += "  body: LayoutBuilder(\n"
                code += "    builder: (context, constraints) {\n"
                code += "      return SingleChildScrollView(\n"
                code += "        child: ConstrainedBox(\n"
                code += "          constraints: BoxConstraints(minHeight: constraints.maxHeight),\n"
                code += f"          child: {inner},\n"
                code += "        ),\n"
                code += "      );\n"
                code += "    },\n"
                code += "  ),\n"

        # Bottom navigation bar (comes AFTER body)
        if bottom_nav:
            code += f"  bottomNavigationBar: {self.generate_widget(bottom_nav, indent_level + 1)},\n"

        code += ")"
        return code

    def generate_bottom_navigation_bar(self, data, indent_level=0):
        """Generate BottomNavigationBar widget with all supported props."""
        props = data.get('props', {})
        items = data.get('items', [])

        if not items:
            return "Container()"

        code = "BottomNavigationBar(\n"

        # Current index - DYNAMIC
        code += "  currentIndex: () {\n"
        code += "    final currentRoute = ModalRoute.of(context)?.settings.name;\n"
        for i, item in enumerate(items):
            route = item.get('route', '/')
            code += f"    if (currentRoute == '{route}') return {i};\n"
        code += "    return 0;\n"
        code += "  }(),\n"

        # Type
        if props.get('type'):
            code += f"  type: BottomNavigationBarType.{props['type']},\n"

        # Colors
        selected_color = self._parse_color(props.get('selectedItemColor'))
        if selected_color:
            code += f"  selectedItemColor: {selected_color},\n"

        unselected_color = self._parse_color(props.get('unselectedItemColor'))
        if unselected_color:
            code += f"  unselectedItemColor: {unselected_color},\n"

        # onTap handler
        code += "  onTap: (index) {\n"
        code += "    final routes = [\n"
        for item in items:
            route = item.get('route', '/')
            code += f"      '{route}',\n"
        code += "    ];\n"
        code += "    if (index < routes.length) {\n"
        code += "      final targetRoute = routes[index];\n"
        code += "      final currentRoute = ModalRoute.of(context)?.settings.name;\n"
        code += "      if (currentRoute != targetRoute) {\n"
        code += "        Navigator.pushReplacementNamed(context, targetRoute);\n"
        code += "      }\n"
        code += "    }\n"
        code += "  },\n"

        # Items
        code += "  items: [\n"
        for item in items:
            label = item.get('label', 'Item').replace("'", "\\'")
            icon = item.get('icon', 'home')
            code += "    BottomNavigationBarItem(\n"
            code += f"      icon: Icon(Icons.{icon}),\n"
            code += f"      label: '{label}',\n"
            code += "    ),\n"
        code += "  ],\n"
        code += ")"
        return code

    def generate_drawer(self, data, indent_level=0):
        """Generate Drawer widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Drawer(\n"
        code += "  child: ListView(\n"
        code += "    padding: EdgeInsets.zero,\n"
        code += "    children: [\n"

        # Drawer header
        header = props.get('header')
        if header:
            title = header.get('title', 'Menu').replace("'", "\\'")
            subtitle = header.get('subtitle', '').replace("'", "\\'")
            bg_color = self._parse_color(header.get('backgroundColor'))

            code += "      DrawerHeader(\n"
            if bg_color:
                code += f"        decoration: BoxDecoration(color: {bg_color}),\n"
            code += "        child: Column(\n"
            code += "          crossAxisAlignment: CrossAxisAlignment.start,\n"
            code += "          mainAxisAlignment: MainAxisAlignment.center,\n"
            code += "          children: [\n"
            code += f"            Text('{title}', style: TextStyle(color: Colors.white, fontSize: 24)),\n"
            if subtitle:
                code += "            SizedBox(height: 8),\n"
                code += f"            Text('{subtitle}', style: TextStyle(color: Colors.white70, fontSize: 14)),\n"
            code += "          ],\n"
            code += "        ),\n"
            code += "      ),\n"

        # Drawer children (usually ListTiles)
        for child in children:
            if child.get('type') == 'ListTile':
                c_props = child.get('props', {})
                title = c_props.get('title', 'Item').replace("'", "\\'")
                icon = c_props.get('icon')
                actions = c_props.get('actions', [])

                code += "      ListTile(\n"
                if icon:
                    code += f"        leading: Icon(Icons.{icon}),\n"
                code += f"        title: Text('{title}'),\n"
                code += "        onTap: () {\n"
                code += "          Navigator.pop(context);\n"
                if actions:
                    code += self.generate_action_chain(
                        actions, indent_level + 5)
                code += "        },\n"
                code += "      ),\n"
            else:
                code += f"      {self.generate_widget(child, indent_level + 3)},\n"

        code += "    ],\n"
        code += "  ),\n"
        code += ")"
        return code

    def generate_listtile(self, data, indent_level=0):
        """Generate ListTile widget with all supported props."""
        props = data.get('props', {})

        code = "ListTile(\n"

        # Leading icon
        if props.get('icon'):
            icon = props.get('icon')
            code += f"  leading: Icon(Icons.{icon}),\n"

        # Title
        title = props.get('title', 'List Item').replace("'", "\\'")
        code += f"  title: Text('{title}'),\n"

        # Subtitle
        if props.get('subtitle'):
            subtitle = props.get('subtitle', '').replace("'", "\\'")
            code += f"  subtitle: Text('{subtitle}'),\n"

        # Trailing icon
        if props.get('trailingIcon'):
            trailing_icon = props.get('trailingIcon')
            code += f"  trailing: Icon(Icons.{trailing_icon}),\n"

        # onTap handler with actions
        actions = props.get('actions', [])
        if actions:
            code += "  onTap: () {\n"
            code += self.generate_action_chain(actions, indent_level + 2)
            code += "  },\n"

        code += ")"
        return code

    def generate_listview(self, data, indent_level=0):
        """Generate ListView.builder widget with all supported props."""
        props = data.get('props', {})
        item_template = data.get('itemTemplate', {})
        item_count = props.get('itemCount', 10)

        code = "ListView.builder(\n"
        code += f"  shrinkWrap: {str(props.get('shrinkWrap', True)).lower()},\n"
        code += f"  padding: EdgeInsets.all({props.get('padding', 0)}),\n"
        code += f"  itemCount: {item_count},\n"
        code += f"  itemBuilder: (context, index) => {self.generate_widget(item_template, indent_level + 2)},\n"
        code += ")"
        return code

    def generate_card(self, data, indent_level=0):
        """Generate Card widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Card(\n"

        # Elevation
        if props.get('elevation') is not None:
            code += f"  elevation: {props['elevation']},\n"

        # Color
        color = self._parse_color(props.get('color'))
        if color:
            code += f"  color: {color},\n"

        # Margin
        if props.get('margin'):
            code += f"  margin: EdgeInsets.all({props['margin']}),\n"

        # Border radius via shape
        if props.get('borderRadius'):
            code += "  shape: RoundedRectangleBorder(\n"
            code += f"    borderRadius: BorderRadius.circular({props['borderRadius']}),\n"
            code += "  ),\n"

        # Child
        if children:
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

        code += ")"
        return code

    def generate_textfield(self, data, indent_level=0):
        """Generate TextField widget with all supported props."""
        props = data.get('props', {})

        code = "TextField(\n"

        # Obscure text (for passwords)
        code += f"  obscureText: {str(props.get('obscureText', False)).lower()},\n"

        # Keyboard type
        keyboard_type = props.get('keyboardType', 'text')
        code += f"  keyboardType: TextInputType.{keyboard_type},\n"

        # Decoration
        code += "  decoration: InputDecoration(\n"

        if props.get('hintText'):
            hint = props['hintText'].replace("'", "\\'")
            code += f"    hintText: '{hint}',\n"

        if props.get('labelText'):
            label = props['labelText'].replace("'", "\\'")
            code += f"    labelText: '{label}',\n"

        if props.get('border'):
            code += "    border: OutlineInputBorder(),\n"

        if props.get('prefixIcon'):
            code += f"    prefixIcon: Icon(Icons.{props['prefixIcon']}),\n"

        code += "  ),\n"
        code += ")"
        return code

    def generate_icon(self, data, indent_level=0):
        """Generate Icon widget with all supported props."""
        props = data.get('props', {})
        icon = props.get('icon', 'star')

        code = f"Icon(Icons.{icon}"

        params = []

        if props.get('size'):
            params.append(f"size: {props['size']}")

        color = self._parse_color(props.get('color'))
        if color:
            params.append(f"color: {color}")

        if params:
            code += ", " + ", ".join(params)

        code += ")"
        return code

    def generate_padding(self, data, indent_level=0):
        """Generate Padding widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])
        padding = props.get('padding', 8)

        code = "Padding(\n"
        code += f"  padding: EdgeInsets.all({padding}),\n"

        if children:
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

        code += ")"
        return code

    def generate_center(self, data, indent_level=0):
        """Generate Center widget."""
        children = data.get('children', [])

        code = "Center(\n"

        if children:
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

        code += ")"
        return code

    def generate_stack(self, data, indent_level=0):
        """Generate Stack widget with all supported props."""
        children = data.get('children', [])

        code = "Stack(\n"
        code += "  children: [\n"

        for child in children:
            code += f"    {self.generate_widget(child, indent_level + 2)},\n"

        code += "  ],\n"
        code += ")"
        return code

    def generate_positioned(self, data, indent_level=0):
        """Generate Positioned widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Positioned(\n"

        # Position properties
        for k in ['top', 'left', 'right', 'bottom', 'width', 'height']:
            if props.get(k) is not None:
                code += f"  {k}: {props[k]},\n"

        # Child
        if children:
            code += f"  child: {self.generate_widget(children[0], indent_level + 1)},\n"

        code += ")"
        return code

    def generate_expanded(self, data, indent_level=0):
        """Generate Expanded widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Expanded(\n"

        # Flex property
        if props.get('flex'):
            code += f"  flex: {props['flex']},\n"

        # Child
        if children:
            code += f"  child: {self.generate_widget(children[0], indent_level + 1)},\n"

        code += ")"
        return code

    def generate_sizedbox(self, data, indent_level=0):
        """Generate SizedBox widget with all supported props."""
        props = data.get('props', {})
        children = data.get('children', [])

        code = "SizedBox(\n"

        # Width
        if props.get('width'):
            code += f"  width: {props['width']},\n"

        # Height
        if props.get('height'):
            code += f"  height: {props['height']},\n"

        # Child
        if children:
            code += f"  child: {self.generate_widget(children[0], indent_level + 1)},\n"

        code += ")"
        return code

    def generate_unknown(self, data, indent_level=0):
        """Generate placeholder for unknown widgets."""
        widget_type = data.get('type', 'Unknown')
        return f"// TODO: Implement {widget_type} widget\nContainer()"
