#!/usr/bin/env python3
"""Run JSONL packs against an OpenAI-compatible endpoint.

run_pack.py pack.jsonl --out responses.jsonl [--base-url URL] [--model NAME]
  [--temperature T] [--max-tokens N] [--concurrency N]
  [--request-options provider-options.json] [--config FILE]

Endpoint/model/key: SOUL_TEST_BASE_URL / SOUL_TEST_MODEL / SOUL_TEST_API_KEY.
Resume only an identical pack and effective generation configuration; use a new
output file after changing either. Credentials never enter fingerprints.
Provider options may set reasoning parameters, but not model/messages/budgets.
"""
import argparse
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_config
from _evaluation import fingerprint


def chat(messages, base_url, key, model, temperature, max_tokens, options=None):
    body = {**(options or {}), 'model': model, 'messages': messages,
            'temperature': temperature, 'max_tokens': max_tokens}
    req = urllib.request.Request(base_url.rstrip('/') + '/chat/completions',
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json',
        **({'Authorization': f'Bearer {key}'} if key else {})})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode())
    choice = data['choices'][0]
    msg = choice['message']
    text = msg.get('content') or msg.get('refusal') or ''
    if not isinstance(text, str):
        raise ValueError('endpoint returned non-text content; adapt the transport explicitly')
    finish = choice.get('finish_reason')
    return {'text': text, 'reasoning': msg.get('reasoning_content') or msg.get('reasoning'),
            'usage': data.get('usage'), 'finish_reason': finish,
            'incomplete': not text.strip() or finish in ('length', 'max_tokens', 'content_filter', 'tool_calls')}


def call(row, base_url, key, model, temperature, max_tokens, options=None):
    result = {**row, 'model': model, 'error': None, 'completion_status': 'complete'}
    history = [{'role': 'system', 'content': row['system']}] if row['system'] else []
    try:
        if row['kind'] == 'scenario':
            responses, reasoning, usages, reasons = [], [], [], []
            result.update(responses=responses, reasoning=reasoning, usage_by_turn=usages, finish_reasons=reasons)
            for t in row['turns']:
                history.append({'role': 'user', 'content': t['text']})
                reply = chat(history, base_url, key, model, temperature, max_tokens, options)
                responses.append(reply['text']); reasoning.append(reply['reasoning'])
                usages.append(reply['usage']); reasons.append(reply['finish_reason'])
                if reply['incomplete']:
                    raise ValueError(f"incomplete scenario turn {len(responses)} (finish_reason={reply['finish_reason']})")
                history.append({'role': 'assistant', 'content': reply['text']})
        else:
            reply = chat(history + [{'role': 'user', 'content': row['prompt']}],
                         base_url, key, model, temperature, max_tokens, options)
            result.update(response=reply['text'], reasoning=reply['reasoning'],
                          usage=reply['usage'], finish_reason=reply['finish_reason'])
            if reply['incomplete']:
                raise ValueError(f"incomplete final response (finish_reason={reply['finish_reason']})")
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        result['completion_status'] = 'incomplete'
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pack'); ap.add_argument('--out', required=True)
    ap.add_argument('--base-url', default=os.environ.get('SOUL_TEST_BASE_URL'))
    ap.add_argument('--model', default=os.environ.get('SOUL_TEST_MODEL'))
    ap.add_argument('--concurrency', type=int); ap.add_argument('--temperature', type=float)
    ap.add_argument('--max-tokens', type=int); ap.add_argument('--config')
    ap.add_argument('--request-options', help='JSON object of provider-specific generation options')
    args = ap.parse_args(argv)
    if not args.base_url or not args.model:
        ap.error('set --base-url/--model or SOUL_TEST_BASE_URL/SOUL_TEST_MODEL')
    cfg = load_config(args.config)['testing']
    options = dict(cfg.get('request_options', {}))
    if args.request_options:
        override = json.loads(Path(args.request_options).read_text(encoding='utf-8'))
        if not isinstance(override, dict): ap.error('--request-options must contain a JSON object')
        options.update(override)
    if set(options) & {'model', 'messages', 'temperature', 'max_tokens', 'max_completion_tokens', 'stream', 'api_key', 'headers'}:
        ap.error('request options may not override transport, model, messages or explicit sampling flags')
    settings = {'base_url': args.base_url.rstrip('/'), 'model': args.model,
                'temperature': args.temperature if args.temperature is not None else cfg['temperature'],
                'max_tokens': args.max_tokens if args.max_tokens is not None else cfg['max_tokens'],
                'request_options': options}
    concurrency = args.concurrency if args.concurrency is not None else cfg['concurrency']
    settings['concurrency'] = concurrency
    if settings['max_tokens'] < 1 or concurrency < 1: ap.error('max-tokens and concurrency must be positive')
    rows = [json.loads(l) for l in Path(args.pack).read_text(encoding='utf-8').splitlines() if l.strip()]
    if not rows or len({r['run_id'] for r in rows}) != len(rows):
        ap.error('pack must be nonempty with unique run_id values')
    execution = fingerprint({'rows': sorted(rows, key=lambda r:r['run_id']), 'generation':settings})
    out, done = Path(args.out), set()
    if out.exists():
        for line in out.read_text(encoding='utf-8').splitlines():
            if line.strip():
                old = json.loads(line)
                if old.get('execution_fingerprint') != execution:
                    ap.error('existing results belong to a different or legacy execution; choose a fresh --out file')
                if not old.get('error') and old.get('completion_status') == 'complete': done.add(old['run_id'])
    todo = [r for r in rows if r['run_id'] not in done]
    out.parent.mkdir(parents=True, exist_ok=True)
    errors = 0
    with ThreadPoolExecutor(max_workers=concurrency) as pool, out.open('a', encoding='utf-8') as fh:
        futures = [pool.submit(call, r, args.base_url, os.environ.get('SOUL_TEST_API_KEY'), args.model,
                               settings['temperature'], settings['max_tokens'], options) for r in todo]
        for future in as_completed(futures):
            result = future.result(); result.update(execution_fingerprint=execution, generation=settings)
            errors += bool(result['error'])
            fh.write(json.dumps(result, ensure_ascii=False) + '\n'); fh.flush()
    print(json.dumps({'ran':len(todo), 'skipped_done':len(done), 'errors':errors,
                      'execution_fingerprint':execution, 'out':str(out)}))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
