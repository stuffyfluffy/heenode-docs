// Общие примитивы векторных диаграмм. Координаты — в сантиметрах от левого верхнего угла холста.
// Использование: #import "../_diagrams.typ": u, edge, arrow, node, note, stage, gate
#import "_template.typ": ink, muted, line-color

#let u = 1cm
#let edge = line-color.darken(20%)

// Стрелка из a в b
#let arrow(a, b, head: true) = {
  let (x1, y1) = a
  let (x2, y2) = b
  let ang = calc.atan2(x2 - x1, y2 - y1)
  let (c, s) = (calc.cos(ang), calc.sin(ang))
  let (len, half) = if head { (0.18, 0.07) } else { (0, 0) }
  let (bx, by) = (x2 - len * c, y2 - len * s)
  place(top + left, line(start: (x1 * u, y1 * u), end: (bx * u, by * u), stroke: 0.6pt + edge))
  if head {
    place(top + left, polygon(fill: edge,
      (x2 * u, y2 * u),
      ((bx - half * s) * u, (by + half * c) * u),
      ((bx + half * s) * u, (by - half * c) * u),
    ))
  }
}

// Блок с заголовком и подписью. current — выделенный, dashed — необязательный или внешний элемент
#let node(x, y, w, h, title, sub, current: false, dashed: false) = place(top + left, dx: x * u, dy: y * u, box(
  width: w * u,
  height: h * u,
  radius: 3pt,
  stroke: if current { 0.9pt + ink } else if dashed { (paint: edge, thickness: 0.5pt, dash: "dashed") } else { 0.5pt + edge },
  align(center + horizon, {
    set par(justify: false, leading: 0.45em)
    text(size: 9pt, weight: "bold", title)
    if sub != none {
      linebreak()
      text(size: 8pt, fill: muted, sub)
    }
  }),
))

// Мелкая подпись на холсте
#let note(x, y, w, body, pos: left) = place(top + left, dx: x * u, dy: y * u, box(width: w * u, {
  set par(justify: false, leading: 0.45em)
  align(pos, text(size: 8pt, fill: muted, body))
}))

// Этап вертикальной схемы
#let stage(title, desc, n: none, current: false, mark: none) = block(
  width: 100%,
  inset: (x: 10pt, y: 8pt),
  radius: 3pt,
  stroke: if current { 0.9pt + ink } else { 0.5pt + edge },
  breakable: false,
  {
    set align(left)
    set par(justify: false)
    grid(
      columns: (1fr, auto),
      row-gutter: 5pt,
      text(size: 10pt)[*#if n != none [#n. ]#title*], if mark != none { text(size: 8pt, fill: muted, mark) },
      grid.cell(colspan: 2, text(size: 9pt, fill: muted, desc)),
    )
  },
)

// Переход между этапами; с ромбом — условие (ворота)
#let gate(label, diamond: true) = box(width: 100%, height: 0.9 * u, {
  let x = 0.5
  arrow((x, 0), (x, 0.9))
  if diamond {
    place(top + left, dx: x * u - 4pt, dy: 0.45 * u - 4pt, polygon(fill: edge, (4pt, 0pt), (8pt, 4pt), (4pt, 8pt), (0pt, 4pt)))
  }
  place(left + horizon, dx: (x + 0.4) * u, text(size: 8pt, fill: muted, label))
})
