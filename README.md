# ЭЕШ Арена — Англи үгсийн сан

Англи хэлний хамгийн түгээмэл үгсийг **Түлхүүр үгийн арга (Keyword Method)**-аар цээжлэх, 1v1 тэмцээнд ашиглах үгсийн сан.

> Түлхүүр үгийн арга: англи үгтэй төстэй дуудагдах монгол үг олж, түүнийг утгатай нь нэг хөгжилтэй дүр зурагт холбоно.
> *afraid* (айсан) → **авираад**: «Эрдэм булчинлаг том биетэй ч гөлөгнөөс **айдаг** тул харахаараа модонд **авираад** гарчихдаг.»
> Аткинсон, Рау нар (Stanford, 1975) боловсруулсан, судалгаагаар баталгаажсан арга.

**Төлөв:** 100 / 1000 үг (туршилтын багц). [Картуудыг харах →](docs/index.html)

## Үг бүрт

| Талбар | Жишээ (`borrow`) |
|---|---|
| `word` | borrow *(жишээ)* |
| `pos` / `pos_mn` | verb / үйл үг |
| `meaning_mn` | зээлэх |
| `ipa` | /ˈbɑːroʊ/ |
| `pron_mn` | бароу |
| `keyword_mn` | бороо |
| `mnemonic_mn` | **Бороо** орохоор би хөршөөсөө шүхэр **зээлдэг**. |
| `image.file` / `image.prompt` | `images/0123-borrow.webp` / Gemini-д өгөх тайлбар |
| `example.en` / `example.mn` | Can I borrow your pen? / Би үзгийг чинь зээлж болох уу? |
| `avoid_with` | Утга нь давхцдаг үгс (see ↔ look). Нэг асуултын сонголтод хамт гаргахгүй |

Тэмцээнд **зөвхөн хоёр төрлийн асуулт** гарна:
- **en2mn** — англи үг → монгол утгыг сонгох (`afraid → ?`)
- **mn2en** — монгол утга → англи үгийг сонгох (`зээлэх → ?`)

Түлхүүр үг, цээжлэх өгүүлбэр, шог зураг нь зөвхөн **давтлага, цээжлэх** үед харагдана.

## Бүтэц

```
data/
  source/words_0001-0100.psv   ← гараар засварладаг эх файл ("|" тусгаарлагчтай)
  words.json                   ← app ашиглана (build.py үүсгэнэ)
  words.csv                    ← Excel / Google Sheets-д нээх
  commonWords.ts               ← app-ийн src/data/commonWords.ts руу хуулна
  topics.json                  ← үг бүрийн сэдэв (Түгээмэл үгс багц доторх ангилал)
images/                        ← шог зургууд (generate_images.py үүсгэнэ)
lib/quiz.ts                    ← асуулт үүсгэх TypeScript функцууд
scripts/
  build.py                     ← эх файлаас JSON/CSV үүсгэж, алдааг шалгана
  generate_images.py           ← Gemini-ээр шог зураг үүсгэнэ
  preview.py                   ← docs/index.html картын хуудас үүсгэнэ
docs/index.html                ← бүх үгийг карт хэлбэрээр харах (GitHub Pages)
```

## Ашиглах

### 1. Үг нэмэх, засах
`data/source/*.psv` файлыг засаад:
```bash
python3 scripts/build.py      # JSON, CSV, commonWords.ts үүсгэнэ; алдаа байвал зогсоно
python3 scripts/preview.py    # картын хуудсыг шинэчилнэ
```

### 2. Шог зураг үүсгэх (Gemini)

**Хялбар арга — GitHub дээр товч дарж (компьютер шаардлагагүй):**
1. Repo → **Settings → Secrets and variables → Actions → New repository secret**
   Name: `GEMINI_API_KEY`, Secret: таны түлхүүр (https://aistudio.google.com/apikey)
2. Repo → **Actions → «Шог зураг үүсгэх (Gemini)» → Run workflow**
   Эхлээд `limit`-д `5` гэж бичиж туршина, дараа нь `0` (бүгдийг).
3. Дуусахад зургууд `images/` хавтсанд автоматаар commit хийгдэнэ. App тэднийг GitHub-аас шууд татна.
   Таалагдаагүй зургийг дахин гаргах: `ids` талбарт `3 17` гэх мэт id бичнэ.

**Компьютер дээрээс:**
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="таны_түлхүүр"
python3 scripts/generate_images.py --limit 5
```
- Аль хэдийн байгаа зургийг алгасна, тасарвал дахин ажиллуулахад үргэлжилнэ.
- Зургийн загварыг `scripts/build.py` доторх `IMAGE_STYLE`-аас өөрчилнө. Model-ийг `GEMINI_IMAGE_MODEL`-оор сольж болно.

### 3. App-д оруулах (ЭЕШ Арена)
1. `python3 scripts/build.py` ажиллуулна.
2. `data/commonWords.ts` → app-ийн `src/data/commonWords.ts`-ийг бүтнээр нь солино.
3. Зургийг хуулах шаардлагагүй: `commonWords.ts` доторх зургийн зам нь энэ repo-ийн `images/` руу (raw.githubusercontent.com) заадаг.

App дотор энэ нь **«Түгээмэл үгс»** багц болж гарна: үгийн картын ар талд шог зураг, түлхүүр үг, цээжлэх өгүүлбэр харагдана;
1v1 тулаан, шалгалтад en2mn / mn2en асуулт болж орно. Бусад багцад давхцсан үг (жишээ: *empty*) зөвхөн энэ багцад үлдэнэ.

`lib/quiz.ts` нь өөр app-д ашиглах бие даасан асуулт үүсгэгч (заавал биш).

## Картын хуудсыг онлайнаар нээх (GitHub Pages)
Repo → **Settings → Pages → Source: Deploy from a branch → Branch: `main`, folder: `/ (root)`**.
Дараа нь `https://<таны-нэр>.github.io/<repo-нэр>/docs/` хаягаар бүх картыг харна.

## Чанарын шалгалт
`build.py` дараахыг шалгана: бүх талбар бөглөгдсөн эсэх, үг/id давхардал, үгсийн аймаг, IPA хэлбэр, түлхүүр үг цээжлэх өгүүлбэрт орсон эсэх, утга давхцсан үгс.
GitHub-д push хийх бүрт `.github/workflows/validate.yml` автоматаар ажиллана.
