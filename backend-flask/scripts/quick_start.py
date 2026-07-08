"""
Quick Start Script for NutriBot Local LLM Setup
Automates the setup process
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(text)
    print("="*60 + "\n")

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    print(f"a–¶ {description}...")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"aœ“ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"aŒ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"aœ“ {description} exists")
        return True
    else:
        print(f"aŒ {description} not found")
        return False

def main():
    """Main quick start process"""
    print_header("NutriBot - Quick Start Setup")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    print("This script will:")
    print("1. Install Python dependencies")
    print("2. Setup environment variables")
    print("3. Run data ingestion")
    print("4. Download Ollama models (optional)")
    print("5. Test the setup")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    # Step 1: Install dependencies
    print_header("Step 1: Installing Python Dependencies")
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing dependencies",
        cwd=project_root
    ):
        print("\naš ï¸  Dependency installation failed. Please install manually:")
        print(f"  cd {project_root}")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Step 2: Setup .env
    print_header("Step 2: Environment Configuration")
    env_file = project_root / '.env'
    env_example = project_root / '.env.example'
    
    if not env_file.exists():
        if env_example.exists():
            print("Creating .env from .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
            print("aœ“ .env file created")
            print("\naš ï¸  Please edit .env file to configure:")
            print("  - DEFAULT_MODEL (llama3.2:3b, qwen2.5:7b, etc.)")
            print("  - GEMINI_API_KEY (optional, for fallback)")
        else:
            print("aŒ .env.example not found")
    else:
        print("aœ“ .env file already exists")
    
    # Step 3: Data Ingestion
    print_header("Step 3: Food Database Setup")
    
    db_path = project_root / 'dataset' / 'nutribot_foods.db'
    
    if db_path.exists():
        print("aœ“ Database already exists")
        response = input("Do you want to re-create the database? (y/N): ")
        if response.lower() != 'y':
            print("Skipping data ingestion...")
        else:
            if not run_command(
                f"{sys.executable} scripts/data_ingestion.py",
                "Running data ingestion",
                cwd=project_root
            ):
                print("\naš ï¸  Data ingestion failed. Please run manually:")
                print(f"  cd {project_root}")
                print("  python scripts/data_ingestion.py")
    else:
        print("Database not found. Running data ingestion...")
        if not run_command(
            f"{sys.executable} scripts/data_ingestion.py",
            "Running data ingestion",
            cwd=project_root
        ):
            print("\naš ï¸  Data ingestion failed. Please run manually:")
            print(f"  cd {project_root}")
            print("  python scripts/data_ingestion.py")
            sys.exit(1)
    
    # Step 4: Ollama Setup
    print_header("Step 4: Ollama Model Setup")
    
    response = input("Do you want to download Ollama models now? (Y/n): ")
    if response.lower() != 'n':
        if not run_command(
            f"{sys.executable} scripts/setup_models.py",
            "Setting up Ollama models",
            cwd=project_root
        ):
            print("\naš ï¸  Model setup failed. You can run it manually later:")
            print(f"  cd {project_root}")
            print("  python scripts/setup_models.py")
    else:
        print("Skipping model download. You can run it later:")
        print(f"  cd {project_root}")
        print("  python scripts/setup_models.py")
    
    # Step 5: Test Setup
    print_header("Step 5: Testing Setup")
    
    print("Testing imports...")
    try:
        from services.food_database import search_foods
        from services.local_llm import LocalLLM
        from services.rag_service import RAGService
        print("aœ“ All services imported successfully")
    except ImportError as e:
        print(f"aŒ Import error: {e}")
        print("Please check your installation")
    
    # Final Summary
    print_header("Setup Complete!")
    
    print("aœ… NutriBot is ready to use!\n")
    print("Next steps:")
    print("1. Start the backend:")
    print(f"   cd {project_root}")
    print("   python app.py")
    print("\n2. Start the frontend (in another terminal):")
    print(f"   cd {project_root.parent / 'frontend'}")
    print("   npm run dev")
    print("\n3. Open browser:")
    print("   http://localhost:3000")
    
    print("\nðŸ“š Documentation:")
    print(f"   - Setup Guide: {project_root / 'OLLAMA_SETUP.md'}")
    print(f"   - Implementation Plan: See artifacts folder")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\naŒ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\naŒ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



