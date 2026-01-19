
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

    def generate_text(self, data, indent_level=0):
        props = data.get('props', {})
        text = props.get('text', 'Text').replace(
            "'", "\\'").replace('$', '\\$')

        code = f"Text(\n"
        code += f"  '{text}',\n"

        style_props = []
        if props.get('fontSize'):
            style_props.append(f"fontSize: {props['fontSize']}")
        if props.get('color'):
            color = props['color'].lstrip('#')
            if len(color) == 4:
                color = 'FF' + color
            style_props.append(f"color: Color(0x{color})")
        if props.get('fontWeight'):
            style_props.append(f"fontWeight: FontWeight.{props['fontWeight']}")

        if style_props:
            code += f"  style: TextStyle(\n"
            for prop in style_props:
                code += f"    {prop},\n"
            code += f"  ),\n"

        if props.get('alignment'):
            code += f"  textAlign: TextAlign.{props['alignment']},\n"

        code += ")"
        return code

    def generate_container(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        layout = data.get('layout', {})

        code = "Container(\n"

        # Width and Height from layout
        if layout.get('w'):
            code += f"  width: {float(layout['w'])},\n"
        if layout.get('h'):
            code += f"  height: {float(layout['h'])},\n"

        # Padding
        if props.get('padding'):
            padding = props['padding']
            code += f"  padding: EdgeInsets.all({padding}),\n"

        # Margin
        if props.get('margin'):
            margin = props['margin']
            code += f"  margin: EdgeInsets.all({margin}),\n"

        # Background Color (only if no decoration)
        has_decoration = props.get('borderRadius') or props.get('border')
        if props.get('backgroundColor') and not has_decoration:
            color = props['backgroundColor'].lstrip('#')
            if len(color) == 4:
                color = 'FF' + color
            code += f"  color: Color(0x{color}),\n"

        # Decoration (for borders, borderRadius, or backgroundColor with decoration)
        if has_decoration:
            code += f"  decoration: BoxDecoration(\n"

            if props.get('backgroundColor'):
                color = props['backgroundColor'].lstrip('#')
                if len(color) == 4:
                    color = 'FF' + color
                code += f"    color: Color(0x{color}),\n"

            if props.get('borderRadius'):
                code += f"    borderRadius: BorderRadius.circular({props['borderRadius']}),\n"

            if props.get('border'):
                code += f"    border: Border.all(\n"
                code += f"      color: Colors.grey,\n"
                code += f"      width: 1,\n"
                code += f"    ),\n"

            code += f"  ),\n"

        # Child
        if children:
            if len(children) == 1:
                child_code = self.generate_widget(
                    children[0], indent_level + 1)
                code += f"  child: {child_code},\n"
            else:
                # Simplified: Just use a Column. Let the screen-level scroll handle it.
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

        # Check if any child is Expanded or Flexible
        has_flex_child = any(
            c.get('type') in ['Expanded', 'Flexible'] for c in children)

        # Check if we should auto-wrap Text in Flexible to prevent overflow
        should_auto_wrap_text = len(children) > 1 and any(
            c.get('type') == 'Text' for c in children)

        # Base Row code
        code = "Row(\n"
        code += "  mainAxisSize: MainAxisSize.min,\n"
        if props.get('mainAxisAlignment'):
            code += f"  mainAxisAlignment: MainAxisAlignment.{props['mainAxisAlignment']},\n"
        if props.get('crossAxisAlignment'):
            code += f"  crossAxisAlignment: CrossAxisAlignment.{props['crossAxisAlignment']},\n"
        code += f"  children: [\n"
        for child in children:
            if child.get('type') == 'Text' and not has_flex_child:
                child_code = self.generate_widget(child, indent_level + 3)
                code += f"    Flexible(child: {child_code}),\n"
            else:
                child_code = self.generate_widget(child, indent_level + 2)
                code += f"    {child_code},\n"
        code += f"  ],\n"
        code += ")"

        # Only wrap in horizontal scroll if it's a simple row with NO flexible children
        if not (has_flex_child or should_auto_wrap_text):
            scroll_code = "SingleChildScrollView(\n"
            scroll_code += "  scrollDirection: Axis.horizontal,\n"
            scroll_code += f"  child: {code},\n"
            scroll_code += ")"
            return scroll_code

        return code

    def generate_column(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Column(\n"
        code += "  mainAxisSize: MainAxisSize.min,\n"
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

    # Action props for the Button widget(Chain action support)

    def generate_button(self, data, indent_level=0):
        props = data.get('props', {})
        text = props.get('text', 'Button').replace(
            "'", "\\'").replace('$', '\\$')

        # Get actions list from props
        actions = props.get('actions', [])

        # Backward compatibility for single action props
        if not actions:
            if props.get('navigateTo'):
                actions.append({
                    'type': 'navigate',
                    'route': props.get('navigateTo')
                })
            if props.get('showSnackbar'):
                actions.append({
                    'type': 'snackbar',
                    'message': props.get('snackbarMessage', 'Action completed')
                })
            if props.get('showDialog'):
                actions.append({
                    'type': 'dialog',
                    'title': props.get('dialogTitle', 'Notification'),
                    'message': props.get('dialogMessage', 'Message')
                })
            if props.get('goBack') or props.get('go_back'):
                actions.append({
                    'type': 'goBack'
                })

        code = "ElevatedButton(\n"
        code += "  onPressed: () {\n"
        code += f"    debugPrint('Button pressed: {text}');\n"
        if actions:
            # Generate the recursive action chain
            action_chain_code = self.generate_action_chain(
                actions, indent_level + 2)
            code += action_chain_code
        else:
            # Default empty handler - Use debugPrint instead of calling undefined functions
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
            message = current_action.get(
                'message', 'Action completed').replace("'", "\\'").replace('$', '\\$')
            code += f"{indent}ScaffoldMessenger.of(context).showSnackBar(\n"
            code += f"{indent}  SnackBar(content: Text('{message}')),\n"
            code += f"{indent});\n"
            # Snackbars are non-blocking, continue to next action
            code += self.generate_action_chain(remaining_actions, indent_level)

        elif action_type == 'dialog':
            title = current_action.get(
                'title', 'Notification').replace("'", "\\'").replace('$', '\\$')
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
            code += f"{indent}          Navigator.pop(context); // Close dialog\n"

            # NEST remaining actions inside the dialog's OK button
            if remaining_actions:
                code += self.generate_action_chain(
                    remaining_actions, indent_level + 5)

            code += f"{indent}        }},\n"
            code += f"{indent}        child: Text('OK'),\n"
            code += f"{indent}      ),\n"
            code += f"{indent}    ],\n"
            code += f"{indent}  ),\n"
            code += f"{indent});\n"
            # Dialog is blocking, so we STOP here. Remaining actions are nested inside.

        elif action_type == 'navigate':
            route = current_action.get('route', '/')
            code += f"{indent}Navigator.pushNamed(context, '{route}');\n"
            # Navigation is terminal for the current screen, but we can still chain if needed
            code += self.generate_action_chain(remaining_actions, indent_level)

        elif action_type == 'goBack' or current_action.get('go_back'):
            code += f"{indent}Navigator.pop(context);\n"
            code += self.generate_action_chain(remaining_actions, indent_level)

        return code

    def generate_image(self, data, indent_level=0):
        props = data.get('props', {})
        src = props.get('src', '')
        fit = props.get('fit', 'cover')

        if src.startswith('http'):
            code = f"Image.network(\n"
            code += f"  '{src}',\n"
            code += f"  fit: BoxFit.{fit},\n"
            code += ")"
        else:
            code = f"Image.asset(\n"
            code += f"  '{src}',\n"
            code += f"  fit: BoxFit.{fit},\n"
            code += ")"

        return code

    def generate_appbar(self, data, indent_level=0):
        props = data.get('props', {})
        title = props.get('title', 'App').replace(
            "'", "\\'").replace('$', '\\$')

        code = "AppBar(\n"
        code += f"  title: Text('{title}'),\n"

        if props.get('backgroundColor'):
            color = props['backgroundColor'].lstrip('#')
            if len(color) == 4:
                color = 'FF' + color
            code += f"  backgroundColor: Color(0x{color}),\n"

        if props.get('elevation') is not None:
            code += f"  elevation: {props['elevation']},\n"

        code += ")"
        return code

    def generate_scaffold(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Scaffold(\n"

        # Find AppBar in children
        appbar = next((c for c in children if c.get('type') == 'AppBar'), None)
        if appbar:
            appbar_code = self.generate_widget(appbar, indent_level + 1)
            code += f"  appBar: {appbar_code},\n"
            children = [c for c in children if c.get('type') != 'AppBar']

        # Body
        if children:
            if len(children) == 1 and children[0].get('type') == 'ListView':
                body_code = self.generate_widget(children[0], indent_level + 1)
                code += f"  body: {body_code},\n"
            else:
                code += f"  body: SingleChildScrollView(\n"
                code += f"    child: Column(\n"
                code += f"      mainAxisSize: MainAxisSize.min,\n"
                code += f"      crossAxisAlignment: CrossAxisAlignment.start,\n"
                code += f"      children: [\n"
                for child in children:
                    child_code = self.generate_widget(child, indent_level + 3)
                    code += f"        {child_code},\n"
                code += f"      ],\n"
                code += f"    ),\n"
                code += f"  ),\n"

        code += ")"
        return code

    def generate_listview(self, data, indent_level=0):
        props = data.get('props', {})
        item_template = data.get('itemTemplate', {})
        item_count = props.get('itemCount', 10)

        code = "ListView.builder(\n"
        code += "  shrinkWrap: true,\n"
        code += "  physics: const NeverScrollableScrollPhysics(),\n"
        code += f"  itemCount: {item_count},\n"
        code += f"  itemBuilder: (context, index) => {self.generate_widget(item_template, indent_level + 2)},\n"
        code += ")"

        return code

    def generate_card(self, data, indent_level=0):
        children = data.get('children', [])
        props = data.get('props', {})

        code = "Card(\n"

        if props.get('elevation') is not None:
            code += f"  elevation: {props['elevation']},\n"

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

    def generate_textfield(self, data, indent_level=0):
        props = data.get('props', {})

        code = "TextField(\n"

        if props.get('hintText'):
            hint = props['hintText'].replace("'", "\\'").replace('$', '\\$')
            code += f"  decoration: InputDecoration(\n"
            code += f"    hintText: '{hint}',\n"
            code += f"  ),\n"

        code += ")"
        return code

    def generate_icon(self, data, indent_level=0):
        props = data.get('props', {})
        icon = props.get('icon', 'star')

        code = f"Icon(Icons.{icon}"

        params = []
        if props.get('size'):
            params.append(f"size: {props['size']}")

        if props.get('color'):
            color = props['color'].lstrip('#')
            if len(color) == 4:
                color = 'FF' + color
            params.append(f"color: Color(0x{color})")

        if params:
            code += ", " + ", ".join(params)

        code += ")"
        return code

    def generate_padding(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])
        padding = props.get('padding', 8)

        code = f"Padding(\n"
        code += f"  padding: EdgeInsets.all({padding}),\n"

        if children:
            if len(children) == 1:
                child_code = self.generate_widget(
                    children[0], indent_level + 1)
                code += f"  child: {child_code},\n"
            else:
                code += f"  child: Column(\n"
                code += f"    mainAxisSize: MainAxisSize.min,\n"
                code += f"    crossAxisAlignment: CrossAxisAlignment.start,\n"
                code += f"    children: [\n"
                for child in children:
                    child_code = self.generate_widget(child, indent_level + 3)
                    code += f"      {child_code},\n"
                code += f"    ],\n"
                code += f"  ),\n"

        code += ")"
        return code

    def generate_center(self, data, indent_level=0):
        children = data.get('children', [])

        code = "Center(\n"

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

    def generate_stack(self, data, indent_level=0):
        children = data.get('children', [])

        code = "Stack(\n"
        code += f"  children: [\n"
        for child in children:
            child_code = self.generate_widget(child, indent_level + 2)
            code += f"    {child_code},\n"
        code += f"  ],\n"
        code += ")"
        return code

    def generate_positioned(self, data, indent_level=0):
        props = data.get('props', {})
        children = data.get('children', [])

        code = "Positioned(\n"

        if props.get('top') is not None:
            code += f"  top: {props['top']},\n"
        if props.get('left') is not None:
            code += f"  left: {props['left']},\n"
        if props.get('right') is not None:
            code += f"  right: {props['right']},\n"
        if props.get('bottom') is not None:
            code += f"  bottom: {props['bottom']},\n"

        if children:
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

        code += ")"
        return code

    def generate_expanded(self, data, indent_level=0):
        children = data.get('children', [])
        props = data.get('props', {})

        code = "Expanded(\n"

        if props.get('flex'):
            code += f"  flex: {props['flex']},\n"

        if children:
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

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
            child_code = self.generate_widget(children[0], indent_level + 1)
            code += f"  child: {child_code},\n"

        code += ")"
        return code

    def generate_unknown(self, data, indent_level=0):
        widget_type = data.get('type', 'Unknown')
        return f"// TODO: Implement {widget_type} widget\nContainer()"
