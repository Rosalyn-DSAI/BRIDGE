"""Run from the project: python scripts/check_ai.py. Never prints your key."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bridge import create_app
from bridge.analysis import analyze, AnalysisError

def main():
    try:
        app=create_app()
        mode=app.config['AI_MODE']
        print('AI mode:',mode)
        if mode=='demo':
            print('Set AI_MODE=gemini and GEMINI_API_KEY in .env, then run again.')
            return 1
        print('Model:',app.config['GEMINI_MODEL' if mode=='gemini' else 'OPENAI_MODEL'])
        print('Testing with a short fictional message; no private document is sent.')
        with app.app_context():
            output=analyze('Please submit the project notes by Friday.','en','en')
        print('SUCCESS: connected, received structured output, and checked source references.')
        print('Action count:',len(output['actions']))
        return 0
    except (AnalysisError,RuntimeError) as exc:
        print('CHECK FAILED:',str(exc))
        return 1

if __name__=='__main__':
    raise SystemExit(main())
