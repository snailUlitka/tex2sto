from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def valid_source() -> str:
    return r"""
\documentclass{tex2sto}
\title{Методы контроля}
\author{Иванов Иван Иванович}
\studentgroup{6401-010302D}
\institute{Институт информатики и кибернетики}
\department{Кафедра программных систем}
\programcode{09.03.01}
\programname{Информатика и вычислительная техника}
\studyprofile{Программное обеспечение средств вычислительной техники}
\supervisor{Петров П. П.}{доцент, к.т.н.}
\normcontroller{Кузнецова Н. Н.}
\year{2026}
\keywords{КОНТРОЛЬ; СИСТЕМА; МЕТОД; МОДЕЛЬ; РЕЗУЛЬТАТ}
\begin{abstract}
Рассмотрена система контроля. Описаны модель, метод и результаты исследования.
\end{abstract}
\source{doe2025}{book}{Иванов И. И.}{Методы контроля}{Самара: Издательство, 2025. 100 с.}
\begin{document}
\introduction
Введение описывает задачу.
\section{Основная часть}
Как показано на рисунке~\ref{fig:scheme}, результат подтверждает модель.
\begin{figure}
\centering
\includegraphics{scheme.png}
\caption{Схема контроля}
\label{fig:scheme}
\end{figure}
Уравнение~\ref{eq:model} задаёт модель.
\begin{equation}
x = y + 1
\label{eq:model}
\end{equation}
Источник~\cite{doe2025} описывает метод.
\conclusion
Получен результат.
\printbibliography
\end{document}
""".strip()


@pytest.fixture
def project_dir(tmp_path: Path, valid_source: str) -> Path:
    (tmp_path / "main.tex").write_text(valid_source, encoding="utf-8")
    (tmp_path / "scheme.png").write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000d49444154789c63606060f80f0001040100adf5d85b0000000049454e44ae426082"
        )
    )
    return tmp_path
