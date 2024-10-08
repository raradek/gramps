
import os
import sys
import importlib
import inspect
import threading



def trace_instance_creation(original_init):
    def new_init(self, *args, **kwargs):
        print(f"Creating instance of: {self.__class__.__name__}")
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
    return new_init

def apply_trace_to_class(cls):
    # Replace the original __init__ with the traced version
    original_init = cls.__init__ if hasattr(cls, '__init__') else lambda self: None
    cls.__init__ = trace_instance_creation(original_init)

def trace_classes_in_directory(directory):
    # Traverse the directory and subdirectories
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):  # Only process Python files
                module_name = file[:-3]  # Remove '.py' extension
                module_path = os.path.join(root, file)
                try:
                    # Import the module dynamically
                    module = import_module_from_file(module_path, module_name)

                    # Get all classes in the module
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Apply trace only to classes defined in the current module
                        if obj.__module__ == module.__name__:
                            apply_trace_to_class(obj)
                except Exception as e:
                    print(f"Failed to process {file}: {e}")

def import_module_from_file(filepath, module_name):
    """Dynamically load a module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Example usage: Trace all classes in the current directory and subdirectories
trace_classes_in_directory('gramps/gui')


import gramps.grampsapp as app

app.main()   
