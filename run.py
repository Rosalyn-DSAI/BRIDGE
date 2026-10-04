"""Start the web server; run worker.py separately for scheduled reminders."""
import os
from bridge import create_app

app = create_app()

if __name__ == '__main__':
    from waitress import serve
    host = os.getenv('HOST', '127.0.0.1')
    if app.config['APP_ENV'] == 'local' and host not in ('127.0.0.1', 'localhost'):
        raise RuntimeError('Local inbox mode must stay on localhost. See docs/DEPLOYMENT.md.')
    serve(app, host=host, port=int(os.getenv('PORT', '5000')))
