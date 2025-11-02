# Complete setup script for backend

echo "🚀 Setting up Inventory Management System Backend..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Setup database
echo "💾 Setting up database..."
python ../scripts/setup_database.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API Documentation: http://localhost:8000/docs"
