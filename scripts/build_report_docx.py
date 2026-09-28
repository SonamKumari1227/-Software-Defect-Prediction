#!/usr/bin/env python
"""Build the Minor Project report in the departmental template format.

The departmental template ``A PROJECT REPORT.docx`` supplies the page setup,
the university header banner and the page-number footer; this script replaces
its body with the content of the Software Defect Prediction project.

Usage
-----
    python scripts/build_report_docx.py
    python scripts/build_report_docx.py --template "../A PROJECT REPORT.docx"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
import pandas as pd
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from docx_builder import ReportBuilder
from sdp.utils import PROJECT_ROOT

FIG = PROJECT_ROOT / "report" / "figures"
RESULTS = PROJECT_ROOT / "results"

# --------------------------------------------------------------------------- #
# Details of the candidate, the guide and the department.
# --------------------------------------------------------------------------- #
STUDENT = "SONAM KUMARI"
REG_NO = "NSU253121001"
ROLL_NO = "253121001"
GUIDE = "Ritesh Kumar Jha"
GUIDE_DESIG = "Assistant Professor (CS & IT)"
HOD = "Lal Kishore Kumar"
UNIVERSITY = "NETAJI SUBHAS UNIVERSITY"
PLACE = "Jamshedpur"
SESSION = "2025 - 2026"
MONTH_YEAR = "SEPTEMBER 2026"
TITLE = "SOFTWARE DEFECT PREDICTION USING MACHINE LEARNING"

DISPLAY = {
    "gradient_boosting": "Gradient Boosting", "random_forest": "Random Forest",
    "svm": "SVM (RBF)", "knn": "k-Nearest Neighbours", "logistic_regression": "Logistic Regression",
    "mlp": "MLP (Neural Network)", "naive_bayes": "Gaussian Naive Bayes", "decision_tree": "Decision Tree",
}


def metrics_rows(dataset: str, cols=("accuracy", "precision", "recall", "f1", "roc_auc", "mcc", "pf")):
    """Read the generated metrics CSV so the report can never drift from the code."""
    df = pd.read_csv(RESULTS / dataset / "test_metrics.csv").sort_values("f1", ascending=False)
    return [[DISPLAY.get(r.model, r.model)] + [f"{getattr(r, c):.3f}" for c in cols]
            for r in df.itertuples()]


def cv_rows(dataset: str):
    df = pd.read_csv(RESULTS / dataset / "test_metrics.csv").sort_values("cv_f1_mean", ascending=False)
    out = []
    for r in df.itertuples():
        out.append([DISPLAY.get(r.model, r.model)] +
                   [f"{getattr(r, f'cv_{m}_mean'):.3f} ± {getattr(r, f'cv_{m}_std'):.3f}"
                    for m in ("accuracy", "precision", "recall", "f1", "roc_auc")])
    return out


def source(rel: str, start: int = 0, end: int | None = None) -> str:
    lines = (PROJECT_ROOT / rel).read_text(encoding="utf-8").split("\n")
    return "\n".join(lines[start:end])


# =========================================================================== #
# FRONT MATTER
# =========================================================================== #
def front_matter(b: ReportBuilder, minimal: bool = True) -> None:
    """Title page and certificate.

    When *minimal* is true the Declaration, Acknowledgement and Abstract pages are
    omitted, which is the arrangement used by the departmental template.
    """
    C = WD_ALIGN_PARAGRAPH.CENTER

    # ---------------- title page ----------------
    b.blank(2)
    b._para("A PROJECT REPORT", size=Pt(16), align=C, space_after=Pt(2))
    b._para("ON", size=Pt(16), align=C, space_after=Pt(2))
    b._para(f"“{TITLE}”", size=Pt(16), bold=True, align=C, space_after=Pt(18))
    b._para("Submitted in Partial Fulfillment for the degree", size=Pt(14), align=C, space_after=Pt(2))
    b._para("of M.Tech. (Master of Technology)", size=Pt(14), align=C, space_after=Pt(2))
    b._para("in Computer Science and Engineering", size=Pt(14), align=C, space_after=Pt(16))
    b._para("Course Code: CS16095  |  Minor Project", size=Pt(14), align=C, space_after=Pt(24))

    b._para("Submitted By: -", size=Pt(16), bold=True, align=C, space_after=Pt(6))
    b._para(STUDENT.title(), size=Pt(14), align=C, space_after=Pt(2))
    b._para(f"Registration No.: {REG_NO}", size=Pt(14), align=C, space_after=Pt(2))
    b._para(f"Roll No.: {ROLL_NO}", size=Pt(14), align=C, space_after=Pt(2))
    b._para(f"M.Tech. (CSE), 2nd Semester, Session {SESSION}", size=Pt(14), align=C, space_after=Pt(22))

    b._para("Under the Guidance of", size=Pt(14), align=C, space_after=Pt(4))
    b._para(GUIDE, size=Pt(14), bold=True, align=C, space_after=Pt(2))
    b._para(f"{GUIDE_DESIG}, Department of Computer Science & Engineering", size=Pt(14),
            align=C, space_after=Pt(24))

    b._para("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", size=Pt(14), bold=True, align=C, space_after=Pt(2))
    b._para(UNIVERSITY, size=Pt(14), bold=True, align=C, space_after=Pt(2))
    b._para(f"{PLACE.upper()}, JHARKHAND", size=Pt(14), bold=True, align=C, space_after=Pt(12))
    b._para(MONTH_YEAR, size=Pt(14), bold=True, align=C, space_after=Pt(2))

    # ---------------- certificate ----------------
    b.chapter("CERTIFICATE")
    b.blank(1)
    b.p(f"This is to certify that the project report entitled “{TITLE}” submitted to "
        f"{UNIVERSITY.title()}, {PLACE}, in partial fulfillment of the requirement for the award of the "
        f"degree of Master of Technology (M.Tech.) in Computer Science and Engineering, is an original "
        f"work carried out by {STUDENT.title()}, Registration No. {REG_NO}, Roll No. {ROLL_NO}, under my "
        f"supervision and guidance during the academic session {SESSION}.")
    b.p("The work embodied in this report has not been submitted, either in part or in full, to any "
        "other university or institution for the award of any degree or diploma. The results reported "
        "were obtained by executing the software developed as part of this project, which is submitted "
        "along with this report.")
    b.blank(3)

    # Signature block as a borderless two-column table so that the names and
    # their captions stay aligned whatever their length.
    sig = b.doc.add_table(rows=4, cols=2)
    sig.autofit = False
    for row, (left, right, bold) in enumerate((
            ("Signature", "Signature", False),
            ("", "", False),
            (GUIDE, HOD, True),
            ("(Project Guide)", "(Head of Department)", False))):
        for col, text in ((0, left), (1, right)):
            cell = sig.rows[row].cells[col]
            cell.width = Inches(3.1)
            para = cell.paragraphs[0]
            para.paragraph_format.space_after = Pt(2)
            if text:
                run = para.add_run(text)
                run.font.name = "Calibri"; run.font.size = Pt(14); run.bold = bold
    b._para(space_after=Pt(24))

    b._para("(External Examiner)", size=Pt(14), align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=Pt(18))
    b._para(f"Date: ______________                              Place: {PLACE}", size=Pt(14))

    if minimal:
        return

    # ---------------- declaration ----------------
    b.chapter("DECLARATION")
    b.p(f"I, {STUDENT.title()}, Registration No. {REG_NO}, Roll No. {ROLL_NO}, a student of M.Tech. "
        f"(Computer Science and Engineering), 2nd Semester, hereby declare that the project report "
        f"entitled “{TITLE}” is an original work carried out by me under the guidance of "
        f"{GUIDE}, Department of Computer Science & Engineering, {UNIVERSITY.title()}, {PLACE}.")
    b.p("I further declare that:")
    b.bullets([
        "This work has not been submitted, in part or in full, for the award of any other degree or "
        "diploma of this or any other university.",
        "All sources of information, data, figures and ideas taken from other works have been duly "
        "acknowledged and cited in the Bibliography.",
        "The datasets used are publicly available benchmark datasets and have been credited to their "
        "originators.",
        "All results reported in this document were produced by executing the source code submitted "
        "with this report and can be reproduced by re-running it.",
        "I have followed the academic integrity and anti-plagiarism policy of the University.",
    ])
    b.blank(4)
    b._para(STUDENT.title(), size=Pt(14), bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=Pt(2))
    b._para(f"Registration No.: {REG_NO}", size=Pt(14), align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=Pt(2))
    b._para("Signature: ____________________", size=Pt(14), align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=Pt(2))
    b._para(f"Date: ______________", size=Pt(14), align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=Pt(2))
    b._para(f"Place: {PLACE}", size=Pt(14), align=WD_ALIGN_PARAGRAPH.RIGHT)

    # ---------------- acknowledgement ----------------
    b.chapter("ACKNOWLEDGEMENT")
    b.p(f"I take this opportunity to express my sincere gratitude to my project guide, {GUIDE}, "
        f"{GUIDE_DESIG}, Department of Computer Science & Engineering, {UNIVERSITY.title()}, for the "
        f"continuous support, valuable suggestions and constructive criticism offered throughout the "
        f"course of this project. The regular discussions on experimental design, on the correct "
        f"handling of training and test data, and on the interpretation of evaluation metrics were "
        f"instrumental in shaping this work.")
    b.p(f"I am deeply grateful to {HOD}, Head of the Department of Computer Science & Engineering, for "
        f"providing the laboratory facilities and an academic environment that encouraged independent "
        f"investigation.")
    b.p("I also wish to thank the faculty members of the department, in particular those who taught "
        "Advanced Software Engineering and Soft Computing Techniques. The treatment of software quality "
        "assurance, software reliability modelling and supervised learning in those courses provided the "
        "conceptual foundation on which this project is built.")
    b.p("I gratefully acknowledge the National Aeronautics and Space Administration (NASA) Metrics Data "
        "Program and the maintainers of the PROMISE Software Engineering Repository for placing the "
        "defect datasets in the public domain, and Professor Martin Shepperd and colleagues for "
        "publishing the cleaned versions of those datasets that made a methodologically sound study "
        "possible. I also thank the developers of the open-source scientific Python ecosystem, "
        "particularly scikit-learn, imbalanced-learn, pandas and matplotlib.")
    b.p("Finally, I thank my family and friends for their constant encouragement and patience during "
        "the preparation of this work.")
    b.blank(3)
    b._para(STUDENT.title(), size=Pt(14), bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=Pt(2))
    b._para(f"Registration No.: {REG_NO}", size=Pt(14), align=WD_ALIGN_PARAGRAPH.RIGHT)

    # ---------------- abstract ----------------
    b.chapter("ABSTRACT")
    b.p("Software defects that escape into later phases of the development life cycle are expensive to "
        "correct and can compromise the reliability of the delivered system. Software Defect Prediction "
        "is the practice of identifying defect-prone modules before testing begins, so that the limited "
        "quality-assurance budget of a project can be directed at the code most likely to fail. This "
        "project surveys the machine-learning literature on defect prediction and reproduces, under a "
        "methodologically sound protocol, the standard classifier-comparison study on the benchmark "
        "datasets of the NASA Metrics Data Program.")
    b.p("Four datasets - KC1, JM1, PC1 and CM1 - were used in the cleaned form published by Shepperd, "
        "Song, Sun and Mair, in which duplicated, inconsistent and implausible records present in the "
        "original files have been removed. Each record describes one software module through 21 to 37 "
        "static code metrics drawn from the McCabe, Halstead and lines-of-code families, together with "
        "a binary label indicating whether a defect was reported against the module. A complete "
        "processing pipeline was implemented in Python. It removes duplicate rows and constant columns, "
        "imputes missing values with the training-fold median, applies a logarithmic transformation to "
        "compensate for the strong right skew of every metric, standardises the features, and balances "
        "the classes with the Synthetic Minority Over-sampling Technique. Every learned transformation "
        "is encapsulated inside a cross-validated pipeline so that no information from the test data can "
        "influence training, a form of leakage that is common in the published literature.")
    b.p("Eight classifiers spanning the principal model families - Logistic Regression, Decision Tree, "
        "Random Forest, Gradient Boosting, Support Vector Machine, k-Nearest Neighbours, Gaussian Naive "
        "Bayes and a Multi-Layer Perceptron - were compared using stratified five-fold cross-validation "
        "on the training partition and an independent stratified hold-out test set. Seven complementary "
        "measures were recorded: Accuracy, Precision, Recall, F1-score, Receiver Operating "
        "Characteristic Area Under the Curve, Matthews Correlation Coefficient and Probability of False "
        "Alarm.")
    b.p("Gradient Boosting achieved the highest F1-score on three of the four datasets, with F1 = 0.509 "
        "and ROC-AUC = 0.733 on KC1, ROC-AUC = 0.858 on PC1 and ROC-AUC = 0.795 on CM1, and obtained the "
        "best mean rank overall. Random Forest was strongest on JM1, the largest dataset, with F1 = "
        "0.461 and ROC-AUC = 0.717. An ablation study established that class balancing is decisive: "
        "without over-sampling, Logistic Regression and the Support Vector Machine reached a precision "
        "of 1.000 on KC1 but a recall of only 0.153, detecting nine of fifty-nine defective modules, "
        "whereas with over-sampling recall rose to 0.678 and the F1-score almost doubled. Analysis of "
        "the metrics showed Halstead difficulty, the counts of distinct operators and operands and the "
        "number of executable lines to be the most informative attributes, although no single metric "
        "correlates with the defect label more strongly than 0.303. Learning curves revealed a "
        "persistent gap between training and validation performance, indicating that the limiting factor "
        "is the information content of static metrics rather than the quantity of training data.")
    b.p("The results are consistent with the published literature and confirm that ensemble methods "
        "combined with explicit treatment of class imbalance provide a practical and reproducible "
        "baseline for software defect prediction. The complete system, comprising an installable Python "
        "package, four command-line tools, a configuration-driven experiment design and an automated "
        "test suite, is submitted with this report.")
    b.blank(1)
    b._para("Keywords: software defect prediction, static code metrics, machine learning, class "
            "imbalance, SMOTE, NASA Metrics Data Program, ensemble learning, software quality assurance, "
            "empirical software engineering.", size=Pt(14), italic=True,
            align=WD_ALIGN_PARAGRAPH.JUSTIFY)


#: Front-matter rows, listed only when the full front matter is built.
FRONT_MATTER_ROWS = [
    ("", "Certificate", "CERTIFICATE"),
    ("", "Declaration", "DECLARATION"),
    ("", "Acknowledgement", "ACKNOWLEDGEMENT"),
    ("", "Abstract", "ABSTRACT"),
    ("", "List of Figures", "LIST OF FIGURES"),
    ("", "List of Tables", "LIST OF TABLES"),
    # "List of Abbreviations" is listed from CONTENTS_ROWS in both modes.
]

#: Rows dropped from the Contents when the figure/table lists are not built.
LIST_ROWS = {"List of Figures", "List of Tables"}

#: (serial number, title as printed, heading the page number points at)
CONTENTS_ROWS = [
    ("1.", "Introduction", "Introduction"),
    ("2.", "Abstraction", "Abstraction"),
    ("3.", "Objective", "Objective"),
    ("4.", "Literature Review", "Literature Review"),
    ("5.", "Existing System and Proposed System", "Existing System and Proposed System"),
    ("6.", "Modules", "Modules"),
    ("7.", "Technology", "Technology"),
    ("8.", "System Requirement", "System Requirement"),
    ("9.", "System Analysis", "System Analysis"),
    ("10.", "Methodology", "Methodology"),
    ("11.", "DFD", "DFD"),
    ("12.", "ER Diagram and Data Model", "ER Diagram and Data Model"),
    ("13.", "Testing", "Testing"),
    ("14.", "Screenshots", "Screenshots"),
    ("15.", "Results and Analysis", "Results and Analysis"),
    ("16.", "Coding", "Coding"),
    ("17.", "Dataset Tables", "Dataset Tables"),
    ("18.", "Conclusion", "Conclusion"),
    ("19.", "Future Scope", "Future Scope"),
    ("20.", "Limitation", "Limitation"),
    ("21.", "Bibliography", "Bibliography"),
    ("", "List of Abbreviations", "LIST OF ABBREVIATIONS"),
    ("", "Appendix A: Execution Instructions", "Appendix A: Execution Instructions"),
]


def _ref_table(b: ReportBuilder, headers: list[str], rows: list[tuple],
               widths: list[float], prefix: str, font_size: int = 14) -> None:
    """A three-column table whose last column is a PAGEREF field.

    Each row is (col1, col2, bookmark_target). Word fills in the page number
    when the document is opened.
    """
    t = b.doc.add_table(rows=1, cols=3)
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(h)
        run.bold = True; run.font.name = "Calibri"; run.font.size = Pt(font_size)
        b._shade(cell, "D9E2F3")

    for col1, col2, target in rows:
        cells = t.add_row().cells
        for i, val in enumerate((col1, col2)):
            cells[i].text = ""
            para = cells[i].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = para.add_run(val)
            run.font.name = "Calibri"; run.font.size = Pt(font_size)
        page = cells[2]
        page.text = ""
        para = page.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        b.pageref(para, b.slug(prefix, target), size=Pt(font_size))

    for r in t.rows:
        for i, w in enumerate(widths):
            r.cells[i].width = Inches(w)
    b._para(space_after=Pt(8))


def contents_page(b: ReportBuilder, minimal: bool = True,
                  figure_and_table_lists: bool = True) -> None:
    """Contents table.

    With *minimal* the table lists the numbered chapters only, beginning at
    Introduction, which is how the departmental template arranges it.
    """
    b.chapter("CONTENTS")
    rows = CONTENTS_ROWS if minimal else FRONT_MATTER_ROWS + CONTENTS_ROWS
    if not figure_and_table_lists:
        rows = [r for r in rows if r[1] not in LIST_ROWS]
    _ref_table(b, ["S.NO", "Chapter", "Page.no"], rows, [0.8, 4.4, 1.0], "_Ch_")
    b._para("Page numbers are generated automatically by Word. To refresh them, select the whole "
            "document with Ctrl+A and press F9.", size=Pt(11), italic=True)


def list_pages(b: ReportBuilder, figure_and_table_lists: bool = True) -> None:
    """The List of Figures and List of Tables pages.

    *figure_and_table_lists* may be turned off to match the departmental
    template, whose front matter is only a title page, a certificate and the
    contents. The List of Abbreviations is always produced, because the
    Contents refers to it.
    """
    if figure_and_table_lists:
        b.chapter("LIST OF FIGURES")
        _ref_table(b, ["Figure No.", "Title", "Page.no"],
                   [(num, cap, num) for num, cap in b.figures],
                   [0.95, 4.35, 0.9], "_Fig_", font_size=11)

        b.chapter("LIST OF TABLES")
        _ref_table(b, ["Table No.", "Title", "Page.no"],
                   [(num, cap, num) for num, cap in b.tables if num],
                   [0.95, 4.35, 0.9], "_Tab_", font_size=11)



def abbreviations_page(b: ReportBuilder) -> None:
    """The List of Abbreviations, placed after the Bibliography."""
    b.chapter("LIST OF ABBREVIATIONS")
    abbr = [
        ("ARFF", "Attribute-Relation File Format"), ("AUC", "Area Under the Curve"),
        ("CM1 / JM1 / KC1 / PC1", "Names of the NASA MDP project datasets"),
        ("CO", "Course Outcome"), ("CSV", "Comma-Separated Values"),
        ("CV", "Cross-Validation"), ("DFD", "Data-Flow Diagram"), ("DT", "Decision Tree"),
        ("EDA", "Exploratory Data Analysis"), ("ER", "Entity-Relationship"),
        ("FN / FP / TN / TP", "False Negative / False Positive / True Negative / True Positive"),
        ("GB", "Gradient Boosting"), ("IDE", "Integrated Development Environment"),
        ("JSON", "JavaScript Object Notation"), ("k-NN", "k-Nearest Neighbours"),
        ("LOC", "Lines of Code"), ("LR", "Logistic Regression"),
        ("MCC", "Matthews Correlation Coefficient"), ("MDP", "Metrics Data Program"),
        ("ML", "Machine Learning"), ("MLP", "Multi-Layer Perceptron"),
        ("NASA", "National Aeronautics and Space Administration"), ("NB", "Naive Bayes"),
        ("PD", "Probability of Detection (Recall)"), ("PF", "Probability of False Alarm"),
        ("PROMISE", "Predictor Models in Software Engineering repository"),
        ("RBF", "Radial Basis Function"), ("RF", "Random Forest"),
        ("ROC", "Receiver Operating Characteristic"), ("SDP", "Software Defect Prediction"),
        ("SMOTE", "Synthetic Minority Over-sampling Technique"),
        ("SVM", "Support Vector Machine"), ("UML", "Unified Modeling Language"),
        ("YAML", "YAML Ain't Markup Language"),
    ]
    b.table("", "", ["Abbreviation", "Expansion"], [[a, e] for a, e in abbr],
            col_widths=[1.9, 4.3], font_size=11)

# =========================================================================== #
# ASSEMBLY
# =========================================================================== #
def build_body(b: ReportBuilder, code_detail: str = "standard") -> None:
    """Run every chapter, in order, against the given builder."""
    import report_chapters_a as A
    import report_chapters_b as B

    A.ch1_introduction(b)
    A.ch2_abstraction(b)
    A.ch3_objective(b)
    A.ch4_literature(b)
    A.ch5_existing_proposed(b)
    A.ch6_modules(b)
    A.ch7_technology(b)
    A.ch8_requirements(b)
    A.ch9_system_analysis(b)
    A.ch10_methodology(b)
    A.ch11_dfd(b)
    B.ch12_er(b)
    B.ch13_testing(b)
    B.ch14_screenshots(b)
    B.ch15_results(b)
    B.ch16_coding(b, code_detail)
    B.ch17_dataset_tables(b)
    B.ch18_conclusion(b)
    B.ch19_future(b)
    B.ch20_limitation(b)
    B.ch21_bibliography(b)
    abbreviations_page(b)
    B.appendix(b)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", default=str(PROJECT_ROOT.parent / "A PROJECT REPORT.docx"),
                    help="Departmental template supplying page setup, header and footer")
    ap.add_argument("--code-detail", choices=["brief", "standard", "full"], default="standard",
                    help="How much source code Chapter 16 reproduces; the main dial on page count")
    ap.add_argument("--lists", choices=["all", "abbreviations-only"], default="all",
                    help="all (default): build List of Figures, List of Tables and List "
                         "of Abbreviations. abbreviations-only: omit the figure and table "
                         "lists, as in the departmental template.")
    ap.add_argument("--front-matter", choices=["minimal", "full"], default="minimal",
                    help="minimal (default): title page, certificate and the three list pages, "
                         "with the Contents beginning at Introduction, as in the departmental "
                         "template. full: also adds Declaration, Acknowledgement and Abstract pages.")
    ap.add_argument("--output", default=str(PROJECT_ROOT / "report" / "Minor_Project_Report.docx"))
    args = ap.parse_args()

    template = Path(args.template)
    if not template.exists():
        raise SystemExit(f"Template not found: {template}")

    # Pass 1 - collect the figure and table registers so that the two list
    # pages, which precede the chapters, can be printed complete.
    scout = ReportBuilder(template)
    build_body(scout, args.code_detail)
    figures, tables = list(scout.figures), list(scout.tables)

    # Pass 2 - the real document.
    b = ReportBuilder(template)
    minimal = args.front_matter == "minimal"
    all_lists = args.lists == "all"
    front_matter(b, minimal)
    contents_page(b, minimal, all_lists)
    b.figures, b.tables = list(figures), list(tables)
    list_pages(b, all_lists)
    build_body(b, args.code_detail)

    b.enable_field_update()   # Word resolves every PAGEREF when the file opens
    out = b.save(args.output)
    pages = b.estimate_pages()
    print(f"written  : {out}")
    print(f"figures  : {len(figures)}")
    print(f"tables   : {len([t for t in tables if t[0]])}")
    print(f"estimated: {pages:.0f} pages")


if __name__ == "__main__":
    main()
