// Диаграммы Регламента лицензирования.
#import "../_template.typ": ink, muted, line-color
#import "../_diagrams.typ": u, edge, arrow, node, note

// Три пути, которыми компания может использовать материал DAO
#let usage-paths = box(width: 16 * u, height: 5.6 * u, {
  node(5.6, 0, 4.8, 1.3, [Материал DAO], [Курс, проект, данные — под копилефт-лицензией])

  node(0, 3.2, 4.8, 2.0, [Бесплатно по лицензии], [Компания делится доработками и связанным кодом на тех же условиях (CC BY-SA, AGPL)])
  node(5.6, 3.2, 4.8, 2.0, [Коммерческая лицензия], [Без условий копилефта; платёж — авторам, subDAO и сети], current: true)
  node(11.2, 3.2, 4.8, 2.0, [Работа людей], [Обучение, адаптация, интеграция, поддержка, хостинг, консультации])

  arrow((7.0, 1.3), (2.4, 3.2))
  arrow((8.0, 1.3), (8.0, 3.2))
  arrow((9.0, 1.3), (13.6, 3.2))

  note(0.6, 1.75, 3.6, [свои доработки открываются], pos: right)
  note(8.15, 2.0, 2.4, [платит за исключение])
  note(11.6, 1.75, 3.6, [платит за работу людей], pos: left)
})

// Доли дохода по видам поступлений
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

#let revenue-splits = box(width: 16 * u, height: 3.2 * u, {
  split-row(0, [Лицензия на материал subDAO], (
    (60, [[60]% — авторам по весу вклада], false),
    (25, [[25]% — subDAO], true),
    (15, [[15]% — сеть], true),
  ))
  split-row(1.2, [Лицензия на материал сети], (
    (60, [[60]% — авторам по весу вклада], false),
    (40, [[40]% — сеть], true),
  ))
  split-row(2.4, [Обучение, работы, хостинг], (
    (70, [70% — исполнителям], false),
    (30, [30% — казне], true),
  ))
})
