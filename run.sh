# Setup and run the FastAPI backend

# Install dependencies
pip install -r requirements.txt

# Run database setup
python scripts/setup_database.py

# Start the server
uvicorn main:app --reload --port 8000
