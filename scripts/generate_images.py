#!/usr/bin/env python3
"""
data/words.json доторх prompt бүрээр шог зураг үүсгэж images/ хавтсанд WebP болгон хадгална.
OPENAI_API_KEY байвал OpenAI (gpt-image-1-mini → gpt-image-1 → dall-e-3), үгүй бол GEMINI_API_KEY-ээр Gemini ашиглана.

Суулгах:
    pip install -r requirements.txt

Ажиллуулах:
    export OPENAI_API_KEY="таны_түлхүүр"          # эсвэл GEMINI_API_KEY
    python3 scripts/generate_images.py              # байхгүй бүх зургийг үүсгэнэ
    python3 scripts/generate_images.py --limit 5    # эхний 5-ыг туршиж үзэх
    python3 scripts/generate_images.py --ids 1 25 99
    python3 scripts/generate_images.py --force --ids 7   # нэг зургийг дахин үүсгэх

Аль хэдийн байгаа зургийг алгасна, тиймээс тасарсан бол дахин ажиллуулахад үргэлжилнэ.
Model-ийг GEMINI_IMAGE_MODEL орчны хувьсагчаар сольж болно.
"""
import argparse
import io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS = os.path.join(ROOT, 'data', 'words.json')
# Эхнийх нь ажиллахгүй бол (нэр солигдсон гэх мэт) дараагийнхыг оролдоно
MODELS = [m for m in os.environ.get('GEMINI_IMAGE_MODEL', '').split(',') if m] or [
    'gemini-2.5-flash-image',
    'gemini-3.1-flash-image-preview',
]
REPORT = os.path.join(ROOT, 'images', '_report.json')
AVAILABLE_IMAGE_MODELS = []
SIZE = 512          # гаралтын хэмжээ (px)
QUALITY = 82        # WebP чанар
PAUSE = 4.0         # хүсэлт хоорондын завсар (сек), хязгаарт хүрэхгүйн тулд


def write_report(done, failed, errors, model, fatal=None):
    import datetime
    total = len([f for f in os.listdir(os.path.join(ROOT, 'images')) if f.endswith('.webp')])
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    json.dump({'time': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'model': model, 'generated_now': done,
               'images_total': total, 'failed': failed, 'fatal_error': fatal,
               'available_image_models': AVAILABLE_IMAGE_MODELS, 'models_tried': MODELS,
               'errors': {k: v for k, v in list(errors.items())[:20]}},
              open(REPORT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


OPENAI_MODELS = [m for m in os.environ.get('OPENAI_IMAGE_MODEL', '').split(',') if m] or [
    'gpt-image-1-mini',
    'gpt-image-1',
    'dall-e-3',
]
OPENAI_QUALITY = os.environ.get('OPENAI_IMAGE_QUALITY', 'medium')  # low / medium / high


def openai_generate(client, model, prompt):
    """Нэг зураг үүсгээд PNG/WebP байт буцаана."""
    import base64
    if model.startswith('dall-e'):
        r = client.images.generate(model=model, prompt=prompt[:3900], size='1024x1024', n=1,
                                   quality='standard', response_format='b64_json')
    else:
        r = client.images.generate(model=model, prompt=prompt, size='1024x1024', n=1, quality=OPENAI_QUALITY)
    return base64.b64decode(r.data[0].b64_json)


def run_openai(todo, key):
    from openai import OpenAI
    from PIL import Image
    global MODELS
    MODELS = list(OPENAI_MODELS)
    key = key.strip()
    if not key.startswith('sk-'):
        write_report(0, [], {}, MODELS[0], fatal=f'OPENAI_API_KEY буруу: "sk-"-ээр эхлэх ёстой (одоо "{key[:12]}..." гэж эхэлж байна)')
        print('OPENAI_API_KEY буруу байна (sk- -ээр эхлэх ёстой).'); sys.exit(1)
    client = OpenAI(api_key=key)
    idx = 0
    done, failed, errors = 0, [], {}
    print(f'OpenAI model: {MODELS[idx]} | үүсгэх зураг: {len(todo)}')
    for i, w in enumerate(todo, 1):
        out_path = os.path.join(ROOT, w['image']['file'])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        ok = False
        attempt = 0
        while attempt < 4:
            try:
                data = openai_generate(client, MODELS[idx], w['image']['prompt'])
                img = Image.open(io.BytesIO(data)).convert('RGB')
                s_ = min(img.size)
                l, t = (img.width - s_) // 2, (img.height - s_) // 2
                img = img.crop((l, t, l + s_, t + s_)).resize((SIZE, SIZE), Image.LANCZOS)
                img.save(out_path, 'WEBP', quality=QUALITY, method=6)
                done += 1
                errors.pop(w['word'], None)
                ok = True
                print(f'[{i}/{len(todo)}] ✓ {w["id"]:04d} {w["word"]} ({MODELS[idx]})')
                break
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                low = msg.lower()
                errors[w['word']] = msg[:300]
                # model олдсонгүй / баталгаажуулалт шаардсан / эрх алга → дараагийн model
                if (('model' in low and ('not found' in low or 'does not exist' in low or 'verified' in low
                                         or 'verify' in low or 'access' in low)) or '403' in msg) and idx + 1 < len(MODELS):
                    idx += 1
                    print(f'  model солив → {MODELS[idx]} ({msg[:120]})')
                    continue
                # түлхүүр буруу эсвэл төлбөр дууссан → шууд зогсоно
                if '401' in msg or 'invalid_api_key' in low or 'incorrect api key' in low \
                        or 'insufficient_quota' in low or 'billing' in low:
                    write_report(done, failed + [w['word']], errors, MODELS[idx], fatal=msg[:500])
                    print('Төлбөр/квотын алдаа:', msg[:300]); sys.exit(1)
                # агуулгын шүүлтүүр → энэ зургийг алгасна
                if 'safety' in low or 'content_policy' in low or 'moderation' in low:
                    print(f'  агуулгын шүүлтүүрт өртөв: {w["word"]}')
                    break
                attempt += 1
                wait = PAUSE * (2 ** attempt)
                print(f'[{i}/{len(todo)}] ! {w["word"]}: {msg[:160]} → {wait:.0f}с хүлээгээд дахин')
                time.sleep(wait)
        if not ok:
            failed.append(w['word'])
        time.sleep(0.5)
    write_report(done, failed, errors, MODELS[idx])
    print(f'\nДууслаа: {done} амжилттай, {len(failed)} алдаатай')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='хамгийн ихдээ хэдэн зураг үүсгэх')
    ap.add_argument('--ids', type=int, nargs='*', help='зөвхөн эдгээр id')
    ap.add_argument('--force', action='store_true', help='байгаа зургийг дарж бичих')
    args = ap.parse_args()

    words = json.load(open(WORDS, encoding='utf-8'))
    if args.ids:
        words = [w for w in words if w['id'] in set(args.ids)]
    todo = [w for w in words if args.force or not os.path.exists(os.path.join(ROOT, w['image']['file']))]
    if args.limit:
        todo = todo[: args.limit]

    if os.environ.get('OPENAI_API_KEY'):
        return run_openai(todo, os.environ['OPENAI_API_KEY'])

    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError:
        print('Эхлээд суулга:  pip install -r requirements.txt'); sys.exit(1)

    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        os.makedirs(os.path.join(ROOT, 'images'), exist_ok=True)
        write_report(0, [], {}, MODELS[0], fatal='OPENAI_API_KEY эсвэл GEMINI_API_KEY тохируулаагүй')
        print('OPENAI_API_KEY эсвэл GEMINI_API_KEY тохируулаагүй байна.'); sys.exit(1)
    try:
        client = genai.Client(api_key=key, http_options={'api_version': 'v1beta'})
    except TypeError:
        client = genai.Client(api_key=key)

    # Энэ түлхүүрээр ашиглах боломжтой зураг үүсгэх model-ууд (тайланд бичнэ)
    global AVAILABLE_IMAGE_MODELS
    try:
        AVAILABLE_IMAGE_MODELS = sorted(
            m.name.split('/')[-1] for m in client.models.list() if 'image' in (m.name or '').lower()
        )
        print('Боломжтой зургийн model-ууд:', AVAILABLE_IMAGE_MODELS)
        for m in reversed(AVAILABLE_IMAGE_MODELS):  # жагсаалтад байгаа шинэ model-уудыг нөөцөд нэмнэ
            if m not in MODELS and 'imagen' not in m:
                MODELS.append(m)
    except Exception as e:  # noqa: BLE001
        AVAILABLE_IMAGE_MODELS = [f'list error: {e}'[:200]]

    model_idx = 0
    print(f'Model: {MODELS[model_idx]} | үүсгэх зураг: {len(todo)}')

    done, failed, errors = 0, [], {}
    for i, w in enumerate(todo, 1):
        out_path = os.path.join(ROOT, w['image']['file'])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        for attempt in range(4):
            try:
                resp = client.models.generate_content(
                    model=MODELS[model_idx],
                    contents=[w['image']['prompt']],
                    config=types.GenerateContentConfig(response_modalities=['IMAGE']),
                )
                data = None
                for part in resp.candidates[0].content.parts:
                    if getattr(part, 'inline_data', None) and part.inline_data.data:
                        data = part.inline_data.data
                        break
                if not data:
                    raise RuntimeError('хариунд зураг алга')
                img = Image.open(io.BytesIO(data)).convert('RGB')
                # төвөөс нь дөрвөлжин тайрч, хэмжээг багасгана
                s = min(img.size)
                l, t = (img.width - s) // 2, (img.height - s) // 2
                img = img.crop((l, t, l + s, t + s)).resize((SIZE, SIZE), Image.LANCZOS)
                img.save(out_path, 'WEBP', quality=QUALITY, method=6)
                done += 1
                errors.pop(w['word'], None)
                print(f'[{i}/{len(todo)}] ✓ {w["id"]:04d} {w["word"]}')
                break
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                errors[w['word']] = msg[:300]
                # model олдсонгүй → дараагийн model руу шилжинэ
                if ('404' in msg or 'not found' in msg.lower()) and model_idx + 1 < len(MODELS):
                    model_idx += 1
                    print(f'  model солив → {MODELS[model_idx]}')
                    continue
                # энэ model-д үнэгүй квот алга → дараагийн model-ийг оролдоно
                if '429' in msg and 'limit: 0' in msg and model_idx + 1 < len(MODELS):
                    model_idx += 1
                    print(f'  квот 0 → model солив: {MODELS[model_idx]}')
                    continue
                # төлбөр/квот → цаашид оролдох нь утгагүй
                if 'billing' in msg.lower() or ('429' in msg and 'limit: 0' in msg):
                    write_report(done, failed + [w['word']], errors, MODELS[model_idx], fatal=msg[:500])
                    print('Квот/төлбөрийн алдаа:', msg[:300]); sys.exit(1)
                wait = PAUSE * (2 ** attempt)
                print(f'[{i}/{len(todo)}] ! {w["word"]}: {e} → {wait:.0f}с хүлээгээд дахин оролдоно')
                time.sleep(wait)
        else:
            failed.append(w['word'])
        time.sleep(PAUSE)

    write_report(done, failed, errors, MODELS[model_idx])
    print(f'\nДууслаа: {done} амжилттай, {len(failed)} алдаатай')
    if failed:
        print('Алдаатай үгс:', ', '.join(failed))
        print('Дахин ажиллуулахад зөвхөн дутуу зургуудыг үүсгэнэ.')


if __name__ == '__main__':
    main()
