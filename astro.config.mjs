// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { satteri } from '@astrojs/markdown-satteri';
import { baseLinks } from './src/lib/base-links.mjs';

// SITE_URL и BASE_PATH задаются в CI. Для своего домена BASE_PATH не нужен.
// Схему можно не указывать: «example.org» превратится в «https://example.org».
const siteEnv = process.env.SITE_URL?.trim();
const site = siteEnv ? (/^https?:\/\//.test(siteEnv) ? siteEnv : `https://${siteEnv}`) : 'https://docs.example.org';
const base = process.env.BASE_PATH || '/';

export default defineConfig({
  site,
  base,
  markdown: {
    // Ссылки в контенте пишутся от корня («/dao/treasury/») — base добавляется при сборке.
    processor: satteri({ hastPlugins: [baseLinks(base)] }),
  },
  integrations: [
    starlight({
      title: 'Heenode DAO',
      description: 'Документация и нормативные документы Heenode DAO',
      logo: { light: './src/assets/logo-light.svg', dark: './src/assets/logo-dark.svg', replacesTitle: false },
      favicon: '/favicon.svg',
      defaultLocale: 'root',
      locales: {
        root: { label: 'Русский', lang: 'ru' },
        en: { label: 'English', lang: 'en' },
      },
      // TODO: заменить на адрес репозитория
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/stuffyfluffy/heenode-docs' }],
      editLink: { baseUrl: 'https://github.com/stuffyfluffy/heenode-docs/edit/main/' },
      lastUpdated: true,
      customCss: [
        '@fontsource/ibm-plex-sans/400.css',
        '@fontsource/ibm-plex-sans/500.css',
        '@fontsource/ibm-plex-sans/600.css',
        '@fontsource/ibm-plex-mono/400.css',
        '@fontsource/ibm-plex-mono/500.css',
        '@fontsource/unbounded/500.css',
        '@fontsource/unbounded/600.css',
        './src/styles/theme.css',
      ],
      components: {
        SiteTitle: './src/components/SiteTitle.astro',
      },
      sidebar: [
        {
          label: 'Начало',
          translations: { en: 'Getting started' },
          items: [
            { slug: 'index', label: 'Введение', translations: { en: 'Introduction' } },
            { slug: 'start/mission' },
            { slug: 'start/glossary' },
          ],
        },
        {
          label: 'Устройство DAO',
          translations: { en: 'How the DAO works' },
          items: [
            { slug: 'dao/liquid-democracy' },
            { slug: 'dao/skill-graph' },
            { slug: 'dao/subdao-fork' },
            { slug: 'dao/treasury' },
          ],
        },
        {
          label: 'Участникам',
          translations: { en: 'For members' },
          items: [
            { slug: 'members/join' },
            { slug: 'members/learn' },
            { slug: 'members/teach' },
            { slug: 'members/research' },
          ],
        },
        {
          label: 'Управление',
          translations: { en: 'Governance' },
          items: [
            { slug: 'governance/proposals' },
            { slug: 'governance/voting' },
            { slug: 'governance/delegation' },
          ],
        },
        {
          label: 'Нормативные документы',
          translations: { en: 'Normative documents' },
          items: [
            { slug: 'normative/overview' },
            { slug: 'normative/charter' },
            { slug: 'normative/user-agreement' },
          ],
        },
        {
          label: 'Все документы (PDF)',
          translations: { en: 'All documents (PDF)' },
          link: '/documents/',
          attrs: { class: 'sidebar-docs-link' },
        },
      ],
    }),
  ],
});
