#!/bin/bash
# Complete Setup Script for Real-time Agent Creation Testing
# Run this to install all dependencies and set up the environment

set -e  # Exit on any error

echo "🚀 Setting up Real-time Agent Creation Test Environment"
echo "============================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📋 Python version: $python_version"

# Install required packages
echo "📦 Installing required Python packages..."
pip install --upgrade pip

# Core dependencies
pip install flask flask-cors flask-socketio python-socketio[asyncio]

# LiveKit dependencies
pip install livekit-agents[openai,turn-detector,silero,cartesia,deepgram]
pip install livekit-plugins-noise-cancellation

# Optional dependencies (install if available)
echo "🔧 Installing optional dependencies..."
pip install faiss-cpu || echo "⚠️ faiss-cpu not available, will use fallback"
pip install ragie || echo "⚠️ ragie not available, will use mock"

echo "✅ Dependencies installed"

# Create necessary directories
echo "📁 Creating test directories..."
mkdir -p logs
mkdir -p templates

# Create minimal .env.local if it doesn't exist
if [ ! -f "../voxie-test/.env.local" ]; then
    echo "📝 Creating minimal .env.local..."
    cat > ../voxie-test/.env.local << 'EOF'
# Test environment configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=test-key-for-local-testing
DEEPGRAM_API_KEY=test-key
CARTESIA_API_KEY=test-key
EOF
fi

echo "🎯 Setup complete! You can now run the tests:"
echo "   python test_complete_integration.py"
echo "   python test_local_verification.py"