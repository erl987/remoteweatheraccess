import os

from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': os.environ.get('CACHE_DIR', '/tmp/frontend-cache')
})
