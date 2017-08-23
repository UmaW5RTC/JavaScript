from jinja2.environment import create_cache
from jinja2 import FileSystemBytecodeCache, MemcachedBytecodeCache
import os

def configure(app):

    def get_service():
        if os.getenv('MODE', None) == "prod":
            import memcache
            return MemcachedBytecodeCache(memcache.Client(['127.0.0.1:11211']),
                                          prefix='adm-j2/%s/' % app.config['VERSION'])
        else:
            return FileSystemBytecodeCache(pattern="__adm_%s_%s.cache" % (app.config['VERSION'], '%s'))

    app.jinja_env.cache = create_cache(500)
    app.jinja_env.cache_size = 500
    app.jinja_env.bytecode_cache = get_service()

    @app.url_defaults
    def versioned_url(endpoint, values):
        """
        applicable to app-level resources
        """
        if app.config['VERSION']:
            if 'static' == endpoint or '.static' == endpoint[-7:]:
                filename = values.get('filename', None)
                if filename and '_v' not in values:
                    values['filename'] = "%s/%s" % (app.config['VERSION'], filename)
                    return

            if '_v' in values and values['_v'] is True:
                values['_v'] = app.config['VERSION']