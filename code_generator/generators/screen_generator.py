from .widget_generator import WidgetGenerator


class ScreenGenerator:

    def __init__(self):
        self.widget_generator = WidgetGenerator()

    def generate_screen(self, screen_data):
        screen_name = screen_data.get('name', 'Home')
        screen_id = screen_data.get('id', 'home')
        components = screen_data.get('components', [])

        # Clean screen name for class name
        class_name = self.to_class_name(screen_name)

        code = self.generate_imports()
        code += self.generate_class_definition(class_name)
        code += self.generate_state_class(class_name, components)

        return code

    def generate_imports(self):
        return """import 'package:flutter/material.dart';

"""

    def generate_class_definition(self, class_name):
        return f"""class {class_name}Screen extends StatefulWidget {{
  const {class_name}Screen({{super.key}});

  @override
  State<{class_name}Screen> createState() => _{class_name}ScreenState();
}}

"""

    def generate_state_class(self, class_name, components):
        code = f"""class _{class_name}ScreenState extends State<{class_name}Screen> {{
"""

        # Add state variables if needed
        code += self.generate_state_variables()

        # Add action methods
        code += self.generate_action_methods()

        # Build method
        code += """  @override
  Widget build(BuildContext context) {
    return """

        # Generate widget tree
        if components:
            # Check if there's a Scaffold
            has_scaffold = any(c.get('type') == 'Scaffold' for c in components)

            if has_scaffold:
                scaffold = next(
                    c for c in components if c.get('type') == 'Scaffold')
                code += self.widget_generator.generate_widget(scaffold)
            else:
                # Wrap in Scaffold if not present
                code += "Scaffold(\n"

                # Check for AppBar
                appbar = next(
                    (c for c in components if c.get('type') == 'AppBar'), None)
                if appbar:
                    code += "      appBar: " + \
                        self.widget_generator.generate_widget(appbar) + ",\n"
                    components = [
                        c for c in components if c.get('type') != 'AppBar']

                code += "      body: "

                if len(components) == 1:
                    code += self.widget_generator.generate_widget(
                        components[0])
                else:
                    code += "Column(\n"
                    code += "        children: [\n"
                    for comp in components:
                        code += "          " + \
                            self.widget_generator.generate_widget(comp) + ",\n"
                    code += "        ],\n"
                    code += "      )"

                code += ",\n    )"
        else:
            # Default empty scaffold
            code += """Scaffold(
      appBar: AppBar(title: const Text('Screen')),
      body: const Center(child: Text('Empty Screen')),
    )"""

        code += ";\n  }\n}\n"

        return code

    def generate_state_variables(self):
        return """  // State variables
  
"""

    def generate_action_methods(self):
        return """  // Action handlers
  void handlePress() {
    // TODO: Implement action
  }
  
  void handleClick() {
    // TODO: Implement action
  }
  
  void onAction() {
    // TODO: Implement action
  }
  
"""

    # Convert string to PascalCase class name
    def to_class_name(self, name):
        # Remove special characters and split on spaces/underscores
        words = name.replace('-', ' ').replace('_', ' ').split()
        # Capitalize first letter of each word
        return ''.join(word.capitalize() for word in words if word)

    # Generate route name from screen name
    def generate_route_name(self, screen_name):
        return '/' + screen_name.lower().replace(' ', '-')
