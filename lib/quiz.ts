/**
 * Үгсийн сангаас 1v1 тэмцээний асуулт үүсгэх туслах функцууд.
 *
 * Хоёр төрлийн асуулт:
 *  - 'en2mn': англи үг харуулаад монгол утгыг сонгуулна   (afraid → айсан)
 *  - 'mn2en': монгол утга харуулаад англи үгийг сонгуулна (зээлэх → borrow)
 *
 * Ашиглах:
 *   import words from '../data/words.json';
 *   import { makeQuestion, makeMatch } from './quiz';
 *   const q = makeQuestion(words[0], words, 'en2mn');
 */

export type Pos = 'noun' | 'verb' | 'adjective' | 'adverb';

export interface VocabWord {
  id: number;
  word: string;
  pos: Pos[];
  pos_mn: string[];
  meaning_mn: string;
  ipa: string;
  pron_mn: string;
  keyword_mn: string;
  mnemonic_mn: string;
  image: { file: string; prompt: string };
  example: { en: string; mn: string };
  /** Утга нь давхцдаг үгс — нэг асуултын сонголтод хамт гаргахгүй */
  avoid_with: string[];
}

export type Direction = 'en2mn' | 'mn2en';

export interface Question {
  wordId: number;
  direction: Direction;
  prompt: string;
  /** 4 сонголт, холилдсон */
  options: string[];
  correctIndex: number;
}

/** Хариултын сонголтод харуулах монгол утга (эхний утгыг авна: "нээх; нээлттэй" → "нээх") */
export const shortMeaning = (w: VocabWord) => w.meaning_mn.split(';')[0].trim();

function shuffle<T>(arr: T[], rand: () => number): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** Хоёр тоглогчид ижил асуулт гаргахын тулд seed-тэй санамсаргүй тоо */
export function seeded(seed: number) {
  let s = seed >>> 0 || 1;
  return () => {
    s ^= s << 13;
    s ^= s >>> 17;
    s ^= s << 5;
    return ((s >>> 0) % 1_000_000) / 1_000_000;
  };
}

export function makeQuestion(
  target: VocabWord,
  all: VocabWord[],
  direction: Direction,
  rand: () => number = Math.random,
  optionCount = 4
): Question {
  const banned = new Set([target.word, ...target.avoid_with]);
  const targetMeaning = shortMeaning(target);
  const pool = all.filter(
    (w) => !banned.has(w.word) && !w.avoid_with.includes(target.word) && shortMeaning(w) !== targetMeaning
  );
  // Ижил үгсийн аймгийнхыг түрүүлж сонгоно — тэгвэл таахад хэцүү, шударга болно
  const samePos = pool.filter((w) => w.pos.some((p) => target.pos.includes(p)));
  const rest = pool.filter((w) => !samePos.includes(w));
  const label = (w: VocabWord) => (direction === 'en2mn' ? shortMeaning(w) : w.word);

  // Буруу сонголтууд хоорондоо ч давхцахгүй байх ёстой (way, road хоёул "зам" гэх мэт)
  const distractors: VocabWord[] = [];
  const usedLabels = new Set([label(target)]);
  const blocked = new Set(banned);
  for (const w of [...shuffle(samePos, rand), ...shuffle(rest, rand)]) {
    if (distractors.length >= optionCount - 1) break;
    if (blocked.has(w.word) || usedLabels.has(label(w))) continue;
    distractors.push(w);
    usedLabels.add(label(w));
    w.avoid_with.forEach((x) => blocked.add(x));
  }
  const options = shuffle([target, ...distractors], rand);
  return {
    wordId: target.id,
    direction,
    prompt: direction === 'en2mn' ? target.word : target.meaning_mn,
    options: options.map(label),
    correctIndex: options.indexOf(target),
  };
}

/** Нэг тоглолтын асуултууд: хоёр чиглэлийг ээлжлүүлж, давхардалгүй үг сонгоно */
export function makeMatch(all: VocabWord[], count: number, seed: number): Question[] {
  const rand = seeded(seed);
  return shuffle(all, rand)
    .slice(0, count)
    .map((w, i) => makeQuestion(w, all, i % 2 === 0 ? 'en2mn' : 'mn2en', rand));
}
