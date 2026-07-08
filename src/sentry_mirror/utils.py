import requests
from sentry_mirror.logger import logger
from sentry_mirror.__about__ import __version__

def check_for_updates():
    """
    Checks GitHub Releases for a newer version.
    """
    # Replace 'your-username' and 'your-repo-name'
    repo_url = "https://api.github.com/repos/BDib/sentrymirror/releases/latest"
    
    try:
        response = requests.get(repo_url, timeout=5)
        if response.status_code == 200:
            latest_version = response.json()["tag_name"].lstrip("v")
            
            if latest_version > __version__:
                logger.info(f"🚀 New version available: {latest_version} (Current: {__version__})")
                logger.info("Run 'pip install --upgrade sentry-mirror' to update.")
            else:
                logger.debug("SentryMirror is up to date.")
        else:
            logger.debug(f"Could not check for updates (Status: {response.status_code})")
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
