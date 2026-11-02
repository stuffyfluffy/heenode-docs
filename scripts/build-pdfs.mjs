// Собирает PDF из исходников Typst, считает SHA-256, число страниц и извлекает текст для поиска.
//
//   documents/<id>/meta.yaml        — описание документа и список версий
//   documents/<id>/v<версия>.typ    — исходник (или готовый PDF в поле `file`)
//
// Результат:
//   public/docs/<id>/v<версия>.pdf  — файлы, которые раздаёт сайт
//   src/generated/pdf-meta.json     — хеши, размеры, страницы и текст для страниц сайта
//
// Компилятор: `typst` из PATH, иначе Python-пакет `typst` (pip install typst).
// Хеш воспроизводим: дата создания PDF фиксируется (дата версии или SOURCE_DATE_EPOCH).

import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import { copyFile, mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { parse } from 'yaml';

const ROOT = process.cwd();
const SRC_DIR = path.join(ROOT, 'documents');
const OUT_DIR = path.join(ROOT, 'public', 'docs');
const META_OUT = path.join(ROOT, 'src', 'generated', 'pdf-meta.json');

function hasTypstCli() {
  return spawnSync('typst', ['--version'], { stdio: 'ignore' }).status === 0;
}

function hasTypstPy() {
  return spawnSync('python', ['-c', 'import typst'], { stdio: 'ignore' }).status === 0;
}

function epochFor(version) {
  if (version.date) return Math.floor(new Date(version.date).getTime() / 1000);
  return Number(process.env.SOURCE_DATE_EPOCH ?? 0);
}

function compileTypst(input, output, epoch, compiler) {
  if (compiler === 'cli') {
    execFileSync('typst', ['compile', '--root', SRC_DIR, input, output], {
      stdio: 'inherit',
      env: { ...process.env, SOURCE_DATE_EPOCH: String(epoch) },
    });
    return;
  }
  const code = [
    'import sys, typst',
    'typst.compile(sys.argv[1], output=sys.argv[2], root=sys.argv[3], timestamp=int(sys.argv[4]))',
  ].join('\n');
  execFileSync('python', ['-c', code, input, output, SRC_DIR, String(epoch)], { stdio: 'inherit' });
}

async function inspectPdf(file) {
  const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs');
  const data = new Uint8Array(await readFile(file));
  const task = pdfjs.getDocument({ data, useSystemFonts: false, verbosity: 0 });
  const doc = await task.promise;
  const parts = [];
  for (let i = 1; i <= doc.numPages; i++) {
    const page = await doc.getPage(i);
    const content = await page.getTextContent();
    parts.push(content.items.map((it) => ('str' in it ? it.str + (it.hasEOL ? '\n' : '') : '')).join(''));
  }
  const pages = doc.numPages;
  await task.destroy();
  return { pages, text: parts.join('\n\n').replace(/[ \t]+\n/g, '\n').trim() };
}

async function main() {
  if (!existsSync(SRC_DIR)) {
    console.warn('[pdfs] папка documents/ не найдена — пропускаю');
    return;
  }
  const compiler = hasTypstCli() ? 'cli' : hasTypstPy() ? 'py' : null;
  const result = {};
  const ids = (await readdir(SRC_DIR, { withFileTypes: true }))
    .filter((d) => d.isDirectory() && !d.name.startsWith('_'))
    .map((d) => d.name)
    .sort();

  for (const id of ids) {
    const metaPath = path.join(SRC_DIR, id, 'meta.yaml');
    if (!existsSync(metaPath)) continue;
    const meta = parse(await readFile(metaPath, 'utf8'));
    result[id] = {};
    await mkdir(path.join(OUT_DIR, id), { recursive: true });

    for (const version of meta.versions ?? []) {
      const out = path.join(OUT_DIR, id, `v${version.version}.pdf`);
      if (version.source) {
        if (!compiler) {
          throw new Error(
            `[pdfs] нет компилятора Typst для ${id}/${version.source}. Установите typst (https://typst.app) или pip install typst`,
          );
        }
        compileTypst(path.join(SRC_DIR, id, version.source), out, epochFor(version), compiler);
      } else if (version.file) {
        await copyFile(path.join(SRC_DIR, id, version.file), out);
      } else {
        throw new Error(`[pdfs] у ${id} v${version.version} нет ни source, ни file`);
      }

      const buf = await readFile(out);
      const { pages, text } = await inspectPdf(out);
      result[id][version.version] = {
        href: `docs/${id}/v${version.version}.pdf`,
        filename: `${id}-v${version.version}.pdf`,
        sha256: createHash('sha256').update(buf).digest('hex'),
        bytes: (await stat(out)).size,
        pages,
        text,
      };
      console.log(`[pdfs] ${id} v${version.version}: ${pages} стр., ${result[id][version.version].sha256.slice(0, 12)}…`);
    }
  }

  await mkdir(path.dirname(META_OUT), { recursive: true });
  await writeFile(META_OUT, JSON.stringify(result, null, 2));
  console.log(`[pdfs] готово: ${ids.length} документов → ${path.relative(ROOT, META_OUT)}`);
}

main().catch((err) => {
  console.error(err.message ?? err);
  process.exit(1);
});
