import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print("\n" + "="*50)
    print("🚀 BoliScript - Hindi Video Transcript Generator")
    print(f"📱 Access on this PC:   http://localhost:{port}")
    print(f"📱 Access on Mobile:    http://<YOUR_LOCAL_IP>:{port}")
    print("="*50 + "\n")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
