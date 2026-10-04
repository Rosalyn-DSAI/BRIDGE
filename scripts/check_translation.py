"""Run fictional translation checks with the local .env; never send email or use the task database."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
from flask import Flask
import bridge.analysis as analysis

SAMPLES = {
    'en': '''Task Title: Prepare the BRIDGE User Guide
Create a user guide explaining account creation, login, translation and task management.
Date: October 6, 2026 (Tuesday)
Time: 9:00 AM – 11:00 AM
Location: University Library
Include screenshots and step-by-step instructions. Submit the completed document before the deadline and update your task status.''',
    'es': '''Se te ha asignado una nueva tarea: Evaluar la compatibilidad móvil del proyecto BRIDGE.
Fecha: Jueves, 8 de octubre de 2026
Horario: De 3:00 p. m. a 4:00 p. m.
Lugar: Laboratorio de informática
Accede a BRIDGE desde un teléfono móvil y comprueba las páginas, la navegación, los botones, los formularios y el inicio de sesión. Documenta los errores. Completa las pruebas dentro del horario establecido, prepara un breve informe y actualiza el estado de la tarea.''',
    'ja': '''タスク名：プロジェクト進捗会議への参加
BRIDGEプロジェクトの進捗会議に参加してください。
日付：2026年10月7日（水曜日）
時間：午後2:00～3:00
場所：会議室B205
会議の前に担当タスクの進捗状況をまとめ、今後の作業計画を準備してください。会議終了後、決定事項を記録し、担当タスクのステータスを更新してください。''',
    'zh': '''【新任务通知】你有一项新的待完成任务：测试BRIDGE项目的邮箱注册功能。
日期：2026年10月5日（星期一）
时间：下午2:00–3:00
地点：计算机实验室
请使用新的邮箱地址创建账户，检查是否收到验证邮件，点击验证链接完成账户激活，并尝试登录系统。请在规定时间内完成任务，并及时更新任务状态。''',
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=['all', *SAMPLES], default='all')
    parser.add_argument('--target', choices=analysis.LANGUAGES, default='en')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env')
    mode = os.getenv('AI_MODE', 'demo')
    if mode not in ('gemini', 'openai'):
        print('Set AI_MODE to your working live provider in .env before this check.')
        return 1
    app = Flask('bridge_translation_check')
    app.config.update(AI_MODE=mode, GEMINI_MODEL=os.getenv('GEMINI_MODEL','gemini-2.5-flash'),
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY',''), OPENAI_MODEL=os.getenv('OPENAI_MODEL','gpt-4o-mini'),
        OPENAI_API_KEY=os.getenv('OPENAI_API_KEY',''))
    if not app.config['GEMINI_API_KEY' if mode=='gemini' else 'OPENAI_API_KEY']:
        print('The selected provider key is missing from .env.')
        return 1
    provider_name = 'gemini_json' if mode=='gemini' else 'openai_json'
    original = getattr(analysis, provider_name)
    report = {'provider':mode, 'model':app.config['GEMINI_MODEL' if mode=='gemini' else 'OPENAI_MODEL'],
        'analysis_sha256':hashlib.sha256(Path(analysis.__file__).read_bytes()).hexdigest(),
        'output_language':args.target, 'cases':[]}
    print('Translator:', analysis.__file__)
    print('Testing fictional messages only. No emails are sent; no task database is opened.')
    print('Each sample normally uses two AI requests; one correction may add a third.')
    failed = False
    try:
        for source in SAMPLES if args.source=='all' else [args.source]:
            case = {'source_language':source, 'source':SAMPLES[source], 'provider_outputs':[]}
            report['cases'].append(case)
            def capture(instructions, data, schema):
                result = original(instructions, data, schema)
                case['provider_outputs'].append({'stage':'extraction' if 'actions' in schema['properties'] else 'translation', 'result':result})
                return result
            setattr(analysis, provider_name, capture)
            print(source+' -> '+args.target+': running...', flush=True)
            try:
                with app.app_context():
                    result = analysis.analyze(SAMPLES[source], args.target, source)
                case['result'] = result
                case['status'] = 'completed; review the returned text for accuracy'
                for action in result['actions']:
                    # JSON escaping keeps Windows consoles with older code pages usable.
                    print(json.dumps({'title':action['title'], 'when':action['deadline_text'], 'where':action['location']},ensure_ascii=True))
            except analysis.AnalysisError as exc:
                failed = True
                case['status'] = 'failed'
                case['error'] = str(exc)
                print(str(exc))
                if '429' in str(exc) or 'connect' in str(exc).lower() or 'timed out' in str(exc):
                    print('Stopping after the provider failure to avoid repeated requests.')
                    break
    finally:
        setattr(analysis, provider_name, original)
    path = ROOT/'translation-check.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Report:', path)
    print('The report contains fictional samples and AI output, not API keys or email credentials.')
    return int(failed)

if __name__ == '__main__':
    raise SystemExit(main())
