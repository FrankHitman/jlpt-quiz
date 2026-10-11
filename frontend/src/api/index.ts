import type { QuizApi } from '../types';
import { realApi } from './client';

/**
 * 整合策略（T4）：
 * - 開發／演示：VITE_USE_MOCK != 'false'（預設）→ 動態載入內建 mock 題庫。
 * - 上線：VITE_USE_MOCK=false npm run build → 只打包 realApi；
 *   mock 題庫（含 correct_option）會被 tree-shake 掉，不會出現在 production 包裡。
 */
export const isMockMode: boolean =
  (import.meta.env.VITE_USE_MOCK as string | undefined) !== 'false';

let cached: Promise<QuizApi> | null = null;

export function getApi(): Promise<QuizApi> {
  if (!cached) {
    cached = isMockMode
      ? import('../mocks/mockServer').then((m) => m.mockApi)
      : Promise.resolve(realApi);
  }
  return cached;
}
