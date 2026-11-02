/**
 * Hast-плагин Sätteri: добавляет base к ссылкам от корня сайта («/members/join/»)
 * в Markdown и MDX, включая атрибут href у компонентов вроде <LinkCard>.
 * Нужно при деплое в подпапку (GitHub Pages): иначе ссылки ведут мимо сайта.
 */
export function baseLinks(base = '/') {
  const prefix = base.replace(/\/$/, '');

  /** Новый href или undefined, если менять нечего. */
  const fix = (href) =>
    prefix &&
    typeof href === 'string' &&
    href.startsWith('/') &&
    !href.startsWith('//') &&
    href !== prefix &&
    !href.startsWith(`${prefix}/`)
      ? prefix + href
      : undefined;

  const visitJsx = {
    filter: ['LinkCard', 'LinkButton', 'a'],
    visit(node, ctx) {
      const attr = node.attributes?.find((a) => a.type === 'mdxJsxAttribute' && a.name === 'href');
      const href = fix(attr?.value);
      if (href) ctx.setProperty(node, 'href', href);
    },
  };

  return {
    name: 'base-links',
    element: {
      filter: ['a'],
      visit(node, ctx) {
        const href = fix(node.properties?.href);
        if (href) ctx.setProperty(node, 'href', href);
      },
    },
    mdxJsxFlowElement: visitJsx,
    mdxJsxTextElement: visitJsx,
  };
}
