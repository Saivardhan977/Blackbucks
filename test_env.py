import sys
import os

def check_environment():
    print("=== Python Environment Check ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Working Directory: {os.getcwd()}")
    
    # Check for required packages
    required = ['flask', 'flask_sqlalchemy']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
            missing.append(package)
    
    if missing:
        print("\nMissing packages. Please install them using:")
        print(f"pip install {' '.join(missing)}")
    else:
        print("\nAll required packages are installed!")

if __name__ == "__main__":
    check_environment()
