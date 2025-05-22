# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
import inspect
from flask import Flask, jsonify, request
import sys, os, pkgutil, importlib
import modules as modules_package

#registry that will contain the commands to be run
COMMAND_REGISTRY = {}

current_script_dir = os.path.dirname(os.path.abspath(__file__))
modules_package_name = 'modules'
modules_dir_path = os.path.join(current_script_dir, modules_package_name)

def load_modules():
    """
    Discovers and loads commands from .py files in the 'modules_dir_path'.
    """
    print(f"Loading modules from directory: {modules_dir_path}")
    if not os.path.isdir(modules_dir_path):
        print(f"Error: Modules directory '{modules_dir_path}' not found.")
        return

    for filename in os.listdir(modules_dir_path):
        # Consider only .py files and ignore __init__.py and non-Python files
        if filename.endswith(".py") and filename != "__init__.py":
            module_file_name = filename[:-3]  # Remove ".py"
            # Construct the full module import name, e.g., "modules.basic_ops"
            # This assumes 'modules_package_name' is how the package is known to Python's import system
            module_import_name = f"{modules_package_name}.{module_file_name}"

            print(f"  Attempting to import module: {module_import_name}")
            try:
                module = importlib.import_module(module_import_name)

                if hasattr(module, 'COMMANDS') and isinstance(module.COMMANDS, dict):
                    for command_name, command_function in module.COMMANDS.items():
                        if command_name in COMMAND_REGISTRY:
                            print(f"    Warning: Command '{command_name}' from module '{module_import_name}' is overwriting an existing command.")
                        COMMAND_REGISTRY[command_name] = command_function
                        print(f"    Registered command: '{command_name}' -> {command_function.__name__}")
                else:
                    print(f"    Module '{module_import_name}' does not have a 'COMMANDS' dictionary or it's not a dict.")
            except ImportError as e:
                print(f"    Failed to import module '{module_import_name}'. Error: {e}")
                print(f"    Check if '{modules_package_name}' is a proper package and accessible in sys.path.")
            except Exception as e:
                print(f"    An unexpected error occurred while processing module '{module_import_name}'. Error: {e}")

    print(f"Finished loading modules. Available commands: {list(COMMAND_REGISTRY.keys())}")



# Flask constructor takes the name of 
# current module (__name__) as argument.
app = Flask(__name__)

# The route() function of the Flask class is a decorator, 
# which tells the application which URL should call 
# the associated function.
@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def hello_world():
    return 'Hello World'


@app.route('/commands_schema', methods=['GET'])
def get_commands_schema():
    """
    Returns a JSON schema describing all available commands, their parameters,
    and descriptions (from docstrings).
    """
    schema_list = []
    for command_name, command_function in COMMAND_REGISTRY.items():
        func_doc = inspect.getdoc(command_function) # Get the clean docstring
        description = func_doc.split('\n\n')[0] if func_doc else "No description available." # First paragraph of docstring
        
        sig = inspect.signature(command_function)
        params_schema = {}
        has_required_params = False

        for param_name, param_obj in sig.parameters.items():
            param_info = {
                "type": "string", # Default, can be refined if type hints are consistently used
                "optional": param_obj.default is not inspect.Parameter.empty,
                "description": "" # Could try to parse from docstring later if more advanced
            }
            if param_obj.annotation is not inspect.Parameter.empty:
                # Try to get a string representation of the type hint
                if hasattr(param_obj.annotation, '__name__'):
                    param_info["type"] = param_obj.annotation.__name__
                else: # For complex types like typing.List[str]
                    param_info["type"] = str(param_obj.annotation)

            if param_obj.default is not inspect.Parameter.empty:
                param_info["default"] = param_obj.default
            else:
                has_required_params = True
            
            params_schema[param_name] = param_info
            
        schema_list.append({
            "name": command_name,
            "description": description,
            "params_schema_for_prompt": params_schema, # Matches key used in controller's prompt
            # "has_required_params": has_required_params # Optional: useful info for LLM
        })
        
    return jsonify({"status": "success", "commands": schema_list})



"""
{
  "command_name": "some_command_identifier",
  "params": {
    "param1_name": "value1",
    "param2_name": "value2"
  }
}
"""

@app.route('/execute', methods=['POST'])
def execute():
    if request.is_json:
        
        try:
            data = request.get_json()
            if 'command_name' not in data:
                return jsonify({"error": "Missing 'command_name' in JSON payload"}), 400
            # Process the JSON data here
            command_name = data['command_name']
            params = data.get('params', {})

            if command_name in COMMAND_REGISTRY:
                try:
                    result = COMMAND_REGISTRY[command_name](**params)
                    return jsonify(result), 200
                except TypeError as e: # Catch errors if params don't match function signature
                    return jsonify({"status": "error", "message": f"Parameter mismatch for command '{command_name}': {str(e)}"}), 400
                except Exception as e: # Catch any other errors during command execution
                    return jsonify({"status": "error", "message": f"Error executing command '{command_name}': {str(e)}"}), 500
            else:
                return jsonify({"error": "unfound function"}), 404
            
        except Exception as e:
            return jsonify({"error": "Invalid JSON format", "details": str(e) }), 400
        
    else:
        return jsonify({"error": "Request must be JSON"}), 400





# main driver function
if __name__ == '__main__':

    load_modules()
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(debug=True)