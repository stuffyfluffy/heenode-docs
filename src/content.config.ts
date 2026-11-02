import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const CATEGORIES = [
  'Устав',
  'Whitepaper',
  'Регламенты',
  'Спецификации',
  'Отчёты',
  'Юридическое',
] as const;

const attachment = z
  .object({
    /** Название на странице документа: «Финансовый расчёт», «Обоснование». */
    title: z.string(),
    /** Пояснение в одну строку. */
    description: z.string().optional(),
    /** Исходник Typst относительно папки документа — соберётся в PDF. */
    source: z.string().optional(),
    /** Готовый файл любого формата (PDF, XLSX, CSV…) относительно папки документа. */
    file: z.string().optional(),
  })
  .refine((a) => Boolean(a.source) !== Boolean(a.file), {
    message: 'У приложения должно быть ровно одно из полей: source или file',
  });

const version = z.object({
  /** Номер версии, например "1.0". Используется в адресе: /documents/<id>/v1.0/ */
  version: z.string(),
  /** Дата утверждения или публикации, ГГГГ-ММ-ДД. Пусто — ещё не утверждено. */
  date: z.coerce.date().optional(),
  /** Кем и как утверждено: «Решение совета № …», «Общее собрание …». */
  approved: z.string().optional(),
  /** Исходник Typst относительно папки документа. */
  source: z.string().optional(),
  /** Готовый PDF относительно папки документа, если исходника нет. */
  file: z.string().optional(),
  /** Приложения к этой версии: обоснование, финансовые расчёты, исходные данные. */
  attachments: z.array(attachment).default([]),
  /** Этап 2: CID в IPFS и ID предложения DAO. Пока не заполняются. */
  cid: z.string().optional(),
  proposalId: z.string().optional(),
});

const documents = defineCollection({
  loader: glob({
    pattern: '*/meta.yaml',
    base: './documents',
    generateId: ({ entry }) => entry.split('/')[0],
  }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.enum(CATEGORIES),
    status: z.enum(['active', 'draft', 'published', 'archived']),
    /** Показывать в блоке «Ключевые документы» */
    featured: z.boolean().default(false),
    /** Страница документации, связанная с документом (slug) */
    related: z.array(z.object({ label: z.string(), href: z.string() })).default([]),
    /** Версии — от новой к старой. Первая считается текущей. */
    versions: z.array(version).min(1),
  }),
});

export const collections = {
  docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }),
  documents,
};
