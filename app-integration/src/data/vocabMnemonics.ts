/**
 * Түлхүүр үгийн аргын (Keyword Method) өгөгдөл.
 * Англи үг (жижиг үсгээр) → түлхүүр үг, цээжлэх өгүүлбэр, шог зураг, кирилл дуудлага.
 * Энд бичигдсэн үгсийн картын ар талд шог зураг, цээжлэх өгүүлбэр харагдана.
 * Зураг: public/vocab/images/<файл>.webp
 */
import { COMMON_MNEMONICS } from './commonWords';

export interface MnemonicEntry {
  keyword: string;
  mnemonic: string;
  pronMn?: string;
  image?: string;
}

export const VOCAB_MNEMONICS: Record<string, MnemonicEntry> = {
  ...COMMON_MNEMONICS,
  neighbor: {
    keyword: 'нэг бэр',
    pronMn: 'нэйбэр',
    mnemonic: 'Манай хөрш айлд нэг бэр ирээд, тэр өдрөөс хойш хоёр айл бие биедээ байнга тусалдаг болов.',
    image: '/vocab/images/neighbor.webp',
  },
};
