print("Python is working!")
print(f"Python version: {__import__('sys').version}")
print(f"Current directory: {__import__('os').getcwd()}")
try:
    import flask
    print("Flask is installed!")
except ImportError:
    print("Flask is not installed.")
