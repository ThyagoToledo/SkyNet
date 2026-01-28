"""
GPU Configuration Diagnostic for Skynet
Detects and configures GPU acceleration for AMD/NVIDIA
"""

import os
import sys

def check_gpu_availability():
    """Check available GPU acceleration"""
    print("\n" + "="*60)
    print("🖥️  GPU ACCELERATION DIAGNOSTIC")
    print("="*60 + "\n")
    
    # Check PyTorch with CUDA
    print("[1] Checking PyTorch GPU support...")
    try:
        import torch
        print(f"   ✓ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"   ✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"   ✓ Using NVIDIA GPU")
            return "cuda"
        else:
            print("   ⚠ CUDA not available (NVIDIA GPU not detected)")
    except ImportError:
        print("   ✗ PyTorch not installed")
    
    # Check DirectML (AMD/Intel)
    print("\n[2] Checking DirectML (AMD/Intel)...")
    try:
        import torch_directml
        print("   ✓ DirectML available!")
        print("   ✓ Using AMD/Intel GPU acceleration")
        return "directml"
    except ImportError:
        print("   ⚠ DirectML not installed")
    
    # Check ONNX Runtime DirectML
    print("\n[3] Checking ONNX Runtime DirectML...")
    try:
        import onnxruntime as ort
        available_providers = ort.get_available_providers()
        print(f"   Available providers: {available_providers}")
        
        if "DmlExecutionProvider" in available_providers:
            print("   ✓ DirectML ExecutionProvider available!")
            return "onnx-directml"
        elif "CUDAExecutionProvider" in available_providers:
            print("   ✓ CUDA ExecutionProvider available!")
            return "onnx-cuda"
        else:
            print("   ℹ Only CPU provider available")
            return "cpu"
    except ImportError:
        print("   ⚠ ONNX Runtime not installed")
    
    print("\n" + "="*60)
    print("❌ NO GPU ACCELERATION DETECTED")
    print("   Using CPU (slower but works)")
    print("="*60 + "\n")
    return "cpu"


def get_installation_instructions(gpu_type):
    """Get installation instructions based on GPU"""
    
    instructions = {
        "cuda": """
╔════════════════════════════════════════════════════════════════╗
║          NVIDIA GPU (CUDA) DETECTED ✓                          ║
╚════════════════════════════════════════════════════════════════╝

Your GPU is already optimized!
- PyTorch with CUDA is installed
- Whisper will use GPU acceleration
- Performance: ⭐⭐⭐⭐⭐

No additional steps needed!
""",
        
        "directml": """
╔════════════════════════════════════════════════════════════════╗
║          AMD/INTEL GPU (DirectML) DETECTED ✓                   ║
╚════════════════════════════════════════════════════════════════╝

Your GPU is optimized!
- PyTorch DirectML is installed
- Whisper will use GPU acceleration
- Performance: ⭐⭐⭐⭐⭐

No additional steps needed!
""",
        
        "onnx-directml": """
╔════════════════════════════════════════════════════════════════╗
║          AMD/INTEL GPU (ONNX DirectML) DETECTED ✓              ║
╚════════════════════════════════════════════════════════════════╝

Your GPU is partially optimized!
- ONNX Runtime DirectML available
- Whisper will use optimized ONNX inference
- Performance: ⭐⭐⭐⭐

Optional: Install PyTorch DirectML for better performance:
  pip install torch-directml

Then restart Skynet.
""",
        
        "onnx-cuda": """
╔════════════════════════════════════════════════════════════════╗
║          NVIDIA GPU (ONNX CUDA) DETECTED ✓                     ║
╚════════════════════════════════════════════════════════════════╝

Your GPU is optimized!
- ONNX Runtime with CUDA available
- Whisper will use GPU acceleration
- Performance: ⭐⭐⭐⭐⭐

No additional steps needed!
""",
        
        "cpu": """
╔════════════════════════════════════════════════════════════════╗
║          NO GPU DETECTED - USING CPU                           ║
╚════════════════════════════════════════════════════════════════╝

Your system will use CPU for inference.
- Performance: ⭐⭐⭐ (slower but functional)

To optimize for AMD GPU, install:

  1. PyTorch DirectML:
     pip uninstall torch -y
     pip install torch-directml

  2. For Intel GPU:
     pip uninstall torch -y
     pip install intel-extension-for-pytorch

  3. Then restart Skynet

Note: Restart PowerShell after installation!
"""
    }
    
    return instructions.get(gpu_type, instructions["cpu"])


def main():
    """Main diagnostic function"""
    gpu_type = check_gpu_availability()
    instructions = get_installation_instructions(gpu_type)
    print(instructions)
    
    print("\n[Summary]")
    print(f"GPU Type: {gpu_type.upper()}")
    print(f"Whisper Model: {os.getenv('WHISPER_MODEL', 'small')}")
    print(f"Language: {os.getenv('LANGUAGE', 'pt')}")
    
    return gpu_type


if __name__ == "__main__":
    main()
