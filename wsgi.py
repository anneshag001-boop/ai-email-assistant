import sys
path = '/home/YOUR_USERNAME/ai-email-assistant'
if path not in sys.path:
    sys.path.insert(0, path)

from app.main import app
