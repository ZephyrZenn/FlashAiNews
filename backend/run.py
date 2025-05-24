import uvicorn
import os

# Set environment variable for development
os.environ.setdefault("ENV", "dev")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
