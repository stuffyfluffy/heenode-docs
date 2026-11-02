// Диаграммы документа «Казна и токеномика».
#import "../_template.typ": ink, muted, line-color
#import "../_diagrams.typ": u, edge, note

// Отрезок в координатах холста (см)
#let seg(a, b, stroke) = place(top + left, line(start: (a.at(0) * u, a.at(1) * u), end: (b.at(0) * u, b.at(1) * u), stroke: stroke))

// Регулятор наград: доля выплат в зависимости от запаса хода казны
#let runway-regulator = box(width: 16 * u, height: 5.9 * u, {
  let (x0, y0, w, h) = (1.4, 0.3, 11.4, 4.6)
  let max-m = 18
  let px(m) = x0 + m * w / max-m
  let py(p) = y0 + h - p / 100 * h
  let pt(m, p) = (px(m), py(p))

  // Зона аварийного режима
  place(top + left, dx: px(0) * u, dy: y0 * u, rect(width: (px(6) - px(0)) * u, height: h * u, fill: luma(244), stroke: none))
  note(px(0) + 0.1, y0 + 0.1, px(6) - px(0) - 0.2, [Аварийный режим: фикс. расходы −40%, исследования заморожены])

  // Сетка и оси
  for p in (20, 50, 100) {
    seg(pt(0, p), pt(max-m, p), (paint: line-color, thickness: 0.4pt, dash: "dotted"))
    note(0, py(p) - 0.17, x0 - 0.15, [#p%], pos: right)
  }
  seg(pt(0, 0), pt(max-m, 0), 0.6pt + edge)
  seg(pt(0, 0), pt(0, 105), 0.6pt + edge)
  for m in (0, 6, 12, 18) {
    seg(pt(m, 0), (px(m), py(0) + 0.12), 0.6pt + edge)
    note(px(m) - 0.5, py(0) + 0.2, 1, [#m], pos: center)
  }
  note(x0, py(0) + 0.6, w, [Запас хода казны, месяцев расходов], pos: center)

  // Рецензенты: не ниже 50%
  seg(pt(0, 50), pt(6, 50), (paint: ink, thickness: 1pt, dash: "dashed"))
  // Остальные награды: пропорционально запасу хода, не ниже 20%
  seg(pt(0, 20), pt(2.4, 20), 1.2pt + ink)
  seg(pt(2.4, 20), pt(12, 100), 1.2pt + ink)
  seg(pt(12, 100), pt(max-m, 100), 1.2pt + ink)

  // Легенда
  let lx = x0 + w + 0.4
  seg((lx, 1.0), (lx + 0.6, 1.0), 1.2pt + ink)
  note(lx + 0.75, 0.8, 1.9, [Награды ученикам и преподавателям])
  seg((lx, 2.4), (lx + 0.6, 2.4), (paint: ink, thickness: 1pt, dash: "dashed"))
  note(lx + 0.75, 2.2, 1.9, [Награды рецензентам (выше 6 мес. — как у всех)])
  note(lx, 3.7, 2.6, [От 12 месяцев — выплаты полностью])
})

// Доли платежа: кому сколько из каждого платного потока
#let split-row(y, label, parts) = {
  note(0, y + 0.2, 3.4, label)
  let x = 3.6
  let total = 12.4
  for (share, text-body, highlight) in parts {
    let w = total * share / 100
    place(top + left, dx: x * u, dy: y * u, box(
      width: w * u - 2pt,
      height: 0.8 * u,
      radius: 2pt,
      fill: if highlight { luma(232) } else { white },
      stroke: 0.5pt + edge,
      align(center + horizon, { set par(justify: false); text(size: 8pt, text-body) }),
    ))
    x += w
  }
}

#let payment-splits = box(width: 16 * u, height: 3.2 * u, {
  split-row(0, [Баунти], ((70, [70% — исполнителю], false), (30, [30% — казне], true)))
  split-row(1.2, [Платная когорта], ((60, [60% — ментору], false), (40, [40% — казне], true)))
  split-row(2.4, [Бронирование лаборатории], ((80, [80% — лаборатории], false), (20, [20% — казне], true)))
})
