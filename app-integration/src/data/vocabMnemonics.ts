/**
 * Түлхүүр үгийн аргын (Keyword Method) өгөгдөл.
 * Англи үг (жижиг үсгээр) → түлхүүр үг, цээжлэх өгүүлбэр, шог зураг, кирилл дуудлага.
 * Энд бичигдсэн үгсийн картын ар талд шог зураг, цээжлэх өгүүлбэр харагдана.
 * Зураг: public/vocab/images/<файл>.webp
 */
import { COMMON_MNEMONICS } from './commonWords';
import { BASIC_MNEMONICS } from './basicWords';
import { DAILY_MNEMONICS } from './dailyWords';
import { WORK_MNEMONICS } from './workWords';
import { TECH_MNEMONICS } from './techWords';
import { ACADEMIC_MNEMONICS } from './academicWords';

export interface MnemonicEntry {
  keyword: string;
  mnemonic: string;
  pronMn?: string;
  image?: string;
}

export const VOCAB_MNEMONICS: Record<string, MnemonicEntry> = {
  ...COMMON_MNEMONICS,
  ...BASIC_MNEMONICS,
  ...DAILY_MNEMONICS,
  ...WORK_MNEMONICS,
  ...TECH_MNEMONICS,
  ...ACADEMIC_MNEMONICS,
};
