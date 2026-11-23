#!/usr/bin/env python3
"""
data/source/*.psv  →  data/words.json + data/words.csv

Ажиллуулах:  python3 scripts/build.py
Алдаа олдвол дэлгэцэнд хэвлээд 1 кодтой гарна (GitHub Actions-д ашиглахад тохиромжтой).
"""
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'source')
OUT_JSON = os.path.join(ROOT, 'data', 'words.json')
OUT_CSV = os.path.join(ROOT, 'data', 'words.csv')

COLUMNS = ['id', 'word', 'pos', 'meaning_mn', 'ipa', 'pron_mn', 'keyword_mn',
           'mnemonic_mn', 'image_scene', 'example_en', 'example_mn']

POS_MN = {
    'noun': 'нэр үг',
    'verb': 'үйл үг',
    'adjective': 'тэмдэг нэр',
    'adverb': 'дайвар үг',
}

# App зургийг GitHub-аас шууд татна (images/ хавтас). Өөр газар байршуулбал энд солино.
IMAGE_BASE = os.environ.get('VOCAB_IMAGE_BASE', 'https://raw.githubusercontent.com/eerdka7208/eyesh-vocab/main/')

# Бүх зурагт нэг ижил загвар өгөх
IMAGE_STYLE = (
    'Funny cartoon illustration for a vocabulary memory card. '
    'Flat vector style, bold clean outlines, bright cheerful colors, simple plain light background, '
    'exaggerated expressions, one clear scene, square 1:1. '
    'Absolutely no text, no letters, no numbers, no words anywhere in the image. Scene: '
)


def slug(word):
    return re.sub(r'[^a-z0-9]+', '-', word.lower()).strip('-')


def stem(s, n=3):
    return s.lower().replace('ё', 'е')[:n]


def main():
    rows, errors, warnings = [], [], []
    files = sorted(glob.glob(os.path.join(SRC, '*.psv')))
    if not files:
        print('data/source/*.psv файл олдсонгүй'); sys.exit(1)

    for path in files:
        name = os.path.basename(path)
        with open(path, encoding='utf-8') as f:
            for ln, line in enumerate(f, 1):
                line = line.rstrip('\n')
                if not line.strip() or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) != len(COLUMNS):
                    errors.append(f'{name}:{ln}: {len(parts)} багана байна, {len(COLUMNS)} байх ёстой')
                    continue
                r = dict(zip(COLUMNS, parts))
                r['_loc'] = f'{name}:{ln}'
                rows.append(r)

    seen_words, seen_ids = {}, {}
    out = []
    for r in rows:
        loc = r['_loc']
        for k in COLUMNS:
            if not r[k]:
                errors.append(f'{loc}: "{k}" хоосон байна')
        try:
            rid = int(r['id'])
        except ValueError:
            errors.append(f'{loc}: id тоо биш'); continue
        if rid in seen_ids:
            errors.append(f'{loc}: id {rid} давхардсан ({seen_ids[rid]})')
        seen_ids[rid] = loc
        w = r['word'].lower()
        if w in seen_words:
            errors.append(f'{loc}: "{w}" үг давхардсан ({seen_words[w]})')
        seen_words[w] = loc

        pos = [p.strip() for p in r['pos'].split(',')]
        for p in pos:
            if p not in POS_MN:
                errors.append(f'{loc}: үгсийн аймаг "{p}" буруу (noun/verb/adjective/adverb)')
        if not (r['ipa'].startswith('/') and r['ipa'].endswith('/')):
            errors.append(f'{loc}: IPA /.../ хэлбэртэй байх ёстой')
        if stem(r['keyword_mn']) not in r['mnemonic_mn'].lower().replace('ё', 'е'):
            warnings.append(f'{loc}: түлхүүр үг "{r["keyword_mn"]}" цээжлэх өгүүлбэрт олдсонгүй')
        if not r['example_en'][-1] in '.!?':
            warnings.append(f'{loc}: англи жишээ цэг/асуултын тэмдэгээр төгсөөгүй')

        s = slug(r['word'])
        out.append({
            'id': rid,
            'word': r['word'],
            'pos': pos,
            'pos_mn': [POS_MN.get(p, p) for p in pos],
            'meaning_mn': r['meaning_mn'],
            'ipa': r['ipa'],
            'pron_mn': r['pron_mn'],
            'keyword_mn': r['keyword_mn'],
            'mnemonic_mn': r['mnemonic_mn'],
            'image': {
                'file': f'images/{rid:04d}-{s}.webp',
                'prompt': IMAGE_STYLE + r['image_scene'],
            },
            'example': {'en': r['example_en'], 'mn': r['example_mn']},
        })

    # Утга давхцах үгс: тэмцээнд нэг асуултын хариултын сонголтод хамт гарч болохгүй
    def tokens(m):
        return {t.strip() for t in re.split(r'[;,()]', m) if t.strip()}
    for a in out:
        ta = tokens(a['meaning_mn'])
        a['avoid_with'] = sorted(b['word'] for b in out if b is not a and ta & tokens(b['meaning_mn']))
        if a['avoid_with']:
            warnings.append(f'"{a["word"]}" ({a["meaning_mn"]}) утга нь {a["avoid_with"]}-тэй давхцаж байна → avoid_with-д бичигдлээ')

    out.sort(key=lambda x: x['id'])
    ids = [x['id'] for x in out]
    if ids and ids != list(range(1, len(ids) + 1)):
        warnings.append('id дараалал 1-ээс тасралтгүй биш байна')

    for wmsg in warnings:
        print('АНХААР:', wmsg)
    if errors:
        for e in errors:
            print('АЛДАА:', e)
        print(f'\n{len(errors)} алдаа олдлоо. Файл үүсгэсэнгүй.')
        sys.exit(1)

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write('\n')
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['id', 'word', 'pos', 'pos_mn', 'meaning_mn', 'ipa', 'pron_mn', 'keyword_mn',
                     'mnemonic_mn', 'example_en', 'example_mn', 'image_file', 'image_prompt', 'avoid_with'])
        for x in out:
            wr.writerow([x['id'], x['word'], ', '.join(x['pos']), ', '.join(x['pos_mn']), x['meaning_mn'],
                         x['ipa'], x['pron_mn'], x['keyword_mn'], x['mnemonic_mn'], x['example']['en'],
                         x['example']['mn'], x['image']['file'], x['image']['prompt'], ', '.join(x['avoid_with'])])
    # App-д шууд хуулах файл: src/data/commonWords.ts ("Түгээмэл үгс" багц)
    topics_path = os.path.join(ROOT, 'data', 'topics.json')
    topics = json.load(open(topics_path, encoding='utf-8')) if os.path.exists(topics_path) else {}
    default_topic = {'noun': 'Түгээмэл нэр үг', 'verb': 'Өдөр тутмын үйл үг',
                     'adjective': 'Түгээмэл тэмдэг нэр', 'adverb': 'Түгээмэл дайвар үг'}
    pos_short = {'noun': 'n.', 'verb': 'v.', 'adjective': 'adj.', 'adverb': 'adv.'}

    def q(v):
        return "'" + v.replace('\\', '\\\\').replace("'", "\\'") + "'"

    # Багц бүр: (нэр, id-ийн муж, файл, үгсийн хувьсагч, mnemonic хувьсагч, id-аар эрэмбэлэх эсэх)
    # BASIC нь app-ын хуучин дарааллыг (vb_basic_NNN) хадгалах ёстой тул id-аар эрэмбэлнэ.
    decks = [
        ('Түгээмэл үгс', range(1, 101), 'commonWords.ts', 'COMMON_WORDS', 'COMMON_MNEMONICS', False),
        ('Суурь A1–A2', range(101, 201), 'basicWords.ts', 'BASIC_WORDS', 'BASIC_MNEMONICS', True),
        ('Өдөр тутам', range(201, 301), 'dailyWords.ts', 'DAILY_WORDS', 'DAILY_MNEMONICS', True),
        ('Ажил & Бизнес', range(301, 401), 'workWords.ts', 'WORK_WORDS', 'WORK_MNEMONICS', True),
        ('Технологи', range(401, 501), 'techWords.ts', 'TECH_WORDS', 'TECH_MNEMONICS', True),
        ('Академик', range(501, 601), 'academicWords.ts', 'ACADEMIC_WORDS', 'ACADEMIC_MNEMONICS', True),
    ]
    topic_order = list(dict.fromkeys(topics.values()))
    for deck_name, id_range, fname, words_var, mn_var, by_id in decks:
        items = [x for x in out if x['id'] in id_range]
        if not items:
            continue
        if by_id:
            rows = sorted(items, key=lambda x: x['id'])
        else:
            rows = sorted(items, key=lambda x: (topic_order.index(topics[x['word']])
                                                if x['word'] in topics else 999, x['id']))
        lines = ['/* eslint-disable */',
                 '// Автоматаар үүсгэсэн (eyesh-vocab/scripts/build.py). Гараар бүү засаарай.',
                 f'// «{deck_name}» багц. Мөр бүр: [сэдэв, англи, монгол, IPA, үгсийн аймаг, жишээ (англи), жишээ (монгол)]',
                 "import type { MnemonicEntry } from './vocabMnemonics';", '',
                 f"export const {words_var}: [string, string, string, string, 'n.' | 'v.' | 'adj.' | 'adv.' | 'phr.', string, string][] = ["]
        cur = None
        for x in rows:
            t = topics.get(x['word'], default_topic[x['pos'][0]])
            if t != cur:
                lines.append(f'  // {t}')
                cur = t
            lines.append(f"  [{q(t)}, {q(x['word'])}, {q(x['meaning_mn'])}, {q(x['ipa'])}, {q(pos_short[x['pos'][0]])}, "
                         f"{q(x['example']['en'])}, {q(x['example']['mn'])}],")
        lines += ['];', '', f'export const {mn_var}: Record<string, MnemonicEntry> = {{']
        for x in items:
            lines.append(f"  {q(x['word'])}: {{ keyword: {q(x['keyword_mn'])}, pronMn: {q(x['pron_mn'])}, "
                         f"mnemonic: {q(x['mnemonic_mn'])}, image: {q(IMAGE_BASE + x['image']['file'])} }},")
        lines += ['};', '']
        with open(os.path.join(ROOT, 'data', fname), 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f'✓ {deck_name}: {len(items)} үг → data/{fname}')
    print(f'\n✓ нийт {len(out)} үг → data/words.json, data/words.csv')


if __name__ == '__main__':
    main()
