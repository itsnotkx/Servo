
import os
from llama_cpp import Llama
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env.local")

model_path = os.getenv("MODEL_PATH")
n_gpu_layers = int(os.getenv("N_GPU_LAYERS", 0))

print(f"Checking GPU support...")
print(f"Model Path: {model_path}")
print(f"Requested GPU Layers: {n_gpu_layers}")

if not model_path or not os.path.exists(model_path):
    print(f"Error: Model file not found at {model_path}")
    exit(1)

try:
    print("\nAttempting to load model with verbose=True...")
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        verbose=True,
        n_ctx=2048
    )
    print("\nModel loaded successfully.")
    # internal verification if possible, but the logs above (stderr) are key
except Exception as e:
    print(f"\nFailed to load model: {e}")
