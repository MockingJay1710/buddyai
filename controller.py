# controller.py
import json
import requests
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- Load .env configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(
        "Please set the GEMINI_API_KEY environment variable in your .env file."
    )

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:5000")
COMMANDS_SCHEMA_ENDPOINT = f"{AGENT_URL}/commands_schema"
COMMANDS_EXECUTION_ENDPOINT = f"{AGENT_URL}/execute"


# --- Pydantic model for Gemini JSON mode ---
class AgentCommandSchemaForGemini(BaseModel):
    command_name: str = Field(
        ..., description="The name of the command to execute from the available list."
    )
    params_as_string: str = Field(
        ..., description="A JSON string representing the parameters for the command."
    )


# --- Fetch command schema from agent ---
def fetch_commands_schema():
    print(f"Fetching command schema from: {COMMANDS_SCHEMA_ENDPOINT}")
    try:
        response = requests.get(COMMANDS_SCHEMA_ENDPOINT, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching schema: {e}")
        return {"commands": []}


# Mapping from Python type strings (from your schema) to JSON Schema type strings
PYTHON_TO_JSON_SCHEMA_TYPE_MAP_CORRECTED = {
    "str": "STRING",
    "string": "STRING",
    "int": "INTEGER",
    "integer": "INTEGER",
    "float": "NUMBER",  # JSON schema uses 'number' for floats and integers sometimes, but 'integer' is more specific
    "number": "NUMBER",
    "bool": "BOOLEAN",
    "boolean": "BOOLEAN",
    "list": "ARRAY",
    "array": "ARRAY",
    "dict": "OBJECT",
    "object": "OBJECT",
    # For NoneType or Optional fields not explicitly typed, you might not add them
    # or represent them carefully if the API supports 'NULL' type.
    # For now, we assume all parameters passed will have one of the above types.
}


# --- Convert commands to Gemini-compatible function declarations ---
# --- Convert commands to Gemini-compatible function declarations ---
def convert_agent_schema_to_function_declarations(agent_commands_list: list) -> list:
    function_declarations = []
    if not agent_commands_list:
        return []

    for agent_cmd_schema in agent_commands_list:
        command_name = agent_cmd_schema.get("name")
        description = agent_cmd_schema.get("description", "No description provided.")
        params_from_agent = agent_cmd_schema.get("params_schema_for_prompt", {})

        if not command_name:
            print(
                f"Warning: Skipping command with no name in schema: {agent_cmd_schema}"
            )
            continue

        properties = {}
        required_params = []

        for param_name, param_details in params_from_agent.items():
            # Get the Python type string (e.g., 'str', 'int') from your agent's schema
            py_type_str_from_agent = param_details.get(
                "type", "string"
            ).lower()  # Your agent schema provides this

            # Convert it to the Gemini API expected type string (e.g., 'STRING', 'INTEGER')
            # THIS IS THE KEY CHANGE: Use the corrected map
            gemini_api_type = PYTHON_TO_JSON_SCHEMA_TYPE_MAP_CORRECTED.get(
                py_type_str_from_agent, "STRING"
            )  # Fallback to STRING

            param_schema = {
                "type": gemini_api_type,  # USE THE CORRECTED TYPE
                "description": param_details.get(
                    "description", f"Parameter named {param_name}"
                ),
            }
            properties[param_name] = param_schema

            if not param_details.get("optional", False):
                required_params.append(param_name)

        func_decl_dict = {
            "name": command_name,
            "description": description,
            "parameters": {
                "type": "OBJECT",  # The type of 'parameters' itself is OBJECT
                "properties": properties,
            },
        }
        if required_params:
            func_decl_dict["parameters"]["required"] = required_params

        function_declarations.append(func_decl_dict)
    return function_declarations


conversation_history = [  # Optional: A system prompt can sometimes help guide the LLM's behavior
    """ types.Content(
                role="system",
                parts=[
                    types.Part(
                        text="You are a helpful assistant that executes tasks by calling available functions based on the user's request. Only use the functions provided. If no function is suitable, explain why you cannot perform the request."
                    )
                ],
            ), """,
]  # Global variable to hold conversation_history for Gemini API calls
MAX_HISTORY_TURNS = (
    5  # Example: Keep last 5 user/model/tool exchanges (adjust as needed)
)


def manage_history_length():
    """Simple strategy to limit history length."""
    global conversation_history
    # A "turn" could be a user message + model response (which might include tool call + tool response)
    # This is a very rough way; token counting is better.
    # Let's say we want to keep roughly MAX_HISTORY_TURNS * 2 or * 3 items if we include tool results
    # For simplicity, let's just cap the number of Content objects.
    max_items = MAX_HISTORY_TURNS * 3
    if len(conversation_history) > max_items:
        # Keep the system prompt (if you add one as the first element) and the most recent items
        # If no persistent system prompt:
        conversation_history = conversation_history[-max_items:]
        # If you have a system prompt as conversation_history[0]:
        # conversation_history = [conversation_history[0]] + conversation_history[-(max_items-1):]


# --- Translate user input to agent command JSON using Gemini ---
def translate_to_command_json(user_input: str, declarations: list) -> dict:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        tools = types.Tool(function_declarations=declarations)

        config = types.GenerateContentConfig(
            temperature=0.1,
            top_p=1,
            top_k=1,
            max_output_tokens=1024,
            tools=[tools],
        )
        global conversation_history
        conversation_history.append(
            types.Content(role="user", parts=[types.Part(text=user_input)]),
        )  # Append user input to conversation_history
        manage_history_length()  # Ensure we don't exceed the max history length

        print("\nAsking Gemini to translate your input into a command...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=config,
            contents=conversation_history,
        )

        # Correctly parse the function call from Gemini's response
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.function_call:
                        fc = part.function_call
                        command_name = fc.name

                        # Convert fc.args (google.protobuf.struct_pb2.Struct) to a Python dict
                        params = {}
                        if (
                            hasattr(fc, "args") and fc.args
                        ):  # Check if args exist and are not None
                            for key, value_struct in fc.args.items():
                                # This part needs robust conversion from Protobuf Value to Python type
                                if hasattr(value_struct, "string_value"):
                                    params[key] = value_struct.string_value
                                elif hasattr(value_struct, "number_value"):
                                    params[key] = value_struct.number_value
                                elif hasattr(value_struct, "bool_value"):
                                    params[key] = value_struct.bool_value
                                elif hasattr(value_struct, "null_value"):
                                    params[key] = None
                                # TODO: Add handling for list_value (becomes list) and struct_value (becomes dict)
                                # if your parameters can be lists or nested objects.
                                # Example for list_value (simplified):
                                # elif hasattr(value_struct, 'list_value'):
                                #     params[key] = [item.string_value for item in value_struct.list_value.values] # Assuming list of strings
                                else:
                                    # This is a fallback. Ideally, you'd handle all expected Protobuf types.
                                    # The `value_struct` itself might sometimes directly represent the Python value
                                    # depending on the SDK version and how it wraps things.
                                    # Printing it helps debug.
                                    print(
                                        f"Warning: Argument '{key}' has an unhandled or complex Protobuf type: {type(value_struct)}. Value: {value_struct}"
                                    )
                                    # Forcing to string might be a last resort for debugging but can cause issues.
                                    # params[key] = str(value_struct) # Or try to access common fields if it's a simple wrapper
                                    if isinstance(
                                        value_struct,
                                        (str, int, float, bool, list, dict),
                                    ):  # If SDK already converted it
                                        params[key] = value_struct
                                    else:
                                        params[key] = str(
                                            value_struct
                                        )  # Last resort string conversion

                        print(
                            f"Gemini suggested function call: '{command_name}' with params: {params}"
                        )

                        # Add the function call ITSELF to history (Gemini expects this)
                        # The 'model' role made the function call
                        conversation_history.append(response.candidates[0].content)

                        return {
                            "command_name": command_name,
                            "params": params,  # `params` is now a Python dictionary
                        }

        # If no function call was made, Gemini might just return text.
        llm_text_response = (
            response.text
            if hasattr(response, "text") and response.text
            else "Gemini did not make a function call and returned no usable text."
        )
        print(
            f"Gemini did not suggest a function call. Text response: '{llm_text_response}'"
        )
        conversation_history.append(
            types.Content(role="model", parts=[types.Part(text=llm_text_response)])
        )
        return {
            "error": "Gemini did not choose a function to call.",
            "text_response": llm_text_response,
        }

    except Exception as e:
        # Include more details if response object exists (e.g., prompt feedback)
        error_detail = ""
        if (
            "response" in locals()
            and response
            and hasattr(response, "prompt_feedback")
            and response.prompt_feedback.block_reason
        ):
            error_detail = f" | Blocked due to: {response.prompt_feedback.block_reason}"
        return {
            "error": f"Failed to process with Gemini (function calling): {str(e)}{error_detail}"
        }


# --- Send command to agent ---
def send_command_to_agent(command_json):
    print(f"\n--- Sending command to agent ---\n{json.dumps(command_json, indent=2)}\n")
    try:
        response = requests.post(
            COMMANDS_EXECUTION_ENDPOINT, json=command_json, timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request to agent timed out."}
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": f"Could not connect to agent at {AGENT_URL}. Is it running?",
        }
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request failed: {e}"}
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Invalid JSON from agent.",
            "raw_response": response.text,
        }


# --- CLI Loop ---
if __name__ == "__main__":
    print("🔧 Local Controller using Gemini JSON Mode (params_as_string)")
    print(f"Connecting to agent at {AGENT_URL}...\n")

    schema = fetch_commands_schema()
    if not schema.get("commands"):
        print("⚠️ No commands available from agent.")
        exit()

    declarations = convert_agent_schema_to_function_declarations(schema["commands"])

    print("✅ Ready. Type your natural language command.")
    print("💡 Example: 'Get weather forecast for Casablanca'")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("You > ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("👋 Exiting controller.")
            break
        if not user_input.strip():
            continue

        command_json = translate_to_command_json(user_input, declarations)
        if "error" in command_json:
            print(f"❌ Error: {command_json['error']}")
            continue

        response = send_command_to_agent(command_json)
        print(f"📨 Agent Response:\n{json.dumps(response, indent=2)}\n")
