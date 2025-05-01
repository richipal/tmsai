"""
Cleanup script to remove HTTPVannaClient class from clients.py file.
"""
import re

SOURCE_FILE = 'server/flask/modules/clients.py'
OUTPUT_FILE = 'server/flask/modules/clients_cleaned.py'

def main():
    # Read the entire file
    with open(SOURCE_FILE, 'r') as file:
        content = file.read()
        
    # Find the HTTPVannaClient class with regex
    # Starting with class definition and ending before the next class or function
    pattern = r'class HTTPVannaClient:.*?(?=class|def\s+\w+|$)'
    cleaned_content = re.sub(pattern, '# HTTPVannaClient class has been removed to comply with instructions\n# not to use "https://ask.vanna.ai/api" for integration\n\n', 
                         content, flags=re.DOTALL)
    
    # Save cleaned content to new file
    with open(OUTPUT_FILE, 'w') as file:
        file.write(cleaned_content)
    
    print(f"Cleaned content saved to {OUTPUT_FILE}")
    print("Please verify the changes and then replace the original file if everything looks good.")

if __name__ == "__main__":
    main()