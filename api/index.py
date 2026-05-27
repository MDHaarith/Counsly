import sys
import os

# Ensure the root project folder is on python path so 'backend' is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from mangum import Mangum

handler = Mangum(app, lifespan="off")