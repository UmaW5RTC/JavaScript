# entry point of app

import os
import sys

PACKAGE_DIR = os.path.join(
    os.path.dirname(__file__),
    "site-packages"
)
sys.path.insert(0, PACKAGE_DIR)

rdir = None
if os.getenv("MODE", None) == "prod":
    sys.path.append("/var/www/sites/challenge-admin/production")
elif os.getenv("MODE", None) == "staging":
    sys.path.append("/var/www/sites/challenge-admin/dev")
elif os.getenv("MODE", None) == "experiment":
    sys.path.append("/var/www/sites/challenge-admin/experiment")
elif os.getenv("MODE", None) == "payment-dev":
    sys.path.append("/var/www/dqworld/experiment/admin")
else:
    rdir = os.path.dirname(os.path.join(os.getcwd(), __file__))
    rdir = os.path.dirname(rdir)
    sys.path.append(os.path.join(rdir, "challenge-admin"))
from main_api import app


if __name__ == "__main__":
    app.run()
