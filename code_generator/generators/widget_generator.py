
class WidgetGenerator:

    def __init__(self):
        pass  # Don't store state at instance level

    def generate_widget(self, widget_data, indent_level=0):
        widget_type = widget_data.get('type', '')

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
        }

        generator = generators.get(widget_type, self.generate_unknown)
        return generator(widget_data, indent_level)

    def indent(self, code, level):
        if not code:
            return code
        spaces = ' ' * (level * 2)
        lines = code.split('\n')
        return '\n'.join(spaces + line if line.strip() else line for line in lines)

    def _parse_color(self, color_str):
        if not color_str:
            return None
        color = color_str.lstrip('#')
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        if len(color) == 6:
            color = 'FF' + color
        return f"Color(0x{color})"

    def generate_text(self, data, indent_level=0):
        props = data.get('props', {})
        text = props.get('text', 'Text').replace(
            "'", "\\'").replace('$', '\\$')

        code = f"Text(\n"
        code += f"  '{text}',\n"

        style_props = []
        if props.get('fontSize'):
            style_props.append(f"fontSize: {props['fontSize']}")

        color_code = self._parse_color(props.get('color'))
        if color_code:
            style_props.append(f"color: {color_code}")

        if props.get('fontWeight'):
            style_props.append(f"fontWeight: FontWeight.{props['fontWeight']}")
        if props.get('fontStyle'):
            style_props.append(f"fontStyle: FontStyle.{props['fontStyle']}")
        if props.get('letterSpacing'):
            style_props.append(f"letterSpacing: {props['letterSpacing']}")
        if props.get('decoration'):
            style_props.append(
                f"decoration: TextDecoration.{props['decoration']}")

        if style_props:
            code += f"  style: TextStyle(\n"
            for prop in style_props:
                code += f"    {prop},\n"
            code += f"  ),\n"

        if props.get('alignment'):
            code += f"  textAlign: TextAlign.{props['alignment']},\n"
        if props.get('maxLines'):
            code += f"  maxLines: {props['maxLines']},\n"
        if props.get('overflow'):
            code += f"  overflow: TextOverflow.{props['overflow']},\n"

        code += ")"
        return code

    def generate_container(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        layout = data.get('layout', {})

        code = "Container(\n"

        if layout.get('w'):
            code += f"  width: {float(layout['w'])},\n"
        if layout.get('h'):
            code += f"  height: {float(layout['h'])},\n"

        if props.get('alignment'):
            code += f"  alignment: Alignment.{props['alignment']},\n"

        if props.get('padding'):
            padding = props['padding']
            code += f"  padding: EdgeInsets.all({padding}),\n"

        if props.get('margin'):
            margin = props['margin']
            code += f"  margin: EdgeInsets.all({margin}),\n"

        has_decoration = any(props.get(k) for k in [
                             'borderRadius', 'border', 'backgroundColor', 'boxShadow', 'gradient'])

        if has_decoration:
            code += f"  decoration: BoxDecoration(\n"
            color_code = self._parse_color(props.get('backgroundColor'))
            if color_code:
                code += f"    color: {color_code},\n"

            if props.get('borderRadius'):
                code += f"    borderRadius: BorderRadius.circular({props['borderRadius']}),\n"

            if props.get('border'):
                border_color = self._parse_color(
                    props.get('borderColor')) or "Colors.grey"
                border_width = props.get('borderWidth', 1)
                code += f"    border: Border.all(color: {border_color}, width: {border_width}),\n"

            code += f"  ),\n"
        elif props.get('backgroundColor'):
            color_code = self._parse_color(props.get('backgroundColor'))
            code += f"  color: {color_code},\n"

        if children:
            if len(children) == 1:
                child_code = self.generate_widget(
                    children[0], indent_level + 1)
                code += f"  child: {child_code},\n"
            else:
                code += f"  child: Column(\n"
                code += f"    mainAxisSize: MainAxisSize.min,\n"
                code += f"    children: [\n"
                for child in children:
                    child_code = self.generate_widget(child, indent_level + 2)
                    code += f"      {child_code},\n"
                code += f"    ],\n"
                code += f"  ),\n"

        code += ")"
        return code

    def generate_row(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Row(\n"

        # In Flutter, Row takes max width by default.
        # If user explicitly sets mainAxisSize to min, we honor it.
        main_axis_size = props.get('mainAxisSize', 'max')
        code += f"  mainAxisSize: MainAxisSize.{main_axis_size},\n"

        if props.get('mainAxisAlignment'):
            code += f"  mainAxisAlignment: MainAxisAlignment.{props['mainAxisAlignment']},\n"
        if props.get('crossAxisAlignment'):
            code += f"  crossAxisAlignment: CrossAxisAlignment.{props['crossAxisAlignment']},\n"

        code += f"  children: [\n"
        for child in children:
            child_code = self.generate_widget(child, indent_level + 2)
            code += f"    {child_code},\n"
        code += f"  ],\n"
        code += ")"
        return code

    def generate_column(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Column(\n"

        # In Flutter, Column takes max height by default.
        # If user explicitly sets mainAxisSize to min, we honor it.
        main_axis_size = props.get('mainAxisSize', 'max')
        code += f"  mainAxisSize: MainAxisSize.{main_axis_size},\n"

        if props.get('mainAxisAlignment'):
            code += f"  mainAxisAlignment: MainAxisAlignment.{props['mainAxisAlignment']},\n"
        if props.get('crossAxisAlignment'):
            code += f"  crossAxisAlignment: CrossAxisAlignment.{props['crossAxisAlignment']},\n"

        code += f"  children: [\n"
        for child in children:
            child_code = self.generate_widget(child, indent_level + 2)
            code += f"    {child_code},\n"
        code += f"  ],\n"
        code += ")"
        return code

    def generate_button(self, data, indent_level=0):
        props = data.get('props', {})
        text = props.get('text', 'Button').replace(
            "'", "\\'").replace('$', '\\$')
        actions = props.get('actions', [])

        # Button Style
        style_parts = []
        bg_color = self._parse_color(props.get('backgroundColor'))
        if bg_color:
            style_parts.append(
                f"backgroundColor: MaterialStateProperty.all({bg_color})")
        fg_color = self._parse_color(props.get('color'))
        if fg_color:
            style_parts.append(
                f"foregroundColor: MaterialStateProperty.all({fg_color})")
        if props.get('elevation') is not None:
            style_parts.append(
                f"elevation: MaterialStateProperty.all({props['elevation']})")
        if props.get('borderRadius'):
            style_parts.append(
                f"shape: MaterialStateProperty.all(RoundedRectangleBorder(borderRadius: BorderRadius.circular({props['borderRadius']})))")

        code = "ElevatedButton(\n"
        if style_parts:
            code += "  style: ButtonStyle(\n"
            for part in style_parts:
                code += f"    {part},\n"
            code += "  ),\n"

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
            code += f"{indent}ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('{message}')));\n"
            code += self.generate_action_chain(remaining_actions, indent_level)
        elif action_type == 'dialog':
            title = current_action.get('title', 'Notification').replace(
                "'", "\\'").replace('$', '\\$')
            message = current_action.get('message', '').replace(
                "'", "\\'").replace('$', '\\$')
            code += f"{indent}showDialog(context: context, builder: (context) => AlertDialog(\n"
            code += f"{indent}  title: Text('{title}'), content: Text('{message}'),\n"
            code += f"{indent}  actions: [TextButton(onPressed: () {{ Navigator.pop(context);\n"
            if remaining_actions:
                code += self.generate_action_chain(
                    remaining_actions, indent_level + 2)
            code += f"{indent}  }}, child: Text('OK'))],\n"
            code += f"{indent}));\n"
        elif action_type == 'navigate':
            route = current_action.get('route', '/')
            code += f"{indent}Navigator.pushNamed(context, '{route}');\n"
            code += self.generate_action_chain(remaining_actions, indent_level)
        elif action_type == 'goBack' or current_action.get('go_back'):
            code += f"{indent}Navigator.pop(context);\n"
            code += self.generate_action_chain(remaining_actions, indent_level)
        return code

    def generate_image(self, data, indent_level=0):
        props = data.get('props', {})
        src = props.get('src', 'https://via.placeholder.com/150')
        fit = props.get('fit', 'cover')
        width = props.get('width')
        height = props.get('height')

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
        props = data.get('props', {})
        title = props.get('title', 'App').replace(
            "'", "\\'").replace('$', '\\$')
        code = "AppBar(\n"
        code += f"  title: Text('{title}'),\n"
        code += f"  centerTitle: {str(props.get('centerTitle', False)).lower()},\n"
        bg_color = self._parse_color(props.get('backgroundColor'))
        if bg_color:
            code += f"  backgroundColor: {bg_color},\n"
        if props.get('elevation') is not None:
            code += f"  elevation: {props['elevation']},\n"
        code += ")"
        return code

    def generate_scaffold(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        code = "Scaffold(\n"
        appbar = next((c for c in children if c.get('type') == 'AppBar'), None)
        if appbar:
            code += f"  appBar: {self.generate_widget(appbar, indent_level + 1)},\n"
            children = [c for c in children if c.get('type') != 'AppBar']

        bg_color = self._parse_color(props.get('backgroundColor'))
        if bg_color:
            code += f"  backgroundColor: {bg_color},\n"

        if children:
            body_child = children[0] if len(children) == 1 else {
                'type': 'Column', 'children': children, 'props': {'crossAxisAlignment': 'start'}}
            code += f"  body: {self.generate_widget(body_child, indent_level + 1)},\n"
        code += ")"
        return code

    def generate_listview(self, data, indent_level=0):
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
        props = data.get('props', {})
        children = data.get('children', [])
        code = "Card(\n"
        if props.get('elevation') is not None:
            code += f"  elevation: {props['elevation']},\n"
        color = self._parse_color(props.get('color'))
        if color:
            code += f"  color: {color},\n"
        if props.get('margin'):
            code += f"  margin: EdgeInsets.all({props['margin']}),\n"
        if props.get('borderRadius'):
            code += f"  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular({props['borderRadius']})),\n"

        if children:
            child_code = self.generate_widget(children[0] if len(children) == 1 else {
                                              'type': 'Column', 'children': children}, indent_level + 1)
            code += f"  child: {child_code},\n"
        code += ")"
        return code

    def generate_textfield(self, data, indent_level=0):
        props = data.get('props', {})
        code = "TextField(\n"
        code += f"  obscureText: {str(props.get('obscureText', False)).lower()},\n"
        code += f"  keyboardType: TextInputType.{props.get('keyboardType', 'text')},\n"
        code += "  decoration: InputDecoration(\n"
        if props.get('hintText'):
            code += f"    hintText: '{props['hintText']}',\n"
        if props.get('labelText'):
            code += f"    labelText: '{props['labelText']}',\n"
        if props.get('border'):
            code += "    border: OutlineInputBorder(),\n"
        if props.get('prefixIcon'):
            code += f"    prefixIcon: Icon(Icons.{props['prefixIcon']}),\n"
        code += "  ),\n"
        code += ")"
        return code

    def generate_icon(self, data, indent_level=0):
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
        props = data.get('props', {})
        children = data.get('children', [])
        padding = props.get('padding', 8)
        code = f"Padding(padding: EdgeInsets.all({padding}),\n"
        if children:
            child_code = self.generate_widget(children[0] if len(children) == 1 else {
                                              'type': 'Column', 'children': children}, indent_level + 1)
            code += f"  child: {child_code},\n"
        code += ")"
        return code

    def generate_center(self, data, indent_level=0):
        children = data.get('children', [])
        code = "Center(\n"
        if children:
            child_code = self.generate_widget(children[0] if len(children) == 1 else {
                                              'type': 'Column', 'children': children}, indent_level + 1)
            code += f"  child: {child_code},\n"
        code += ")"
        return code

    def generate_stack(self, data, indent_level=0):
        children = data.get('children', [])
        code = "Stack(\n"
        code += "  children: [\n"
        for child in children:
            code += f"    {self.generate_widget(child, indent_level + 2)},\n"
        code += "  ],\n"
        code += ")"
        return code

    def generate_positioned(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        code = "Positioned(\n"
        for k in ['top', 'left', 'right', 'bottom', 'width', 'height']:
            if props.get(k) is not None:
                code += f"  {k}: {props[k]},\n"
        if children:
            code += f"  child: {self.generate_widget(children[0], indent_level + 1)},\n"
        code += ")"
        return code

    def generate_expanded(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        code = "Expanded(\n"
        if props.get('flex'):
            code += f"  flex: {props['flex']},\n"
        if children:
            code += f"  child: {self.generate_widget(children[0], indent_level + 1)},\n"
        code += ")"
        return code

    def generate_sizedbox(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        code = "SizedBox(\n"
        if props.get('width'):
            code += f"  width: {props['width']},\n"
        if props.get('height'):
            code += f"  height: {props['height']},\n"
        if children:
            code += f"  child: {self.generate_widget(children[0], indent_level + 1)},\n"
        code += ")"
        return code

    def generate_unknown(self, data, indent_level=0):
        widget_type = data.get('type', 'Unknown')
        return f"// TODO: Implement {widget_type} widget\nContainer()"
