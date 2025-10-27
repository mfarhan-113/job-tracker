from .base import *  # noqa

# Import the appropriate settings based on the environment
if os.environ.get('ENVIRONMENT') == 'production':
    from .production import *  # noqa
else:
    from .development import *  # noqa
