// Общий шаблон нормативных документов Heenode DAO.
// Использование: #import "../_template.typ": doc
//                #show: doc.with(title: "…", version: "1.0", status: "active")

#let ink = rgb("#15171C")
#let muted = rgb("#565B66")
#let line-color = rgb("#DCDAD2")

#let doc(
  title: "",
  subtitle: none,
  kind: none,
  version: "",
  status: "active",
  body,
) = {
  set document(title: title, author: "Heenode DAO")
  set text(lang: "ru", font: ("Libertinus Serif", "New Computer Modern"), size: 11pt, fill: ink)
  set par(justify: true, leading: 0.72em, spacing: 1.1em)
  set page(
    paper: "a4",
    margin: (x: 2.4cm, top: 2.6cm, bottom: 2.4cm),
    header: {
      set text(font: "DejaVu Sans Mono", size: 7.5pt, fill: muted)
      grid(columns: (1fr, auto), [HEENODE DAO], [v#version])
      v(-4pt)
      line(length: 100%, stroke: 0.4pt + line-color)
    },
    footer: context {
      set text(font: "DejaVu Sans Mono", size: 7.5pt, fill: muted)
      align(center)[— #counter(page).display() —]
    },
    background: if status == "draft" {
      rotate(-35deg, text(size: 72pt, fill: luma(238), weight: "bold")[ЧЕРНОВИК])
    },
  )

  show heading.where(level: 1): it => {
    v(1.2em, weak: true)
    block(text(size: 13pt, weight: "bold", it.body))
    v(0.5em, weak: true)
  }
  show heading.where(level: 2): it => {
    v(0.9em, weak: true)
    block(text(size: 11pt, weight: "bold", it.body))
  }
  set enum(indent: 0.6em, numbering: "1.1.")
  set list(indent: 0.6em)
  set table(stroke: 0.4pt + line-color, inset: 6pt, align: left)
  show table: set par(justify: false)

  // Титул
  v(1.6cm)
  align(center)[
    #if kind != none [
      #text(font: "DejaVu Sans Mono", size: 8.5pt, fill: muted, tracking: 0.12em)[#upper(kind)]
      #v(0.4em)
    ]
    #text(size: 22pt, weight: "bold", tracking: 0.02em)[#title]
    #if subtitle != none [
      #v(0.2em)
      #text(size: 11.5pt, fill: muted)[#subtitle]
    ]
    #v(0.4em)
    #text(font: "DejaVu Sans Mono", size: 8.5pt, fill: muted)[Версия #version]
  ]
  v(1.2cm)
  body
}
