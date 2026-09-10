\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{tex2sto-ssau}[2026/09/09 tex2sto SSAU v1]
\LoadClass[14pt,a4paper]{extarticle}
\RequirePackage[a4paper,left=30mm,right=15mm,top=20mm,bottom=20mm]{geometry}
\RequirePackage{fontspec}
\RequirePackage{polyglossia}
\setdefaultlanguage{russian}
\setotherlanguage{english}
\setmainfont{Times New Roman}
\setsansfont{Times New Roman}
\setmonofont{Times New Roman}
\RequirePackage{setspace}
\onehalfspacing
\setlength{\parindent}{12.5mm}
\setlength{\parskip}{0pt}
\RequirePackage{graphicx}
\RequirePackage{amsmath}
\RequirePackage{longtable}
\RequirePackage{booktabs}
\RequirePackage{caption}
\RequirePackage{listings}
\RequirePackage[hidelinks]{hyperref}
\captionsetup{font=normalsize,labelformat=empty,labelsep=none}
\lstset{basicstyle=\fontsize{12}{14}\selectfont,breaklines=true,frame=single}
\makeatletter
\renewcommand\section{\@startsection{section}{1}{\z@}{-3.5ex \@plus -1ex \@minus -.2ex}{2.3ex \@plus.2ex}{\normalfont\fontsize{14}{17}\bfseries}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}{-3.25ex\@plus -1ex \@minus -.2ex}{1.5ex \@plus .2ex}{\normalfont\fontsize{14}{17}\bfseries}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}{-3.25ex\@plus -1ex \@minus -.2ex}{1.5ex \@plus .2ex}{\normalfont\fontsize{14}{17}\itshape}}
\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname\quad}
\makeatother
\newcommand{\texstructural}[1]{\begin{center}\bfseries #1\end{center}}
\newcommand{\texappendix}[2]{\texstructural{ПРИЛОЖЕНИЕ #1}\begin{center}#2\end{center}}
\newcommand{\texinstitute}[1]{\def\texStoredInstitute{#1}}
\newcommand{\texdepartment}[1]{\def\texStoredDepartment{#1}}
\newcommand{\textitle}[1]{\def\texStoredTitle{#1}}
\newcommand{\texprogramcode}[1]{\def\texStoredProgramCode{#1}}
\newcommand{\texprogramname}[1]{\def\texStoredProgramName{#1}}
\newcommand{\texstudyprofile}[1]{\def\texStoredStudyProfile{#1}}
\newcommand{\texauthor}[1]{\def\texStoredAuthor{#1}}
\newcommand{\texstudentgroup}[1]{\def\texStoredStudentGroup{#1}}
\newcommand{\texsupervisordetails}[1]{\def\texStoredSupervisorDetails{#1}}
\newcommand{\texsupervisor}[1]{\def\texStoredSupervisor{#1}}
\newcommand{\texcity}[1]{\def\texStoredCity{#1}}
\newcommand{\texyear}[1]{\def\texStoredYear{#1}}
\newcommand{\textitlepage}{%
  \thispagestyle{empty}\begin{center}
  МИНОБРНАУКИ РОССИИ\\
  Федеральное государственное автономное образовательное учреждение\\
  высшего образования\\
  «Самарский национальный исследовательский университет\\
  имени академика С. П. Королева»\\[1em]
  \texStoredInstitute\\\texStoredDepartment\\[4em]
  {\bfseries ВЫПУСКНАЯ КВАЛИФИКАЦИОННАЯ РАБОТА\\[2em]\texStoredTitle\par}
  \vfill
  \begin{flushleft}Направление \texStoredProgramCode\ \texStoredProgramName\\Профиль «\texStoredStudyProfile»\end{flushleft}
  \begin{flushright}Обучающийся: \texStoredAuthor, группа \texStoredStudentGroup\\Руководитель: \texStoredSupervisorDetails\ \texStoredSupervisor\end{flushright}
  \vfill \texStoredCity\ \texStoredYear
  \end{center}\clearpage}
\newcommand{\texassignment}[5]{%
  \texstructural{ЗАДАНИЕ}
  Утверждающий: #1\par Цель работы: #2\par
  Вопросы, подлежащие разработке: #3\par
  Дата выдачи: #4\par Срок представления: #5\clearpage}
\newcommand{\texassignmentcontinuation}{\texstructural{ЗАДАНИЕ (ПРОДОЛЖЕНИЕ)}\vfill\clearpage}
\newcommand{\texabstract}[6]{%
  \texstructural{РЕФЕРАТ}
  Работа: \pageref{LastPage} с., #1 рис., #2 табл., #3 источник(ов), #4 прил.\par
  \noindent #5\par #6\clearpage}
\makeatletter
\renewcommand{\tableofcontents}{\texstructural{СОДЕРЖАНИЕ}\@starttoc{toc}}
\makeatother
\AtBeginDocument{\fontsize{14}{21}\selectfont}
