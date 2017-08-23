# entry point of app

import os
import sys

PACKAGE_DIR = os.path.join(
    os.path.dirname(__file__),
    "site-packages"
)
sys.path.insert(0, PACKAGE_DIR)

from main import app


if __name__ == "__main__":
    app.run()

