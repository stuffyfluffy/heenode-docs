/** Ссылка с учётом base (например, при деплое на GitHub Pages в подпапку). */
export function url(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
}
