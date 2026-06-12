"""
Setup Script for Ollama Models
Downloads and configures LLM models for NutriBot
"""

import subprocess
import sys
import os


MODELS = {
    'llama3.2:3b': 'Llama-3.2-3B-Instruct (Lightweight, Fast)',
    'qwen2.5:7b': 'Qwen2.5-7B-Instruct (Smarter, More Capable)',
    'llama3.1:8b-q4_K_M': 'Llama-3.1-8B-Instruct Q4 (Balanced)'
}


def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"aœ“ Ollama is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("aŒ Ollama is not installed!")
        print("\nPlease install Ollama first:")
        print("  Windows: https://ollama.com/download/windows")
        print("  Mac: brew install ollama")
        print("  Linux: curl -fsSL https://ollama.com/install.sh | sh")
        return False


def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        print("aœ“ Ollama service is running")
        return True
    except subprocess.CalledProcessError:
        print("aš ï¸  Ollama service might not be running")
        print("Start it with: ollama serve")
        return False


def list_installed_models():
    """List currently installed models"""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\nCurrently installed models:")
        print(result.stdout)
        
        # Parse installed models
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        installed = []
        for line in lines:
            if line.strip():
                model_name = line.split()[0]
                installed.append(model_name)
        
        return installed
    except subprocess.CalledProcessError as e:
        print(f"Error listing models: {e}")
        return []


def pull_model(model_name: str):
    """Download a model"""
    print(f"\n{'='*60}")
    print(f"Downloading {model_name}...")
    print(f"Description: {MODELS.get(model_name, 'Unknown')}")
    print(f"{'='*60}")
    print("\nThis may take several minutes depending on your internet speed...")
    print("Model sizes: 3B (~2GB), 7B (~4.5GB), 8B-Q4 (~4.5GB)\n")
    
    try:
        # Run ollama pull with real-time output
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\naœ“ Successfully downloaded {model_name}")
            return True
        else:
            print(f"\naŒ Failed to download {model_name}")
            return False
            
    except Exception as e:
        print(f"\naŒ Error downloading model: {e}")
        return False


def test_model(model_name: str):
    """Test a model with a simple prompt"""
    print(f"\nTesting {model_name}...")
    
    try:
        result = subprocess.run(
            ['ollama', 'run', model_name, 'Sebutkan 3 makanan tinggi protein dalam bahasa Indonesia'],
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        print(f"\naœ“ Model response:")
        print(result.stdout)
        return True
        
    except subprocess.TimeoutExpired:
        print("aš ï¸  Model test timed out (this is normal for first run)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"aŒ Model test failed: {e}")
        return False


def main():
    """Main setup process"""
    print("="*60)
    print("NutriBot - Ollama Model Setup")
    print("="*60)
    
    # Check Ollama installation
    if not check_ollama_installed():
        sys.exit(1)
    
    # Check if Ollama is running
    check_ollama_running()
    
    # List installed models
    installed = list_installed_models()
    
    # Ask user which models to download
    print("\n" + "="*60)
    print("Available Models:")
    print("="*60)
    
    for i, (model_name, description) in enumerate(MODELS.items(), 1):
        status = "aœ“ INSTALLED" if model_name in installed else "a—‹ Not installed"
        print(f"{i}. {model_name}")
        print(f"   {description}")
        print(f"   Status: {status}\n")
    
    print("Which models would you like to download?")
    print("Enter numbers separated by commas (e.g., 1,2) or 'all' for all models")
    print("Press Enter to skip if models are already installed")
    
    choice = input("\nYour choice: ").strip().lower()
    
    if not choice:
        print("\nSkipping model download.")
    else:
        models_to_download = []
        
        if choice == 'all':
            models_to_download = list(MODELS.keys())
        else:
            try:
                indices = [int(x.strip()) for x in choice.split(',')]
                model_list = list(MODELS.keys())
                models_to_download = [model_list[i-1] for i in indices if 1 <= i <= len(model_list)]
            except (ValueError, IndexError):
                print("Invalid input. Exiting.")
                sys.exit(1)
        
        # Download selected models
        for model_name in models_to_download:
            if model_name in installed:
                print(f"\naœ“ {model_name} is already installed, skipping...")
            else:
                success = pull_model(model_name)
                if not success:
                    print(f"Failed to download {model_name}, continuing...")
    
    # Test a model
    print("\n" + "="*60)
    print("Model Testing")
    print("="*60)
    
    # Get updated list of installed models
    installed = list_installed_models()
    
    if installed:
        # Test first installed model
        test_model_name = installed[0]
        print(f"\nTesting {test_model_name}...")
        test_model(test_model_name)
    
    # Final summary
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nInstalled models:")
    for model in installed:
        print(f"  aœ“ {model}")
    
    print("\nNext steps:")
    print("1. Update .env file with your preferred model:")
    print("   DEFAULT_MODEL=llama3.2:3b")
    print("\n2. Run data ingestion:")
    print("   python scripts/data_ingestion.py")
    print("\n3. Start the backend:")
    print("   python app.py")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()



