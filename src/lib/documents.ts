import { getCollection, type CollectionEntry } from 'astro:content';
import pdfMeta from '../generated/pdf-meta.json';

export type DocEntry = CollectionEntry<'documents'>;
export type DocVersion = DocEntry['data']['versions'][number];

export interface AttachmentInfo {
  title: string;
  description: string;
  href: string;
  filename: string;
  /** Расширение без точки: pdf, xlsx, csv… */
  ext: string;
  sha256: string;
  bytes: number;
  /** Число страниц — только для PDF. */
  pages: number | null;
}

export interface PdfInfo {
  href: string;
  filename: string;
  sha256: string;
  bytes: number;
  pages: number;
  text: string;
  attachments: AttachmentInfo[];
}

export const STATUS_LABEL: Record<DocEntry['data']['status'], string> = {
  active: 'Действует',
  draft: 'Черновик',
  published: 'Опубликован',
  archived: 'Архив',
};

const CATEGORY_ORDER = ['Устав', 'Whitepaper', 'Регламенты', 'Спецификации', 'Отчёты', 'Юридическое'];

export async function getDocuments(): Promise<DocEntry[]> {
  const docs = await getCollection('documents');
  return docs.sort(
    (a, b) =>
      CATEGORY_ORDER.indexOf(a.data.category) - CATEGORY_ORDER.indexOf(b.data.category) ||
      a.data.title.localeCompare(b.data.title, 'ru'),
  );
}

export function pdfFor(id: string, version: string): PdfInfo {
  const info = (pdfMeta as Record<string, Record<string, PdfInfo>>)[id]?.[version];
  if (!info) throw new Error(`Нет собранного PDF для ${id} v${version}. Запустите npm run pdfs.`);
  return info;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} МБ`;
}

export function formatDate(date?: Date): string {
  if (!date) return '—';
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function attachmentsLabel(n: number): string {
  const m10 = n % 10, m100 = n % 100;
  const word = m10 === 1 && m100 !== 11 ? 'приложение' : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? 'приложения' : 'приложений';
  return `${n} ${word}`;
}

export function pagesLabel(n: number): string {
  const m10 = n % 10, m100 = n % 100;
  const word = m10 === 1 && m100 !== 11 ? 'страница' : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? 'страницы' : 'страниц';
  return `${n} ${word}`;
}
