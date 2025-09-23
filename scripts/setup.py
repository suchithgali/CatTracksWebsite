#!/usr/bin/env python3
"""
Setup script for CatTracks Python environment
This script installs required Python dependencies and validates the environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8+")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")

def install_requirements():
    """Install Python requirements."""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    cmd = f"{sys.executable} -m pip install -r requirements.txt"
    return run_command(cmd, "Installing Python requirements") is not None

def validate_gis_packages():
    """Validate that GIS packages are working correctly."""
    try:
        import geopandas
        import fiona
        print("✅ GIS packages (geopandas, fiona) are working")
        return True
    except ImportError as e:
        print(f"❌ GIS package import failed: {e}")
        print("   You may need to install GDAL system dependencies")
        return False

def check_data_directory():
    """Check if required data directories exist."""
    data_dir = Path("data")
    geopkg_dir = Path("geopkg")
    
    if not data_dir.exists():
        print("📁 Creating data directory...")
        data_dir.mkdir(exist_ok=True)
    
    if not geopkg_dir.exists():
        print("⚠️  geopkg directory not found. Please add GeoPackage files manually.")
        geopkg_dir.mkdir(exist_ok=True)
    
    print("✅ Data directories are ready")

def main():
    """Main setup function."""
    print("🚀 Setting up CatTracks Python environment...")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        sys.exit(1)
    
    # Validate GIS packages
    validate_gis_packages()
    
    # Check data directories
    check_data_directory()
    
    print("\n🎉 Python environment setup completed!")
    print("\nNext steps:")
    print("1. Add your Google Maps API key to src/python/find_nearest.py")
    print("2. Place GeoPackage files in the geopkg/ directory")
    print("3. Run: python src/python/address_lookup.py")
    print("4. Start using CatTracks!")

if __name__ == "__main__":
    main()