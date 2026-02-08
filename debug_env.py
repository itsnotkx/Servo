import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

try:
    import yaml
    print(f"YAML version: {yaml.__version__}")
    print(f"YAML file: {yaml.__file__}")
except ImportError as e:
    print(f"Error importing yaml: {e}")

try:
    import inference.core.config_loader
    print("Successfully imported config_loader")
except ImportError as e:
    print(f"Error importing config_loader: {e}")
except Exception as e:
    print(f"Error running config_loader: {e}")
