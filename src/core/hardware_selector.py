"""
Hardware Selector
Menu for selecting CPU/NVIDIA/AMD hardware acceleration
"""

import os
import sys
import json
from pathlib import Path


class HardwareSelector:
    """Hardware acceleration selector for AI processing"""
    
    CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "hardware_config.json"
    
    def __init__(self):
        self.selected_hardware = "cpu"
        self.available_hardware = self._detect_hardware()
        
    def _detect_hardware(self) -> dict:
        """Detect available hardware"""
        hardware = {
            "cpu": True,
            "nvidia": False,
            "amd": False
        }
        
        # Check for NVIDIA GPU
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                hardware["nvidia"] = True
                hardware["nvidia_name"] = result.stdout.strip().split('\n')[0]
        except Exception:
            pass
            
        # Check for AMD GPU (via DirectML on Windows)
        try:
            # Check if AMD GPU exists via WMIC
            import subprocess
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if "amd" in output or "radeon" in output:
                    hardware["amd"] = True
                    # Extract AMD GPU name
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if "amd" in line.lower() or "radeon" in line.lower():
                            hardware["amd_name"] = line.strip()
                            break
        except Exception:
            pass
            
        return hardware
        
    def show_menu(self) -> str:
        """Display hardware selection menu and return choice"""
        
        # Check for saved config
        saved = self._load_config()
        if saved and not os.environ.get("SKYNET_FORCE_HARDWARE_MENU"):
            print(f"[Hardware] Usando configuração salva: {saved}")
            self.selected_hardware = saved
            return saved
        
        self._print_banner()
        
        while True:
            print("\n╔══════════════════════════════════════════════════════════════╗")
            print("║           SKYNET - Seleção de Hardware para IA               ║")
            print("╠══════════════════════════════════════════════════════════════╣")
            
            # CPU option (always available)
            print("║  [1] CPU (funciona em qualquer PC)                           ║")
            
            # NVIDIA option
            if self.available_hardware.get("nvidia"):
                gpu_name = self.available_hardware.get("nvidia_name", "NVIDIA GPU")
                print(f"║  [2] NVIDIA GPU - {gpu_name[:40]:<40} ║")
            else:
                print("║  [2] NVIDIA GPU (não detectada)                              ║")
                
            # AMD option
            if self.available_hardware.get("amd"):
                gpu_name = self.available_hardware.get("amd_name", "AMD GPU")
                print(f"║  [3] AMD GPU - {gpu_name[:43]:<43} ║")
            else:
                print("║  [3] AMD GPU (não detectada)                                 ║")
                
            print("╠══════════════════════════════════════════════════════════════╣")
            print("║  [S] Salvar escolha e não perguntar novamente                ║")
            print("╚══════════════════════════════════════════════════════════════╝")
            
            choice = input("\nEscolha uma opção [1/2/3]: ").strip().lower()
            
            save_choice = False
            if 's' in choice:
                save_choice = True
                choice = choice.replace('s', '').strip()
            
            if choice == "1":
                self.selected_hardware = "cpu"
                break
            elif choice == "2":
                if self.available_hardware.get("nvidia"):
                    self.selected_hardware = "nvidia"
                    break
                else:
                    print("\n⚠️  GPU NVIDIA não detectada. Instale os drivers NVIDIA primeiro.")
            elif choice == "3":
                if self.available_hardware.get("amd"):
                    self.selected_hardware = "amd"
                    break
                else:
                    print("\n⚠️  GPU AMD não detectada. Verifique os drivers AMD.")
            else:
                print("\n❌ Opção inválida. Digite 1, 2 ou 3.")
        
        # Save if requested
        if save_choice or input("\nSalvar esta escolha para próximas vezes? [s/N]: ").lower() == 's':
            self._save_config(self.selected_hardware)
            print(f"✅ Configuração salva: {self.selected_hardware}")
        
        print(f"\n✅ Hardware selecionado: {self.selected_hardware.upper()}")
        return self.selected_hardware
        
    def _print_banner(self):
        """Print welcome banner"""
        print("\n" + "=" * 64)
        print("              SKYNET - Personal AI Assistant")
        print("=" * 64)
        
    def _load_config(self) -> str:
        """Load saved hardware configuration"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get("hardware")
        except Exception:
            pass
        return None
        
    def _save_config(self, hardware: str):
        """Save hardware configuration"""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({"hardware": hardware}, f)
        except Exception as e:
            print(f"⚠️  Erro ao salvar configuração: {e}")
            
    def get_ollama_env_vars(self) -> dict:
        """Get environment variables for Ollama based on hardware selection"""
        env_vars = {}
        
        if self.selected_hardware == "nvidia":
            # NVIDIA CUDA - Ollama uses CUDA by default when available
            env_vars["CUDA_VISIBLE_DEVICES"] = "0"
            
        elif self.selected_hardware == "amd":
            # AMD ROCm/DirectML
            # On Windows, Ollama uses DirectML for AMD GPUs
            env_vars["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"  # Common compatibility setting
            
        else:  # CPU
            # Force CPU-only mode
            env_vars["CUDA_VISIBLE_DEVICES"] = ""
            
        return env_vars
        
    def configure_environment(self):
        """Apply hardware-specific environment variables"""
        env_vars = self.get_ollama_env_vars()
        for key, value in env_vars.items():
            os.environ[key] = value
        print(f"[Hardware] Ambiente configurado para: {self.selected_hardware.upper()}")


def select_hardware() -> str:
    """Convenience function to select hardware"""
    selector = HardwareSelector()
    return selector.show_menu()


if __name__ == "__main__":
    # Test hardware detection
    selector = HardwareSelector()
    print("Hardware detectado:", selector.available_hardware)
    choice = selector.show_menu()
    print(f"Selecionado: {choice}")
