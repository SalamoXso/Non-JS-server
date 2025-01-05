import os

# Define a list of large default folders to exclude completely
EXCLUDED_FOLDERS = ['node_modules', '.git', '.vscode', '__pycache__']

def print_tree(path, indent=""):
    """ Recursively prints the directory tree structure, excluding specific folders. """
    if not os.path.isdir(path):
        print("Please provide a valid directory path.")
        return
    
    # Print the folder name
    print(f"{indent}{os.path.basename(path)}/")
    
    # Walk through the directory contents
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        
        # Skip the excluded folders entirely (just print their names)
        if item in EXCLUDED_FOLDERS:
            print(f"{indent}    {item}/")
            continue
        
        # If it's a directory, recurse
        if os.path.isdir(item_path):
            print_tree(item_path, indent + "    ")
        else:
            # If it's a file, just print it
            print(f"{indent}    {item}")

def main():
    # Automatically get the current working directory
    current_directory = os.getcwd()
    print_tree(current_directory)

if __name__ == "__main__":
    main()
