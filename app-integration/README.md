# ЭЕШ Арена app-д оруулах файлууд

AI Studio-ийн Code хэсэгт эдгээрийг **яг ижил замаар** буулгана (Raw → бүгдийг сонгох → хуулах → буулгах):

| Энэ repo дахь файл | App дахь зам |
|---|---|
| `data/commonWords.ts` | `src/data/commonWords.ts` (шинэ) |
| `data/basicWords.ts` | `src/data/basicWords.ts` («Суурь A1–A2» багц, 100 үг) |
| `app-integration/src/data/vocabMnemonics.ts` | `src/data/vocabMnemonics.ts` |
| `app-integration/src/components/FlashcardDeck.tsx` | `src/components/FlashcardDeck.tsx` (картын шинэ ар тал) |

Үүний дараа Gemini-д «Түгээмэл үгс» багцыг холбох prompt-ыг өгнө.
Шог зургууд app-д хуулах шаардлагагүй — GitHub-ийн `images/` хавтаснаас шууд татагдана.
