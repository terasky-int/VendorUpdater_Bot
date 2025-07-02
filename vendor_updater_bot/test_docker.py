#!/usr/bin/env python3
"""Test Docker build for vendor_updater_bot"""

import subprocess
import sys
import os

def test_docker_build():
    """Test if Docker image builds successfully"""
    try:
        print("🐳 Testing vendor_updater_bot Docker build...")
        
        # Stay in parent directory for build context
        # os.chdir("docker")  # Don't change directory
        
        # Build Docker image with correct context
        result = subprocess.run([
            "docker", "build", "-f", "docker/Dockerfile", "-t", "vendor-updater-bot:test", "."
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker build test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_docker_build()
    sys.exit(0 if success else 1)