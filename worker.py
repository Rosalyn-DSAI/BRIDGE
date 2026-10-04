"""One persistent worker: python worker.py. One pass: python worker.py --once."""
import argparse
import logging
import time
from bridge import create_app
from bridge.reminders import deliver_due

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    app = create_app()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    with app.app_context():
        while True:
            try:
                result = deliver_due()
                if result['processed']:
                    logging.info('Reminder pass: %s', result)
            except Exception:
                logging.exception('Worker pass failed; retrying on next tick')
            if args.once:
                break
            time.sleep(app.config['WORKER_INTERVAL'])

if __name__ == '__main__':
    main()
