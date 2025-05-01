import sys
import subprocess
import os

def install_vanna():
    try:
        # First try the simplest approach
        print("Attempting to install base vanna package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "vanna", "--no-deps"])
        print("Successfully installed vanna without dependencies")
        
        # Now try to install minimal requirements
        print("Installing minimal dependencies...")
        minimal_deps = [
            "numpy",
            "pandas", 
            "scikit-learn", 
            "requests",
            "openai"
        ]
        
        for dep in minimal_deps:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"Successfully installed {dep}")
            except Exception as e:
                print(f"Error installing {dep}: {str(e)}")
        
        return True
    except Exception as e:
        print(f"Error installing vanna: {str(e)}")
        return False

if __name__ == "__main__":
    success = install_vanna()
    print(f"Installation {'successful' if success else 'failed'}")
    
    # Test if we can import vanna now
    try:
        import vanna
        print(f"Successfully imported vanna version {vanna.__version__}")
    except ImportError as e:
        print(f"Error importing vanna: {str(e)}")