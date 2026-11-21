import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Check,
  ChevronLeft,
  ChevronRight,
  KeyRound,
  Play,
  RotateCcw,
  RotateCw,
  Shuffle,
  Volume2,
} from 'lucide-react';
import { SUBJECTS } from '../data/subjects';
import { VOCAB_BANK } from '../data/vocabBank';
import type { SubjectId, VocabWord } from '../types/game';
import { speakEnglish } from '../utils/speech';

const MASTERED_STORAGE_KEY = 'word_arena_mastered_v1';

type MasteryFilter = 'all' | 'learning' | 'mastered';

function readMasteredIds(): Set<string> {
  try {
    const raw = localStorage.getItem(MASTERED_STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return new Set(parsed.filter((x): x is string => typeof x === 'string'));
    }
  } catch {
    // ignore storage errors
  }
  return new Set();
}

function saveMasteredIds(ids: Set<string>): void {
  try {
    localStorage.setItem(MASTERED_STORAGE_KEY, JSON.stringify(Array.from(ids)));
  } catch {
    // ignore storage errors
  }
}

/** Цээжлэх өгүүлбэр доторх түлхүүр үгийг тодруулна */
function highlightKeyword(sentence: string, keyword?: string): React.ReactNode {
  if (!keyword) return sentence;
  const lower = sentence.toLowerCase();
  let i = lower.indexOf(keyword.toLowerCase());
  let j = i >= 0 ? i + keyword.length : -1;
  if (i < 0) {
    i = lower.indexOf(keyword.toLowerCase().slice(0, 3));
    if (i < 0) return sentence;
    j = i;
  }
  while (j < sentence.length && /[\p{L}\p{N}-]/u.test(sentence[j])) j++;
  return (
    <>
      {sentence.slice(0, i)}
      <strong className="font-extrabold text-[var(--sky-dark)]">{sentence.slice(i, j)}</strong>
      {sentence.slice(j)}
    </>
  );
}

/** Шог зураг. Зураг хараахан байхгүй бол түлхүүр үгтэй өнгөт хавтан харуулна. */
const MnemonicImage: React.FC<{ word: VocabWord }> = ({ word }) => {
  const [failed, setFailed] = useState(!word.image);
  useEffect(() => setFailed(!word.image), [word.id, word.image]);
  const box = 'w-[40%] max-w-[220px] aspect-square shrink-0 rounded-2xl';
  if (failed) {
    const hue = [...word.id].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 360, 7);
    return (
      <div
        className={`${box} flex flex-col items-center justify-center text-center p-2`}
        style={{ background: `linear-gradient(135deg, hsl(${hue} 85% 92%), hsl(${(hue + 40) % 360} 80% 82%))` }}
      >
        <KeyRound className="w-6 h-6 mb-1" style={{ color: `hsl(${hue} 55% 32%)` }} />
        <span
          className="font-display font-extrabold text-[15px] sm:text-[20px] leading-tight break-words max-w-full"
          style={{ color: `hsl(${hue} 55% 26%)` }}
        >
          {word.keyword}
        </span>
      </div>
    );
  }
  return (
    <img
      src={word.image}
      alt={word.mnemonic || word.english}
      draggable={false}
      onError={() => setFailed(true)}
      className={`${box} object-cover bg-[var(--surface-2)]`}
    />
  );
};

interface FlashcardDeckProps {
  selectedSubject: SubjectId;
  onSelectSubject: (id: SubjectId) => void;
  onStartQuiz?: (deckId: SubjectId) => void;
}

export const FlashcardDeck: React.FC<FlashcardDeckProps> = ({
  selectedSubject,
  onSelectSubject,
  onStartQuiz,
}) => {
  const [wordsSource, setWordsSource] = useState<VocabWord[]>(VOCAB_BANK);
  const [masteredIds, setMasteredIds] = useState<Set<string>>(() => readMasteredIds());
  const [masteryFilter, setMasteryFilter] = useState<MasteryFilter>('all');
  const [shuffleSeed, setShuffleSeed] = useState(0);
  const [cardIndex, setCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  // Sync from server /api/vocab if available
  useEffect(() => {
    let cancelled = false;
    fetch('/api/vocab?deck=ALL')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!cancelled && data && Array.isArray(data.words) && data.words.length > 0) {
          setWordsSource(data.words);
        }
      })
      .catch(() => {
        // Keep bundled VOCAB_BANK fallback
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const deckStatsMap = useMemo(() => {
    const map: Record<string, { total: number; mastered: number }> = {
      ALL: { total: wordsSource.length, mastered: 0 },
    };
    for (const s of SUBJECTS) {
      if (s.id !== 'ALL') {
        map[s.id] = { total: 0, mastered: 0 };
      }
    }
    for (const w of wordsSource) {
      const isM = masteredIds.has(w.id);
      if (isM) map.ALL.mastered += 1;
      if (!map[w.deck]) {
        map[w.deck] = { total: 0, mastered: 0 };
      }
      map[w.deck].total += 1;
      if (isM) map[w.deck].mastered += 1;
    }
    return map;
  }, [wordsSource, masteredIds]);

  const deckWords = useMemo(() => {
    return selectedSubject === 'ALL'
      ? wordsSource
      : wordsSource.filter((w) => w.deck === selectedSubject);
  }, [wordsSource, selectedSubject]);

  const deckMasteredCount = useMemo(
    () => deckWords.filter((w) => masteredIds.has(w.id)).length,
    [deckWords, masteredIds]
  );

  const visibleWords = useMemo(() => {
    let list = deckWords.filter((w) => {
      if (masteryFilter === 'mastered') return masteredIds.has(w.id);
      if (masteryFilter === 'learning') return !masteredIds.has(w.id);
      return true;
    });
    if (shuffleSeed > 0) {
      list = [...list].sort((a, b) => {
        const ha = (a.id.charCodeAt(a.id.length - 1) * 31 + shuffleSeed * 17) % 97;
        const hb = (b.id.charCodeAt(b.id.length - 1) * 31 + shuffleSeed * 17) % 97;
        return ha - hb;
      });
    }
    return list;
  }, [deckWords, masteryFilter, masteredIds, shuffleSeed]);

  useEffect(() => {
    setCardIndex(0);
    setIsFlipped(false);
  }, [selectedSubject, masteryFilter, shuffleSeed]);

  const safeIndex =
    visibleWords.length > 0 ? Math.min(cardIndex, visibleWords.length - 1) : 0;
  const currentWord = visibleWords[safeIndex] || null;
  const isCurrentMastered = currentWord ? masteredIds.has(currentWord.id) : false;

  const goPrev = useCallback(() => {
    if (visibleWords.length <= 1) return;
    setIsFlipped(false);
    setCardIndex((prev) => (prev - 1 + visibleWords.length) % visibleWords.length);
  }, [visibleWords.length]);

  const goNext = useCallback(() => {
    if (visibleWords.length <= 1) return;
    setIsFlipped(false);
    setCardIndex((prev) => (prev + 1) % visibleWords.length);
  }, [visibleWords.length]);

  const markWord = useCallback(
    (mastered: boolean) => {
      if (!currentWord) return;
      const next = new Set(masteredIds);
      if (mastered) {
        next.add(currentWord.id);
      } else {
        next.delete(currentWord.id);
      }
      setMasteredIds(next);
      saveMasteredIds(next);
      if (visibleWords.length > 1) {
        setIsFlipped(false);
        setCardIndex((prev) => (prev + 1) % visibleWords.length);
      } else {
        setIsFlipped(false);
      }
    },
    [currentWord, masteredIds, visibleWords.length]
  );

  // Keyboard shortcuts: Space to flip, Left/Right arrows to navigate
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      if (e.code === 'Space') {
        e.preventDefault();
        setIsFlipped((f) => !f);
      } else if (e.code === 'ArrowRight') {
        goNext();
      } else if (e.code === 'ArrowLeft') {
        goPrev();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [goNext, goPrev]);

  const masteryPct =
    deckWords.length > 0 ? Math.round((deckMasteredCount / deckWords.length) * 100) : 0;

  const selectedDeckMeta =
    SUBJECTS.find((s) => s.id === selectedSubject) || SUBJECTS[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
      {/* LEFT / MAIN STAGE: Interactive Flashcard + Actions */}
      <div className="lg:col-span-7 space-y-4 lg:space-y-5 min-w-0">
        {currentWord ? (
          <>
            {/* Focused 3D Flashcard */}
            <div
              className="perspective-1000 cursor-pointer select-none focus:outline-none group"
              onClick={() => setIsFlipped((prev) => !prev)}
              role="button"
              tabIndex={0}
              aria-label={isFlipped ? 'Англи үгийг харах' : 'Монгол утгыг харах'}
              onKeyDown={(e) => {
                if (e.key === 'Enter') setIsFlipped((prev) => !prev);
              }}
            >
              <div
                className={`relative w-full min-h-[420px] sm:min-h-[420px] lg:min-h-[440px] transition-transform duration-500 preserve-3d ${
                  isFlipped ? 'rotate-y-180' : ''
                }`}
              >
                {/* Front Face (English) */}
                <div
                  className={`absolute inset-0 backface-hidden rounded-[22px] border-2 border-b-[5px] p-6 sm:p-8 lg:p-10 flex flex-col justify-between bg-[var(--surface)] transition-colors ${
                    isCurrentMastered
                      ? 'border-[var(--accent)]/60'
                      : 'border-[var(--border)] group-hover:border-[var(--border-strong)]'
                  }`}
                >
                  {/* Top Metadata Row */}
                  <div className="flex items-center justify-between gap-3 text-[13px] text-[var(--text-muted)]">
                    <span className="truncate font-medium">
                      {currentWord.deckName} · {currentWord.topic}
                    </span>
                    <span className="tabular-nums font-bold shrink-0">
                      {safeIndex + 1} / {visibleWords.length}
                    </span>
                  </div>

                  {/* Center Focal Word */}
                  <div className="my-auto text-center space-y-3 py-5">
                    <div className="font-mono text-[13px] sm:text-[14px] font-medium text-[var(--text-muted)]">
                      {currentWord.partOfSpeech}
                      {currentWord.ipa ? ` · ${currentWord.ipa}` : ''}
                    </div>
                    <div className="font-display text-[32px] sm:text-[44px] lg:text-[50px] leading-[1.12] font-extrabold text-[var(--text)] tracking-tight break-words px-2">
                      {currentWord.english}
                    </div>
                    <div className="pt-2 flex justify-center">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          speakEnglish(currentWord.english);
                        }}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border-2 border-[var(--border)] border-b-[3px] bg-[var(--surface-2)] hover:bg-[var(--sky-soft)] hover:border-[var(--sky)]/50 hover:text-[var(--sky-dark)] text-[13.5px] font-bold text-[var(--text)] whitespace-nowrap shrink-0 cursor-pointer transition-all active:translate-y-[1px] active:border-b-2"
                      >
                        <Volume2 className="w-4 h-4 text-[var(--sky)]" />
                        Сонсох
                      </button>
                    </div>
                  </div>

                  {/* Bottom Hint Row */}
                  <div className="flex items-center justify-between gap-3 text-[13px] text-[var(--text-muted)] pt-3.5 border-t border-[var(--border)]">
                    <span
                      className={`inline-flex items-center gap-1.5 font-semibold ${
                        isCurrentMastered ? 'text-[var(--accent-text)]' : ''
                      }`}
                    >
                      {isCurrentMastered ? (
                        <>
                          <Check className="w-3.5 h-3.5" strokeWidth={2.8} />
                          Цээжилсэн
                        </>
                      ) : (
                        'Давтаж буй'
                      )}
                    </span>
                    <span className="inline-flex items-center gap-1.5 font-bold text-[var(--text-muted)] group-hover:text-[var(--text)] transition-colors">
                      <RotateCw className="w-3.5 h-3.5" />
                      Утга харах
                    </span>
                  </div>
                </div>

                {/* Back Face: үндсэн үг · шог зураг · утга · цээжлэх өгүүлбэр · жишээ */}
                <div
                  className={`absolute inset-0 backface-hidden rotate-y-180 rounded-[22px] border-2 border-b-[5px] p-4 sm:p-6 lg:p-7 flex flex-col gap-3 sm:gap-4 overflow-hidden bg-[var(--surface)] transition-colors ${
                    isCurrentMastered
                      ? 'border-[var(--accent)]/60'
                      : 'border-[var(--sky)]/55'
                  }`}
                >
                  {/* Зүүн дээд: үндсэн үг, дуудлага · Баруун дээд: сонсох, дугаар */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2 flex-wrap">
                        <span className="font-display text-[24px] sm:text-[30px] leading-none font-extrabold text-[var(--text)] tracking-tight break-words">
                          {currentWord.english}
                        </span>
                        <span className="text-[13px] font-semibold text-[var(--text-muted)]">
                          {currentWord.partOfSpeech}
                        </span>
                      </div>
                      <div className="mt-1.5 text-[13px] text-[var(--text-muted)]">
                        <span className="font-mono">{currentWord.ipa}</span>
                        {currentWord.pronMn && (
                          <span className="font-semibold"> · {currentWord.pronMn}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          speakEnglish(currentWord.english);
                        }}
                        aria-label="Үгийг сонсох"
                        className="p-2 rounded-xl border-2 border-[var(--border)] bg-[var(--surface-2)] text-[var(--sky)] hover:bg-[var(--sky-soft)] hover:border-[var(--sky)]/50 cursor-pointer transition-colors"
                      >
                        <Volume2 className="w-4 h-4" />
                      </button>
                      <span className="text-[13px] tabular-nums font-bold text-[var(--text-muted)]">
                        {safeIndex + 1} / {visibleWords.length}
                      </span>
                    </div>
                  </div>

                  {currentWord.mnemonic ? (
                    /* Шог зураг + утга + цээжлэх өгүүлбэр */
                    <div className="flex-1 min-h-0 flex items-center gap-3 sm:gap-5">
                      <MnemonicImage word={currentWord} />
                      <div className="flex-1 min-w-0 flex flex-col gap-2.5">
                        <div className="font-display text-[22px] sm:text-[30px] leading-[1.15] font-extrabold text-[var(--accent-text)] break-words">
                          {currentWord.mongolian}
                        </div>
                        <div className="rounded-2xl border-2 border-[var(--sky)]/35 bg-[var(--sky-soft)] px-3 py-2.5">
                          <div className="flex items-center gap-1.5 text-[11.5px] font-extrabold uppercase tracking-wide text-[var(--sky-dark)]">
                            <KeyRound className="w-3.5 h-3.5" />
                            {currentWord.keyword}
                          </div>
                          <p className="mt-1 text-[13.5px] sm:text-[15px] leading-snug text-[var(--text)]">
                            {highlightKeyword(currentWord.mnemonic, currentWord.keyword)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Цээжлэх өгүүлбэргүй үг: утгыг төвд нь томоор */
                    <div className="flex-1 flex items-center justify-center text-center">
                      <div className="font-display text-[26px] sm:text-[34px] lg:text-[38px] leading-[1.18] font-extrabold text-[var(--accent-text)] break-words px-2">
                        {currentWord.mongolian}
                      </div>
                    </div>
                  )}

                  {/* Жишээ өгүүлбэр */}
                  <div className="pt-3 border-t border-[var(--border)] space-y-1">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-[14px] sm:text-[15.5px] font-semibold text-[var(--text)] leading-snug">
                        “{currentWord.exampleEn}”
                      </p>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          speakEnglish(currentWord.exampleEn);
                        }}
                        aria-label="Жишээ өгүүлбэр сонсох"
                        className="p-1.5 rounded-lg border-2 border-[var(--border)] bg-[var(--surface-2)] text-[var(--sky)] shrink-0 hover:bg-[var(--sky-soft)] hover:border-[var(--sky)]/50 cursor-pointer transition-colors"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <p className="text-[13px] sm:text-[14px] text-[var(--text-muted)] leading-snug">
                      {currentWord.exampleMn}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Primary Learning Decision Pair */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => markWord(false)}
                className="min-h-[48px] py-3 px-4 rounded-2xl border-2 border-[var(--border)] border-b-4 bg-[var(--surface)] hover:bg-[var(--danger-soft)] hover:border-[var(--danger)]/55 text-[var(--danger)] font-display font-bold text-[15px] inline-flex items-center justify-center gap-2 whitespace-nowrap cursor-pointer transition-all active:translate-y-[2px] active:border-b-2"
              >
                <RotateCcw className="w-4 h-4" strokeWidth={2.3} />
                Дахин давтах
              </button>

              <button
                type="button"
                onClick={() => markWord(true)}
                className="btn-gold-cta min-h-[48px] py-3 px-4 text-[15px] inline-flex items-center justify-center gap-2 whitespace-nowrap cursor-pointer"
              >
                <Check className="w-4 h-4" strokeWidth={2.8} />
                {isCurrentMastered ? 'Цээжилсэн' : 'Цээжиллээ'}
              </button>
            </div>

            {/* Quiet Navigation & Shuffle Bar */}
            <div className="flex items-center justify-between gap-2 pt-1">
              <button
                type="button"
                onClick={goPrev}
                disabled={visibleWords.length <= 1}
                className="btn-warm-secondary min-h-[42px] px-3.5 py-2 text-[13.5px] inline-flex items-center gap-1.5 whitespace-nowrap cursor-pointer disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
                Өмнөх
              </button>

              <div className="flex items-center gap-2">
                <span className="text-[13.5px] font-bold tabular-nums text-[var(--text-muted)] px-1">
                  {safeIndex + 1} / {visibleWords.length}
                </span>
                <button
                  type="button"
                  onClick={() => setShuffleSeed((s) => s + 1)}
                  title="Картуудыг холих"
                  className="btn-warm-secondary min-h-[42px] px-3 py-2 text-[13px] font-semibold inline-flex items-center gap-1.5 whitespace-nowrap cursor-pointer"
                >
                  <Shuffle className="w-3.5 h-3.5 text-[var(--sky)]" />
                  <span>Холих</span>
                </button>
              </div>

              <button
                type="button"
                onClick={goNext}
                disabled={visibleWords.length <= 1}
                className="btn-warm-secondary min-h-[42px] px-3.5 py-2 text-[13.5px] inline-flex items-center gap-1.5 whitespace-nowrap cursor-pointer disabled:opacity-40"
              >
                Дараах
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Subtle Desktop Keyboard Hint */}
            <div className="hidden lg:flex items-center justify-center gap-3 text-[12.5px] font-medium text-[var(--text-muted)] pt-1">
              <span>Space — эргүүлэх</span>
              <span aria-hidden="true">·</span>
              <span>← / → — шилжих</span>
            </div>
          </>
        ) : (
          <div className="warm-card p-8 sm:p-10 text-center space-y-3 min-h-[330px] lg:min-h-[420px] flex flex-col items-center justify-center">
            <p className="font-display font-extrabold text-lg text-[var(--text)]">
              Энэ шүүлтүүрт одоогоор үг алга
            </p>
            <p className="text-sm text-[var(--text-muted)] max-w-sm">
              Бүх үгээ эсвэл өөр багц сонгон үргэлжлүүлээрэй.
            </p>
            <div className="flex flex-wrap justify-center gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setMasteryFilter('all')}
                className="btn-warm-secondary px-4 py-2.5 text-sm cursor-pointer"
              >
                Бүх үгийг харах
              </button>
              {onStartQuiz && (
                <button
                  type="button"
                  onClick={() => onStartQuiz(selectedSubject)}
                  className="btn-gold-cta px-5 py-2.5 text-sm cursor-pointer inline-flex items-center gap-1.5"
                >
                  <Play className="w-4 h-4" />
                  Шалгалт өгөх
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* RIGHT RAIL: Progress, Filter & Deck Selector */}
      <aside className="lg:col-span-5 lg:sticky lg:top-24 warm-card p-5 sm:p-6 space-y-5 min-w-0">
        {/* Progress Overview */}
        <div className="space-y-2.5">
          <div className="flex items-baseline justify-between gap-3">
            <span className="font-display font-bold text-[16px] text-[var(--text)]">
              {selectedDeckMeta.shortName} · Ахиц
            </span>
            <div className="flex items-baseline gap-1.5 tabular-nums">
              <span className="font-display font-extrabold text-[17px] text-[var(--accent-text)]">
                {deckMasteredCount} / {deckWords.length}
              </span>
              <span className="text-[13px] font-semibold text-[var(--text-muted)]">
                ({masteryPct}%)
              </span>
            </div>
          </div>

          <div className="duo-progress-track">
            <div
              className="duo-progress-fill"
              style={{ width: `${masteryPct}%` }}
            />
          </div>
        </div>

        {/* Status Filter Tabs (Clean inline strip — no nested bordered card) */}
        <div className="pt-4 border-t border-[var(--border)] space-y-2.5">
          <div className="text-[13px] font-bold text-[var(--text-muted)]">
            Шүүлтүүр
          </div>
          <div className="grid grid-cols-3 gap-1.5" role="group" aria-label="Үгийн төлөв">
            {(
              [
                { id: 'all', label: 'Бүгд', count: deckWords.length },
                { id: 'learning', label: 'Шинэ', count: deckWords.length - deckMasteredCount },
                { id: 'mastered', label: 'Цээжилсэн', count: deckMasteredCount },
              ] as const
            ).map((f) => {
              const active = masteryFilter === f.id;
              return (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setMasteryFilter(f.id)}
                  className={`py-2 px-2 rounded-xl text-[13px] font-bold whitespace-nowrap cursor-pointer transition-colors text-center border-2 ${
                    active
                      ? 'bg-[var(--accent-soft)] border-[var(--accent)] text-[var(--accent-text)]'
                      : 'bg-[var(--surface-2)] border-transparent text-[var(--text-muted)] hover:text-[var(--text)]'
                  }`}
                >
                  {f.label}{' '}
                  <span className="tabular-nums opacity-80">{f.count}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Deck Selector Grid (Clean 2x3 tiles) */}
        <div className="pt-4 border-t border-[var(--border)] space-y-2.5">
          <div className="flex items-center justify-between text-[13px]">
            <span className="font-bold text-[var(--text-muted)]">Үгийн багц</span>
            <span className="text-[var(--text-muted)] tabular-nums font-medium">
              {SUBJECTS.length} сэдэв
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2" role="group" aria-label="Үгийн багц">
            {SUBJECTS.map((s) => {
              const active = s.id === selectedSubject;
              const stats = deckStatsMap[s.id] || { total: 0, mastered: 0 };
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => onSelectSubject(s.id)}
                  className={`px-3.5 py-2.5 rounded-2xl text-left border-2 border-b-[3px] cursor-pointer transition-all active:translate-y-[1px] active:border-b-2 flex flex-col gap-0.5 min-w-0 ${
                    active
                      ? 'bg-[var(--sky-soft)] border-[var(--sky)] text-[var(--sky-dark)]'
                      : 'bg-[var(--surface)] border-[var(--border)] text-[var(--text)] hover:bg-[var(--surface-2)] hover:border-[var(--border-strong)]'
                  }`}
                >
                  <span className="font-display font-bold text-[14px] truncate">
                    {s.shortName}
                  </span>
                  <span
                    className={`text-[12.5px] font-semibold tabular-nums ${
                      active ? 'text-[var(--sky-dark)]/80' : 'text-[var(--text-muted)]'
                    }`}
                  >
                    {stats.mastered} / {stats.total} үг
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Quick Action to Test Current Deck */}
        {onStartQuiz && (
          <div className="pt-4 border-t border-[var(--border)]">
            <button
              type="button"
              onClick={() => onStartQuiz(selectedSubject)}
              className="btn-warm-secondary w-full min-h-[46px] px-4 py-2.5 text-[15px] font-bold inline-flex items-center justify-center gap-2 cursor-pointer"
            >
              <Play className="w-4 h-4 text-[var(--accent-text)]" />
              Энэ багцаар шалгалт өгөх
            </button>
          </div>
        )}
      </aside>
    </div>
  );
};
