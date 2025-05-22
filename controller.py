# controller.py
import json
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any

# --- Pydantic Model Definition FOR GEMINI'S RESPONSE SCHEMA ---
# We'll ask Gemini to give us params as a JSON string
class AgentCommandSchemaForGemini(BaseModel):
    command_name: str = Field(..., description="The name of the command to execute from the available list.")
    params_as_string: str = Field(..., description="A JSON string representing the parameters for the command. Should be an empty JSON object string like '{}' if no parameters are needed.")

# --- Configuration ---
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable in your .env file.")

genai.configure(api_key=GEMINI_API_KEY)

generation_config_with_json = {
    "temperature": 0.1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 1024,
    "response_mime_type": "application/json",
    "response_schema": AgentCommandSchemaForGemini, # Use the modified schema
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

try:
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config_with_json,
        safety_settings=safety_settings
    )
    print("Successfully initialized Gemini model with JSON mode.")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    exit()

AGENT_URL = os.getenv('AGENT_URL', 'http://localhost:5000')
COMMANDS_SCHEMA_ENDPOINT = f"{AGENT_URL}/commands_schema"

# --- Global variable to store the fetched command schema ---
AGENT_COMMANDS_SCHEMA_STRING = "No commands loaded yet. Please ensure agent is running and schema can be fetched."

def fetch_and_format_agent_commands_schema():
    """
    Fetches the command schema from the agent and formats it for the LLM prompt.
    Updates the global AGENT_COMMANDS_SCHEMA_STRING.
    """
    global AGENT_COMMANDS_SCHEMA_STRING
    print(f"Attempting to fetch command schema from: {COMMANDS_SCHEMA_ENDPOINT}")
    try:
        response = requests.get(COMMANDS_SCHEMA_ENDPOINT, timeout=5)
        response.raise_for_status()
        schema_data = response.json()

        if schema_data.get("status") == "success" and "commands" in schema_data:
            commands = schema_data["commands"]
            if not commands:
                AGENT_COMMANDS_SCHEMA_STRING = "Agent reported success but returned no commands."
                print(AGENT_COMMANDS_SCHEMA_STRING)
                return

            description_string = "Available commands (for your reference to select `command_name` and populate `params_as_string`):\n"
            for cmd in commands:
                description_string += f"Command Name for `command_name` field: `{cmd['name']}`\n"
                description_string += f"  Description: {cmd.get('description', 'No description.')}\n"
                
                params_info = cmd.get('params_schema_for_prompt', {})
                if params_info:
                    description_string += "  Parameters (to be formatted as a JSON string for the `params_as_string` field):\n"
                    for p_name, p_detail in params_info.items():
                        p_type = p_detail.get('type', 'any')
                        opt_text = "(optional)" if p_detail.get('optional') else "(required)"
                        p_desc = p_detail.get('description', '')
                        default_val = f" (defaults to: {p_detail['default']})" if 'default' in p_detail else ""
                        description_string += f"    - `{p_name}`: type `{p_type}` {opt_text}{default_val}. {p_desc}\n"
                else:
                    description_string += "  Parameters for `params_as_string` field: None (use an empty JSON object string: '{}')\n"
                description_string += "\n"
            AGENT_COMMANDS_SCHEMA_STRING = description_string
            print("Successfully fetched and formatted agent command schema.")
            print(f"Formatted Schema:\n{AGENT_COMMANDS_SCHEMA_STRING}") # For debugging
        else:
            error_msg = schema_data.get("message", "Unknown error structure from agent schema endpoint.")
            AGENT_COMMANDS_SCHEMA_STRING = f"Failed to parse valid schema from agent: {error_msg}"
            print(AGENT_COMMANDS_SCHEMA_STRING)

    except requests.exceptions.RequestException as e:
        AGENT_COMMANDS_SCHEMA_STRING = f"Could not connect to agent to fetch command schema: {e}. Ensure agent is running."
        print(AGENT_COMMANDS_SCHEMA_STRING)
    except json.JSONDecodeError:
        AGENT_COMMANDS_SCHEMA_STRING = "Agent's schema endpoint did not return valid JSON."
        print(AGENT_COMMANDS_SCHEMA_STRING)


# --- Function to get available commands description (NOW USES THE GLOBAL VARIABLE) ---
def get_available_commands_description():
    """
    Returns the globally stored, dynamically fetched command schema string.
    """
    return AGENT_COMMANDS_SCHEMA_STRING # This is now populated by fetch_and_format_agent_commands_schema()



def translate_to_command_json(natural_language_input: str):
    commands_desc_str = get_available_commands_description()

    prompt_parts = [
        f"You are an AI assistant. Your task is to translate the user's natural language request into a structured JSON object that conforms to the `AgentCommandSchemaForGemini`. This schema requires a `command_name` (string) and a `params_as_string` (a JSON string).",
        "Consult the 'Available commands' list to determine the correct `command_name` and the structure for its parameters, then format those parameters as a JSON string for the `params_as_string` field.",
        "If a command takes no parameters, the `params_as_string` field should be the string `'{{}}'`.",
        "If the user's request cannot be mapped to any available command, or if required parameters are missing, you MUST output a specific JSON object: `{{\"error\": \"Could not understand or map the command.\"}}` (This error object does not conform to AgentCommandSchemaForGemini, it's a special error case).",
        "\n--- Available commands (for your reference) ---",
        commands_desc_str,
        "--- User Request ---",
        f"User's instruction: \"{natural_language_input}\"",
        "\n--- Instructions for JSON output ---",
        f"Based on the user's instruction, generate a JSON object strictly conforming to the `AgentCommandSchemaForGemini` (with `command_name` and `params_as_string`). If you cannot, generate the specified error JSON.",
    ]
    full_prompt = "\n".join(prompt_parts)

    print("\n--- Sending to Gemini (JSON Mode with params_as_string) ---")
    print("-----------------------------------------------------------\n")

    gemini_response_obj = None # Initialize to handle UnboundLocalError
    try:
        gemini_response_obj = model.generate_content(full_prompt)
        llm_output_text = gemini_response_obj.text.strip()
        print(f"Gemini Raw JSON Output: >>>{llm_output_text}<<<")

        # Attempt to parse the output. It might be the AgentCommandSchemaForGemini
        # or our defined error JSON.
        try:
            parsed_data = json.loads(llm_output_text)

            if "error" in parsed_data: # Check if LLM generated our custom error format
                print(f"LLM indicated a mapping error: {parsed_data['error']}")
                return parsed_data

            # Validate against AgentCommandSchemaForGemini Pydantic model
            validated_gemini_schema = AgentCommandSchemaForGemini(**parsed_data)

            # Now, parse the params_as_string into an actual dictionary
            try:
                actual_params = json.loads(validated_gemini_schema.params_as_string)
            except json.JSONDecodeError:
                print(f"Failed to parse params_as_string: '{validated_gemini_schema.params_as_string}'")
                return {"error": "LLM provided invalid JSON in params_as_string."}

            # Construct the final command object for the agent
            return {
                "command_name": validated_gemini_schema.command_name,
                "params": actual_params
            }

        except json.JSONDecodeError:
            print(f"LLM output was not valid JSON. Output: '{llm_output_text}'")
            return {"error": "LLM output was not valid JSON."}
        except ValidationError as ve:
            print(f"LLM JSON did not match AgentCommandSchemaForGemini. Output: '{llm_output_text}'. Errors: {ve}")
            return {"error": "LLM JSON did not match expected schema for command/params_as_string."}

    except Exception as e:
        error_message = f"Error communicating with Gemini: {type(e).__name__} - {e}"
        # Safely check prompt_feedback if gemini_response_obj was assigned
        if gemini_response_obj and hasattr(gemini_response_obj, 'prompt_feedback') and \
           gemini_response_obj.prompt_feedback and gemini_response_obj.prompt_feedback.block_reason:
            error_message += f" | Blocked due to: {gemini_response_obj.prompt_feedback.block_reason}"
        elif gemini_response_obj and hasattr(gemini_response_obj, 'candidates') and \
             gemini_response_obj.candidates and hasattr(gemini_response_obj.candidates[0], 'finish_reason') and \
             gemini_response_obj.candidates[0].finish_reason != 'STOP':
            error_message += f" | Finish Reason: {gemini_response_obj.candidates[0].finish_reason}"
        print(error_message)
        return {"error": error_message}


COMMANDS_EXECUTION_ENDPOINT = f"{AGENT_URL}/execute"

def send_command_to_agent(command_json):
    print(f"\n--- Sending to Agent ---")
    print(f"URL: {AGENT_URL}")
    print(f"Payload: {json.dumps(command_json, indent=2)}")
    print("------------------------\n")
    try:
        response = requests.post(COMMANDS_EXECUTION_ENDPOINT, json=command_json, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": f"Could not connect to agent at {AGENT_URL}. Is it running?"}
    # ... (rest of your send_command_to_agent function) ...
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request to agent timed out."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Error during request to agent: {e}"}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Agent did not return valid JSON.", "raw_response": response.text}


if __name__ == '__main__':
    print("Local Task Controller (with Gemini JSON Mode - params_as_string) started.")

    # Fetch the schema from the agent when the controller starts
    fetch_and_format_agent_commands_schema()

    print(f"Ensure agent_server.py is running and accessible at {AGENT_URL}")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        user_input = input("\nYou (type 'exit' to quit): ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting controller.")
            break
        if not user_input.strip():
            continue
        
        final_command_for_agent = translate_to_command_json(user_input)
        print(f"Processed LLM Output (for agent): {json.dumps(final_command_for_agent, indent=2)}")

        if final_command_for_agent.get("error"):
            print(f"Error: {final_command_for_agent['error']}")
            continue
        
        agent_response = send_command_to_agent(final_command_for_agent)
        print(f"Agent Response: {json.dumps(agent_response, indent=2)}")