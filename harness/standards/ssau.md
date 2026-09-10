# SSAU STO Implementation Checklist

## Source and Authority

The normative source reviewed for this profile is STO 02068410-004-2018,
`General Requirements for Educational Text Documents`, September 2019 edition
with Amendment No. 1 and an effective date of 2019-11-09.

This file is a derived engineering checklist, not a reproduction or substitute
for the source standard. Clause references are retained so an implementation
or test can be checked against the normative document.

Use this precedence when evidence conflicts:

1. explicit user decisions for the project;
2. the source STO;
3. supplied teaching templates and accepted document examples.

The reviewed teaching DOCX is useful for Word mechanics but is not normative.
It demonstrates A4 page setup, correct margins, 14 pt Times New Roman defaults,
1.5 line spacing, custom styles, native OMML equations, and bottom-centered page
numbers. It also contains instructional color, direct formatting, comments,
and a non-master title page, so it must not be copied wholesale.

## Page and Body Text

Derived from clauses 3.1-3.4 and confirmed project choices:

- A4, portrait, one-sided layout;
- black Times New Roman;
- 14 pt body text;
- 12 pt table and code-listing text;
- no bold presentation supplied by ordinary authoring commands;
- 1.5 line spacing for body text;
- justified body paragraphs;
- 1.25 cm first-line indent;
- margins: 30 mm left, 15 mm right, 20 mm top, 20 mm bottom;
- every structural element starts on a new page;
- every numbered top-level section starts on a new page.

## Page Numbering

Derived from clauses 4.2.1-4.2.2:

- use continuous Arabic page numbering across the document and appendices;
- place the number at the bottom center without a trailing period;
- count the title page but do not display its page number.

## Structure and Headings

Derived from clauses 4.1.1-4.1.10:

- supported structural elements include title, optional assignment, abstract,
  contents, introduction, main sections, conclusion, optional definitions and
  abbreviations, optional references, and optional appendices;
- structural-element headings are unnumbered, centered, uppercase, not
  underlined, and have no trailing period;
- numbered sections, subsections, items, and subitems use Arabic hierarchical
  numbering without a trailing period;
- section and subsection titles start with an uppercase letter, have no trailing
  period, are not underlined, and must not hyphenate;
- items and subitems normally have numbers without titles;
- list levels use the STO-prescribed dash, selected lowercase Cyrillic letters,
  and Arabic numbers with closing parentheses.

The dialect should represent semantic levels and let the profile generate
punctuation and numbering. Authors must not type presentation prefixes by hand.

## Abstract

Derived from clauses 5.3.1-5.3.5:

- report page, figure, table, source, and appendix counts;
- report graphical-document sheet counts and formats when present;
- require 5-15 keywords or keyword phrases;
- render keywords uppercase, comma-separated, without word breaks or a final
  period;
- the recommended abstract text limit is 850 characters;
- object, goal, results, novelty, characteristics, application, and economic
  significance requirements are human-review content rules unless represented
  by explicit structured fields.

## Contents

Derived from clauses 5.4.1-5.4.2:

- include introduction, all named numbered levels, conclusion, optional
  definitions and abbreviations, references, and appendices with start pages;
- entries begin with an uppercase letter and otherwise use lowercase text;
- introduction, conclusion, references, and appendices are not numbered as
  sections;
- show an appendix entry as `Приложение А`, while the appendix page label is
  `ПРИЛОЖЕНИЕ А`.

The case distinction above is an explicit project decision informed by the
teaching template while retaining the uppercase structural heading required by
the STO.

## Figures

Derived from clauses 6.1.1-6.1.10:

- place a figure after its first mention, on the next page, or in an appendix;
- require at least one document reference to every figure;
- use global or section-local Arabic numbering according to the document's
  selected numbering policy;
- center explanatory text and the caption below the figure;
- format the caption as `Рисунок N — Название` without a trailing period;
- use single spacing for a multi-line caption and prevent word hyphenation;
- use appendix-local identifiers such as `Рисунок А.3`.

## Tables

Derived from clauses 6.2.1-6.2.14:

- place a table after its first mention or on the next page;
- require at least one document reference to every table;
- place `Таблица N — Название` above the table, left aligned, without a first-line
  indent or trailing period;
- use single spacing when the title spans multiple lines;
- use global or section-local numbering according to the selected policy;
- repeat the header or side heading when a table is divided;
- label later page parts `Продолжение таблицы N` without repeating the title or
  adding a trailing period;
- omit the closing bottom border on an interrupted first part where required;
- do not allow empty cells; use an appropriate dash when data is absent;
- use appendix-local identifiers such as `Таблица А.1`;
- keep a table note inside the table above its final boundary.

Word does not reevaluate fields in repeated table-header rows. The DOCX path
therefore splits a semantic `longtable` into separate editable tables at
explicit `\tablebreak` points, inserts a page break and `Продолжение таблицы N`
before every later part, and repeats the semantic header. Each part contains at
most 18 data rows so the source cannot silently defer an obviously oversized
segment to pagination. PDF removes the explicit hints and uses native
`longtable` continuation heads.

## Equations

Derived from clauses 6.3.1-6.3.5:

- place display equations on their own line with at least one free line above
  and below;
- follow the prescribed break points and repeat the operator at a continuation;
- use the multiplication sign rather than programming-language operators;
- explain symbols immediately below in source order, starting with `где`
  without a colon and including units where applicable;
- number referenced equations in parentheses at the right edge;
- use global or section-local numbering according to the selected policy;
- use appendix-local identifiers such as `(Б.2)`;
- keep DOCX equations editable through native OMML when supported by the tested
  Pandoc conversion path.

## References and Bibliography

Derived from clauses 5.9.1-5.9.2 and 6.4.1-6.4.3:

- order sources by first mention;
- number sources with Arabic numerals and no period after the number;
- render citations in square brackets;
- keep source records as structured tagged data inside the `.tex` project for
  v1;
- defer the complete field model until the additional bibliography STO is
  reviewed.

## Appendices and Listings

Derived from clauses 5.10.1-5.10.10 and confirmed project choices:

- place appendices after references and in first-reference order;
- require every appendix to be referenced from the main document;
- start each appendix on a new page;
- center `ПРИЛОЖЕНИЕ А` at the top and place a centered mixed-case title on a
  separate line without a trailing period;
- assign permitted uppercase Cyrillic letters and exclude the letters named by
  the STO;
- keep continuous document page numbering;
- include every appendix in the contents;
- prefix appendix sections, figures, tables, and equations with the appendix
  letter;
- support code listings primarily as appendix content and render them in 12 pt
  Times New Roman until a more specific requirement is established.

## Mechanical Prose Checks

Derived from clauses 7.2-7.13:

Potentially automatable checks include:

- forbidden arbitrary abbreviations;
- bare mathematical signs, `№`, and `%` in prose without numeric values;
- a minus sign before a negative prose value where the word `минус` is required;
- digits one through nine without a unit where words are required;
- decimal points where Russian decimal commas are required;
- separation of a numeric value from its unit by a breakable space;
- inconsistent units for the same represented parameter;
- non-decimal fractions where the permitted exception does not apply.

Use warnings when context can make the pattern legitimate. Use errors only when
the dialect or normalized document model proves the violation deterministically.
Do not add NLP-based terminology or writing-quality enforcement in v1.
