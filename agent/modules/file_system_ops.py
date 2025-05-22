# agent/modules/file_system_ops.py
import os
import shutil
import glob

def create_file(path: str, content: str = ""):
    """
    Creates a new file at the specified path with optional initial content.
    
    If the file already exists, it will be overwritten.
    Ensure the directory structure for the path exists, or handle errors appropriately.
    
    Args:
        path (str): The full path, including filename, where the file should be created.
        content (str, optional): The initial text content for the file. Defaults to an empty string.
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"status": "success", "message": f"File '{path}' created successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create file '{path}': {e}"}

def read_file(path: str):
    """
    Reads the entire content of a specified text file.

    Returns the content as a string if successful.
    Handles cases where the file does not exist or is not a file.

    Args:
        path (str): The full path to the file to be read.
    """
    try:
        if not os.path.exists(path):
            return {"status": "error", "message": f"File '{path}' not found."}
        if not os.path.isfile(path):
            return {"status": "error", "message": f"Path '{path}' is not a file."}
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": f"Failed to read file '{path}': {e}"}

def delete_file_or_directory(path: str):
    """
    Deletes a specified file or an entire directory (including its contents).

    Use with caution, especially for directories, as this action is irreversible.

    Args:
        path (str): The full path to the file or directory to be deleted.
    """
    try:
        if not os.path.exists(path):
            return {"status": "error", "message": f"Path '{path}' not found for deletion."}
        
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
            return {"status": "success", "message": f"File '{path}' deleted successfully."}
        elif os.path.isdir(path):
            shutil.rmtree(path)
            return {"status": "success", "message": f"Directory '{path}' and its contents deleted successfully."}
        else:
            return {"status": "error", "message": f"Path '{path}' is not a file or directory."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete '{path}': {e}"}

def move_or_rename(source_path: str, destination_path: str):
    """
    Moves or renames a file or directory from a source path to a destination path.

    If the destination is an existing directory, the source will be moved into it.
    If the destination specifies a new name, the source will be renamed.

    Args:
        source_path (str): The current path of the file or directory.
        destination_path (str): The new path or name for the file or directory.
    """
    try:
        if not os.path.exists(source_path):
            return {"status": "error", "message": f"Source path '{source_path}' not found."}
        shutil.move(source_path, destination_path)
        return {"status": "success", "message": f"Moved '{source_path}' to '{destination_path}' successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to move '{source_path}' to '{destination_path}': {e}"}

def search_files(directory: str, file_pattern: str, content_pattern: str = "", recursive: bool = True):
    """
    Searches for files matching a name pattern within a directory.
    
    Optionally searches for a specific content pattern (string) within those files.
    The search can be recursive to include subdirectories.

    Args:
        directory (str): The directory path to start the search from.
        file_pattern (str): A glob-style pattern for file names (e.g., "*.txt", "report_*.docx").
        content_pattern (str, optional): A string to search for within the content of matching files. 
                                         If empty, only filenames are matched. Defaults to "".
        recursive (bool, optional): If True, the search will include subdirectories. Defaults to True.
    """
    found_files = []
    try:
        if not os.path.isdir(directory):
            return {"status": "error", "message": f"Directory '{directory}' not found."}

        # ... (rest of the search logic remains the same)
        if recursive:
            for root, _, files in os.walk(directory):
                for filename in files:
                    if glob.fnmatch.fnmatch(filename, file_pattern):
                        full_path = os.path.join(root, filename)
                        if content_pattern:
                            try:
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    if content_pattern in f.read():
                                        found_files.append(full_path)
                            except Exception:
                                pass 
                        else:
                            found_files.append(full_path)
        else:
            for filename in os.listdir(directory):
                full_path = os.path.join(directory, filename)
                if os.path.isfile(full_path) and glob.fnmatch.fnmatch(filename, file_pattern):
                    if content_pattern:
                        try:
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                if content_pattern in f.read():
                                    found_files.append(full_path)
                        except Exception:
                            pass
                    else:
                        found_files.append(full_path)
        
        return {"status": "success", "found_files": found_files, "count": len(found_files)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to search files in '{directory}': {e}"}

COMMANDS = {
    "fs_create_file": create_file,
    "fs_read_file": read_file,
    "fs_delete": delete_file_or_directory,
    "fs_move": move_or_rename,
    "fs_search_files": search_files,
}