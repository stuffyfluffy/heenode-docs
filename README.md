# Heenode DAO — документация

Сайт документации и библиотека нормативных документов (PDF). Этап 1: без ончейн-логики.

**Стек:** Astro + Starlight · MDX · Typst → PDF · pdf.js · Pagefind · GitHub Actions.

## Запуск

```bash
npm install
pip install typst        # или установите CLI: https://github.com/typst/typst
npm run dev              # собирает PDF и запускает сайт на http://localhost:4321
npm run build            # статическая сборка в dist/
```

## Где что лежит

```
src/content/docs/            страницы документации (MDX/Markdown); en/ — английская версия
documents/<id>/meta.yaml     описание документа: название, категория, статус, версии
documents/<id>/v<x>.typ      исходник PDF на Typst
documents/_template.typ      общий шаблон оформления PDF (шапка, нумерация, «ЧЕРНОВИК»)
scripts/build-pdfs.mjs       сборка PDF + SHA-256 + число страниц + текст для поиска
src/pages/documents/         библиотека и страницы документов
src/components/PdfViewer.astro  просмотрщик на pdf.js (миниатюры, зум, страницы)
src/styles/theme.css         токены и стили из макета (светлая и тёмная темы)
```

## Как это работает

- `npm run pdfs` проходит по `documents/*/meta.yaml`, собирает каждую версию в `public/docs/<id>/v<версия>.pdf` и пишет хеши, размеры и текст в `src/generated/pdf-meta.json`. Обе папки генерируются — в git их нет.
- Хеш воспроизводим: дата внутри PDF фиксируется (поле `date` версии или `SOURCE_DATE_EPOCH`). Один и тот же исходник даёт один и тот же SHA-256.
- Текст PDF выводится на странице документа в блоке «Текст документа», поэтому поиск находит и содержимое документов.
- `/documents/<id>/` — текущая версия, `/documents/<id>/v<версия>/` — любая версия. В поиск попадает только текущая.

## Деплой

Workflow `.github/workflows/deploy.yml` собирает сайт на каждый PR и выкладывает на GitHub Pages при пуше в `main`.

1. Settings → Pages → Source: **GitHub Actions**.
2. Settings → Variables: `SITE_URL` — адрес сайта.
3. Лучше подключить собственный домен. Без него сайт будет в подпапке `/<repo>/` — тогда задайте `BASE_PATH=/<repo>/`. Ссылки внутри Markdown написаны от корня, и при подпапке их придётся поправить.

## Что заменить

- `[org]/[repo]` в `astro.config.mjs`, `.github/CODEOWNERS` и на страницах документов (`src/pages/documents/`).
- Плейсхолдеры в квадратных скобках в текстах и документах: `[X]%`, `[N]`, `[решение / дата]`.

## Задел под этап 2

В `meta.yaml` у каждой версии предусмотрены пустые поля `cid` (IPFS) и `proposalId` (предложение DAO). SHA-256 уже считается в CI — на втором этапе тот же хеш записывается в реестр контракта.
