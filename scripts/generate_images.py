#!/usr/bin/env python3
"""
data/words.json доторх prompt бүрээр Gemini-ээр шог зураг үүсгэж images/ хавтсанд WebP болгон хадгална.

Суулгах:
    pip install google-genai pillow

Ажиллуулах:
    export GEMINI_API_KEY="таны_түлхүүр"          # Windows PowerShell: $env:GEMINI_API_KEY="..."
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
MODEL = os.environ.get('GEMINI_IMAGE_MODEL', 'gemini-2.5-flash-image')
SIZE = 512          # гаралтын хэмжээ (px)
QUALITY = 82        # WebP чанар
PAUSE = 4.0         # хүсэлт хоорондын завсар (сек), хязгаарт хүрэхгүйн тулд


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='хамгийн ихдээ хэдэн зураг үүсгэх')
    ap.add_argument('--ids', type=int, nargs='*', help='зөвхөн эдгээр id')
    ap.add_argument('--force', action='store_true', help='байгаа зургийг дарж бичих')
    args = ap.parse_args()

    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError:
        print('Эхлээд суулга:  pip install google-genai pillow'); sys.exit(1)

    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        print('GEMINI_API_KEY орчны хувьсагч тохируулаагүй байна.'); sys.exit(1)
    client = genai.Client(api_key=key)

    words = json.load(open(WORDS, encoding='utf-8'))
    if args.ids:
        words = [w for w in words if w['id'] in set(args.ids)]

    todo = [w for w in words if args.force or not os.path.exists(os.path.join(ROOT, w['image']['file']))]
    if args.limit:
        todo = todo[: args.limit]
    print(f'Model: {MODEL} | үүсгэх зураг: {len(todo)}')

    done, failed = 0, []
    for i, w in enumerate(todo, 1):
        out_path = os.path.join(ROOT, w['image']['file'])
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        for attempt in range(4):
            try:
                resp = client.models.generate_content(
                    model=MODEL,
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
                print(f'[{i}/{len(todo)}] ✓ {w["id"]:04d} {w["word"]}')
                break
            except Exception as e:  # noqa: BLE001
                wait = PAUSE * (2 ** attempt)
                print(f'[{i}/{len(todo)}] ! {w["word"]}: {e} → {wait:.0f}с хүлээгээд дахин оролдоно')
                time.sleep(wait)
        else:
            failed.append(w['word'])
        time.sleep(PAUSE)

    print(f'\nДууслаа: {done} амжилттай, {len(failed)} алдаатай')
    if failed:
        print('Алдаатай үгс:', ', '.join(failed))
        print('Дахин ажиллуулахад зөвхөн дутуу зургуудыг үүсгэнэ.')


if __name__ == '__main__':
    main()
