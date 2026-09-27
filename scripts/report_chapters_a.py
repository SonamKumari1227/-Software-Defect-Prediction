"""Chapters 1 to 11 of the Minor Project report."""

from __future__ import annotations

from docx.shared import Pt

from docx_builder import ReportBuilder
from sdp.utils import PROJECT_ROOT

FIG = PROJECT_ROOT / "report" / "figures"


# =========================================================================== #
def ch1_introduction(b: ReportBuilder) -> None:
    b.chapter("Introduction")

    b.h2("1.1  Background")
    b.p("Software has become the operating fabric of modern society. Aircraft avionics, medical "
        "instrumentation, banking settlement systems, telecommunication switches and the control "
        "software of spacecraft all depend on programs behaving exactly as intended. Despite five "
        "decades of advances in programming languages, development processes and verification tools, "
        "defects remain an unavoidable by-product of software construction. A defect is any flaw in a "
        "software artefact that can cause the system to behave in a way that differs from its "
        "specification, and in a system of even moderate size the number of such flaws introduced "
        "during development is measured in hundreds.")
    b.p("What makes defects economically significant is not merely their existence but the way the cost "
        "of removing them grows with time. Boehm's classical study of software engineering economics "
        "established that the cost of correcting a fault rises by roughly an order of magnitude with "
        "each successive phase in which it remains undetected, so that a requirements error found by a "
        "customer after release can cost a hundred times more to repair than the same error caught "
        "during a design review. Later industrial surveys have repeatedly confirmed the shape of this "
        "curve even as the absolute numbers have changed.")
    b.p("A second empirical regularity makes the problem tractable. Defects are not spread uniformly "
        "over a code base. Boehm and Basili, summarising a body of industrial measurement, observed "
        "that approximately eighty per cent of the defects in a system arise from approximately twenty "
        "per cent of its modules. If those modules could be identified in advance, the same testing "
        "budget would remove far more defects than if it were spread evenly across the system.")
    b.p("Testing and code inspection are the established means of finding defects, and both are "
        "expensive. Exhaustive testing of any realistic program is impossible, and manual inspection "
        "consumes senior engineering time, which is the scarcest resource on most projects. Quality "
        "assurance is therefore always an exercise in allocation: given a fixed budget, which parts of "
        "the system should be examined first? Software Defect Prediction addresses precisely this "
        "allocation problem.")
    b.p("A defect-prediction model takes measurable properties of a software module and estimates the "
        "likelihood that the module contains a defect. The properties most commonly used are static "
        "code metrics, which are computed directly from the source text without executing it. They "
        "include simple size measures such as the number of lines of code, structural measures such as "
        "McCabe's cyclomatic complexity, and the vocabulary-based measures proposed by Halstead. "
        "Because these metrics can be extracted automatically as soon as code is written, a model "
        "built on them can produce a risk ranking long before the first test case is executed.")
    b.p("The modern treatment of the problem as a supervised binary classification task was established "
        "by Menzies, Greenwald and Frank in 2007. Their study, together with the public release of the "
        "NASA Metrics Data Program datasets through the PROMISE repository, made defect prediction one "
        "of the most heavily studied problems in empirical software engineering. Several hundred papers "
        "have since compared classification algorithms, feature-selection strategies and resampling "
        "techniques on these datasets.")

    b.h2("1.2  Motivation")
    b.p("Three considerations motivated the choice of this topic for the Minor Project.")
    b.h3("1.2.1  Direct relevance to software engineering practice")
    b.p("Even a model of modest accuracy has practical value, because it is used to rank modules rather "
        "than to make an irreversible decision. A reviewer who inspects the twenty per cent of modules "
        "ranked most risky, and who finds a disproportionate share of the defects there, has obtained a "
        "real benefit even if the model's individual predictions are frequently wrong. The subject "
        "connects directly to the software quality assurance, software testing and software reliability "
        "modelling topics of the Advanced Software Engineering syllabus, and to the supervised learning "
        "and optimisation topics of Soft Computing Techniques.")
    b.h3("1.2.2  Documented methodological weaknesses in the published literature")
    b.p("A substantial part of the defect-prediction literature is difficult to trust. In 2013 "
        "Shepperd, Song, Sun and Mair audited the NASA datasets on which most of that literature rests "
        "and discovered that the distributed files contain a large number of exactly duplicated "
        "records, records that are identical in every metric but carry conflicting labels, and records "
        "with physically impossible values such as a module reported to have zero lines of code but a "
        "non-zero cyclomatic complexity. In the KC1 dataset, cleaning removes almost half of the rows. "
        "A second and independent weakness is that many studies fit scaling parameters, imputation "
        "statistics or resampling procedures on the complete dataset before separating training from "
        "test data. This allows information from the test set to influence the model and inflates the "
        "reported performance. Reproducing the standard methodology while avoiding both faults is "
        "therefore a worthwhile exercise in its own right, and it corresponds exactly to the stated "
        "outcome of this course, which is to analyse an existing solution and reproduce it.")
    b.h3("1.2.3  The class-imbalance problem")
    b.p("Defective modules are a minority in every dataset examined here, ranging from roughly eight "
        "per cent of modules in PC1 to roughly twenty-five per cent in KC1. Accuracy, the measure most "
        "frequently quoted in undergraduate treatments of classification, is actively misleading under "
        "such imbalance: on PC1 a model that predicts every module to be clean achieves ninety-two per "
        "cent accuracy while detecting nothing at all. A serious study must therefore treat imbalance "
        "explicitly and must report measures that are sensitive to performance on the minority class.")

    b.h2("1.3  Scope of the Project")
    b.p("This project is entirely software-based. No hardware was designed, fabricated or interfaced. "
        "The work delivered consists of the following elements.")
    b.bullets([
        "Automated acquisition of four public benchmark datasets from the NASA Metrics Data Program, "
        "with support for both the original and the cleaned versions of each file.",
        "Exploratory data analysis of the static code metrics, including distribution analysis, "
        "skewness measurement, inter-metric correlation and correlation with the defect label.",
        "A preprocessing pipeline comprising duplicate removal, constant-column removal, median "
        "imputation, logarithmic transformation and standardisation, constructed so that no learned "
        "quantity is ever estimated from test data.",
        "Explicit handling of class imbalance by synthetic minority over-sampling, with cost-sensitive "
        "learning and no balancing supported as alternatives for comparison.",
        "Implementation and comparison of eight supervised classification algorithms drawn from the "
        "linear, probabilistic, instance-based, kernel, single-tree, bagging, boosting and neural "
        "families.",
        "Evaluation by stratified five-fold cross-validation on the training partition and by a single "
        "measurement on an independent stratified hold-out test set, using seven complementary metrics.",
        "An ablation study quantifying the effect of class balancing, and supplementary analyses "
        "comprising learning curves and decision-threshold sensitivity.",
        "A reusable, configuration-driven and automatically tested Python package, together with "
        "command-line tools for data acquisition, exploratory analysis, model training and the scoring "
        "of previously unseen modules.",
    ])
    b.p("The following topics were considered and deliberately placed outside the scope of the present "
        "work, and are revisited in the chapter on future scope: cross-project defect prediction, in "
        "which a model trained on one project is applied to another; deep learning models that operate "
        "on the abstract syntax tree or token stream of the source code rather than on aggregate "
        "metrics; and process metrics such as code churn, developer count and ownership, which are "
        "derived from version-control history rather than from the code itself.")

    b.h2("1.4  Organisation of the Report")
    b.p("The remainder of this report is organised as follows. Chapter 2 presents a condensed "
        "abstraction of the problem and the approach. Chapter 3 states the objectives and the research "
        "questions. Chapter 4 reviews the relevant literature on code metrics, classification "
        "algorithms, data quality and class imbalance. Chapter 5 contrasts current industrial practice "
        "with the proposed system. Chapter 6 describes the software modules that were implemented and "
        "Chapter 7 the technologies used. Chapter 8 records the hardware and software requirements and "
        "Chapter 9 presents the system analysis. Chapter 10 sets out the methodology in detail. "
        "Chapters 11 and 12 give the data-flow and entity-relationship views of the system. Chapter 13 "
        "documents the testing strategy. Chapter 14 reproduces the output of the working system. "
        "Chapter 15, the principal chapter of the report, presents and analyses the experimental "
        "results. Chapter 16 lists the significant source code and Chapter 17 the structure of the "
        "datasets. Chapters 18, 19 and 20 give the conclusion, the future scope and the limitations of "
        "the work respectively, and Chapter 21 lists the references consulted.")


# =========================================================================== #
def ch2_abstraction(b: ReportBuilder) -> None:
    b.chapter("Abstraction")
    b.p("The problem addressed by this project can be stated abstractly as follows. Let a software "
        "system be decomposed into a finite set of modules, where a module is the smallest unit for "
        "which the measurement tools of the project produce a metric record; in the datasets used here "
        "a module corresponds to a function, procedure or method. Each module is characterised by a "
        "vector of d real-valued static code metrics, and is associated with a binary label that "
        "records whether at least one defect was subsequently reported against that module. The task is "
        "to learn, from a collection of labelled modules, a function that maps an unseen metric vector "
        "to a prediction of defect-proneness, and additionally to a continuous score that allows "
        "modules to be ranked by risk.")
    b.p("The abstraction deliberately discards a great deal of information. It ignores the identity of "
        "the programmer, the age of the code, the number of times it has been modified, the "
        "requirements it implements and the semantics of the operations it performs. What remains is a "
        "purely structural description: how large the module is, how many decision points it contains, "
        "how rich its vocabulary of operators and operands is, and how deeply nested its control flow "
        "becomes. The central empirical question of the field, and of this project, is how much of the "
        "variation in defect-proneness such a structural description can explain.")
    b.p("Three properties of the data make the learning problem harder than a textbook classification "
        "exercise. First, the classes are imbalanced: defective modules are a minority, and a learner "
        "that optimises overall error rate will be tempted to ignore them entirely. Second, the metrics "
        "are strongly right-skewed and highly collinear, because most of them are algebraic functions "
        "of the same underlying counts of operators and operands, so the effective dimensionality of "
        "the feature space is far lower than the nominal dimensionality. Third, the labels are noisy: "
        "a module marked as clean may simply be a module whose defects were never reported.")
    b.p("The solution developed in this project consists of four elements. A data-cleaning stage removes "
        "duplicated and degenerate records. A transformation stage compresses the skew of each metric "
        "and places all metrics on a common scale. A balancing stage synthesises additional minority "
        "examples so that the learner is not dominated by the majority class. A classification stage "
        "applies eight standard supervised algorithms and compares them under an evaluation protocol "
        "that measures performance on data the model has never seen and that reports measures sensitive "
        "to the minority class. Every stage that estimates a quantity from data is fitted strictly "
        "within the training portion of each split, so that the reported performance is an honest "
        "estimate of what the model would achieve on genuinely new modules.")
    b.p("The outcome of the study is not a single deployable model but a quantified comparison. It "
        "establishes which algorithms perform best on these data, how large the differences between "
        "them are relative to their variability, how much is gained by treating the imbalance "
        "explicitly, and where the ceiling on achievable performance appears to lie.")


# =========================================================================== #
def ch3_objective(b: ReportBuilder) -> None:
    b.chapter("Objective")

    b.h2("3.1  Problem Statement")
    b.p("Given a set of software modules, each described by a vector of static code metrics and "
        "labelled according to whether a defect was reported against it, construct and evaluate "
        "supervised classification models that predict the defect-proneness of unseen modules. "
        "Particular emphasis is to be placed on correct identification of the minority defective class, "
        "and the comparison between learning algorithms is to be carried out under a protocol that is "
        "free from information leakage and that is exactly reproducible.")

    b.h2("3.2  Objectives")
    b.p("The project pursues the following seven objectives. The first corresponds to the first course "
        "outcome of the Minor Project, which requires the identification of a research problem through "
        "a literature survey, and the fourth corresponds to the second course outcome, which requires "
        "that an existing solution be analysed and reproduced.")
    b.numbered([
        "To survey the literature on machine-learning-based software defect prediction, covering static "
        "code metrics, the benchmark datasets of the NASA Metrics Data Program, the treatment of class "
        "imbalance and accepted evaluation practice, and to identify the methodological weaknesses that "
        "recur in that literature.",
        "To acquire four cleaned benchmark datasets and to characterise them through exploratory data "
        "analysis, establishing their size, class balance, missing-value structure, metric "
        "distributions and inter-metric correlation.",
        "To design and implement a preprocessing pipeline that performs imputation, logarithmic "
        "transformation, standardisation and synthetic over-sampling, and that is structured so that "
        "every learned parameter is estimated only from training data.",
        "To reproduce the standard classifier-comparison methodology using eight supervised learning "
        "algorithms representative of the principal model families used in the field.",
        "To evaluate all models using stratified cross-validation and an independent hold-out set, "
        "reporting Accuracy, Precision, Recall, F1-score, ROC-AUC, Matthews Correlation Coefficient and "
        "Probability of False Alarm.",
        "To quantify, through a controlled ablation study, the effect of class balancing on each "
        "classifier, and to supplement this with learning-curve and decision-threshold analyses that "
        "explain the observed performance ceiling.",
        "To deliver a reusable, configurable and automatically tested software package that includes a "
        "prediction interface capable of scoring modules that were not part of any benchmark dataset.",
    ])

    b.h2("3.3  Research Questions")
    b.p("The experimental work is organised around three research questions, each of which is answered "
        "explicitly in Chapter 15.")
    b.bullets([
        "RQ1. Which static code metrics are most strongly associated with defect-proneness, and how "
        "strong is that association?",
        "RQ2. Which classification algorithm performs best on these datasets, and is the ranking "
        "consistent across datasets of differing size and class balance?",
        "RQ3. What is the effect of synthetic minority over-sampling on precision, recall, F1-score and "
        "the false-alarm rate, and does the effect differ between families of classifier?",
    ])

    b.h2("3.4  Expected Outcomes")
    b.p("At the conclusion of the work it was expected that a ranked comparison of the eight "
        "classifiers would be available for each of the four datasets, supported by cross-validated "
        "estimates of variability; that the contribution of class balancing would be quantified rather "
        "than assumed; that the most informative metrics would be identified; and that the entire "
        "experiment would be reproducible from a single command by any reader in possession of the "
        "submitted source code.")


# =========================================================================== #
def ch4_literature(b: ReportBuilder) -> None:
    b.chapter("Literature Review")
    b.p("This chapter reviews the body of work on which the project rests. It is organised into six "
        "themes: the static code metrics that constitute the feature space, the application of machine "
        "learning to defect prediction, the data-quality problems of the benchmark datasets, the "
        "treatment of class imbalance, accepted evaluation practice, and the research gap that this "
        "project addresses.")

    b.h2("4.1  Static Code Metrics")
    b.p("The measurement of program complexity begins with McCabe, who in 1976 proposed cyclomatic "
        "complexity as a quantitative basis for testing. Cyclomatic complexity counts the number of "
        "linearly independent paths through the control-flow graph of a program and is computed as "
        "v(G) = e - n + 2p, where e is the number of edges, n the number of nodes and p the number of "
        "connected components. Because every independent path requires at least one test case to "
        "exercise it, the measure simultaneously bounds the testing effort and indicates the number of "
        "opportunities the programmer had to make a control-flow mistake. Two derived measures appear "
        "in the NASA datasets: design complexity, which counts only those decision points that "
        "participate in calls to other modules, and essential complexity, which measures the degree to "
        "which the control-flow graph resists reduction and therefore quantifies unstructuredness.")
    b.p("A second family of measures was introduced by Halstead in 1977 under the name software "
        "science. Halstead observed that a program can be regarded as a sequence of tokens, each of "
        "which is either an operator or an operand, and defined all of his measures in terms of four "
        "counts: the number of distinct operators, the number of distinct operands, the total number of "
        "operator occurrences and the total number of operand occurrences. From these he derived "
        "program vocabulary, program length, volume, difficulty, level, effort, estimated programming "
        "time and an estimate of the number of delivered bugs. Although the psychological theory that "
        "Halstead advanced to justify these definitions has not withstood scrutiny, the measures "
        "themselves remain in wide use as descriptive statistics of program text, and they form the "
        "majority of the features in the datasets used here.")
    b.p("Alongside these, the simplest measures of all retain considerable predictive power. Counts of "
        "total lines, executable lines, comment lines and blank lines are trivially computed and "
        "correlate with almost every other structural measure. A recurring finding of the literature is "
        "that much of the apparent predictive power of sophisticated complexity measures is attributable "
        "to their correlation with module size.")

    b.h2("4.2  Machine Learning for Defect Prediction")
    b.p("Menzies, Greenwald and Frank published in 2007 the study that defined the modern form of the "
        "problem. Working on eight NASA datasets, they demonstrated that a Naive Bayes classifier "
        "applied to logarithmically transformed metrics achieved a mean probability of detection of "
        "approximately seventy-one per cent at a false-alarm rate of approximately twenty-five per "
        "cent. Their central argument was methodological: the choice of metrics matters less than the "
        "way the metrics are used, and simple learners applied with appropriate preprocessing "
        "outperform elaborate ones applied naively. The logarithmic transformation they recommended is "
        "adopted in the present project.")
    b.p("Lessmann, Baesens, Mues and Pietsch conducted in 2008 the most systematic benchmark of the "
        "period, comparing twenty-two classification algorithms across ten NASA datasets within a "
        "single experimental framework and applying statistical tests to the resulting rankings. Their "
        "conclusion was that, when performance is measured by area under the receiver operating "
        "characteristic curve, the great majority of classifiers are statistically indistinguishable "
        "from one another. Random Forest was among the strongest performers, but the differences "
        "between the top sixteen algorithms were not significant. The practical implication drawn by "
        "the authors was that practitioners should select an algorithm on grounds of interpretability "
        "and computational cost rather than expected accuracy.")
    b.p("Ghotra, McIntosh and Hassan revisited this conclusion in 2015 using the cleaned versions of "
        "the NASA data together with the PROMISE datasets collected by Jureczko. Applying a "
        "Scott-Knott effect-size difference test to the results of thirty-one classifiers, they found "
        "that classifier choice does matter once the data-quality defects are removed, and that the "
        "algorithms separate into statistically distinct groups. Ensemble methods and logistic model "
        "trees occupied the top group. This finding is directly relevant to the present work, which "
        "uses the cleaned data and observes exactly such a separation between ensembles and the single "
        "decision tree.")
    b.p("Hall, Beecham, Bowes, Gray and Counsell published in 2012 a systematic literature review "
        "covering two hundred and eight primary studies. Their principal findings were that models "
        "built with simple techniques such as Naive Bayes and Logistic Regression tend to perform well; "
        "that models combining metrics from several families outperform models restricted to a single "
        "family; that the way in which the study is designed and reported has more influence on the "
        "conclusions than the modelling technique; and that a substantial proportion of the published "
        "literature is methodologically too weak to contribute reliable evidence. Malhotra reached "
        "compatible conclusions in a 2015 review of sixty-four studies, and Wahono documented the "
        "dominance of the NASA datasets in a survey of research trends. Li, Jing and Zhu surveyed in "
        "2018 the newer directions of the field, including transfer learning for cross-project "
        "prediction and deep learning over source-code representations.")

    b.h2("4.3  Data Quality and the NASA Datasets")
    b.p("The paper that most directly shapes the design of this project is the 2013 data-quality audit "
        "by Shepperd, Song, Sun and Mair. The authors examined the thirteen NASA MDP datasets in "
        "circulation and catalogued five categories of defect in the data itself: identical cases, in "
        "which the same metric vector and label appear more than once; inconsistent cases, in which "
        "identical metric vectors carry contradictory labels; cases containing missing values; cases "
        "containing implausible values, such as a module with zero lines of code but a non-zero "
        "Halstead volume; and constant attributes carrying no information. They produced two cleaned "
        "collections, designated D-prime and D-double-prime, the latter additionally removing "
        "inconsistent cases.")
    b.p("The magnitude of the problem is considerable. In KC1 the original file contains 2,109 records, "
        "of which the cleaned D-double-prime version retains 1,162. Because duplicated records are "
        "distributed randomly between training and test partitions, an evaluation performed on the "
        "original data effectively tests the model on instances it has already memorised, and the "
        "reported performance is correspondingly optimistic. The authors demonstrated that published "
        "results differ materially between the original and cleaned versions and recommended that all "
        "future work use the cleaned data. This project follows that recommendation; the software "
        "retains the ability to load the original files so that the difference can be measured, and "
        "that measurement is reported in Chapter 15.")

    b.h2("4.4  Class Imbalance")
    b.p("Chawla, Bowyer, Hall and Kegelmeyer introduced the Synthetic Minority Over-sampling Technique "
        "in 2002. Rather than duplicating minority instances, which causes a classifier to overfit the "
        "exact repeated points, SMOTE creates new instances by interpolation: for each minority "
        "instance one of its k nearest minority neighbours is selected at random, and a synthetic point "
        "is placed at a random position on the line segment joining the two. The effect is to widen the "
        "region of feature space that the classifier associates with the minority class, which "
        "generally increases recall at some cost in precision.")
    b.p("Tantithamthavorn, Hassan and Matsumoto evaluated in 2020 the effect of rebalancing techniques "
        "on one hundred and one defect datasets. They reported that over-sampling substantially "
        "improves recall and AUC-type measures for most classifiers, that it degrades precision, and "
        "that the improvement in recall is generally worth the loss in precision when the cost of a "
        "missed defect exceeds the cost of an unnecessary inspection. They also issued a warning that "
        "is central to the design of the present system: rebalancing must be applied only to the "
        "training data. Applying SMOTE before splitting places synthetic points derived from test "
        "instances into the training set and produces meaningless results. Cost-sensitive learning, in "
        "which the loss function assigns a higher penalty to errors on the minority class, is an "
        "alternative that avoids synthesising data at all, and is implemented in this project as a "
        "configurable option.")

    b.h2("4.5  Evaluation Practice")
    b.p("There is broad agreement in the literature that accuracy is an inappropriate measure for this "
        "problem. Under the class distribution of PC1, a constant predictor that declares every module "
        "clean attains an accuracy of approximately ninety-two per cent while providing no information "
        "whatever. The measures customarily reported in place of accuracy are recall, also called the "
        "probability of detection; the probability of false alarm, which is the proportion of clean "
        "modules incorrectly flagged; the F1-score, which is the harmonic mean of precision and recall; "
        "and the area under the receiver operating characteristic curve, which is threshold-independent "
        "and insensitive to class prevalence.")
    b.p("Chicco and Jurman argued in 2020 that the Matthews Correlation Coefficient is more informative "
        "than either accuracy or the F1-score on imbalanced binary problems, because it is the only "
        "commonly used single-figure measure that incorporates all four cells of the confusion matrix "
        "and is therefore high only when the classifier performs well on both classes. This project "
        "reports the coefficient alongside the conventional measures. On the question of validation "
        "design, stratified k-fold cross-validation is the accepted standard, with repetition over "
        "several random seeds recommended where computational budget allows.")

    b.h2("4.6  Research Gap and Positioning of this Work")
    b.p("The field is mature, and this project does not claim to introduce a new algorithm. What the "
        "literature survey identifies is a persistent gap between accepted methodological advice and "
        "common practice. Three faults recur: the use of the original rather than the cleaned NASA "
        "files; the application of preprocessing or resampling before the training and test partitions "
        "are separated; and the reporting of accuracy as the headline measure. Each of these faults "
        "inflates the apparent performance of the resulting model, and a study that commits all three "
        "can report figures that are entirely unattainable in practice.")
    b.p("The contribution of this project is therefore a careful reproduction. It uses the cleaned "
        "datasets; it encapsulates every learned transformation, including the over-sampling step, "
        "inside a pipeline that is refitted within each cross-validation fold; and it reports seven "
        "measures of which accuracy is the least emphasised. The resulting figures are lower than many "
        "published on the original data, and the comparison of the two, reported in Chapter 15, is "
        "itself one of the findings of the work. Table 4.1 summarises the literature surveyed.")

    b.table("4.1", "Summary of the surveyed literature",
            ["Ref.", "Author (Year)", "Data used", "Method", "Principal finding"],
            [["[1]", "McCabe (1976)", "—", "Control-flow analysis",
              "Cyclomatic complexity bounds testing effort and indicates error-proneness"],
             ["[2]", "Halstead (1977)", "—", "Operator/operand counting",
              "Vocabulary-based measures estimate effort and delivered bugs"],
             ["[3]", "Menzies et al. (2007)", "8 NASA sets", "Naive Bayes, J48, OneR",
              "Log-transformed Naive Bayes attains PD 71 % at PF 25 %"],
             ["[4]", "Lessmann et al. (2008)", "10 NASA sets", "22 classifiers",
              "Most classifiers statistically indistinguishable on AUC"],
             ["[5]", "Hall et al. (2012)", "208 studies", "Systematic review",
              "Simple learners perform well; study design dominates technique"],
             ["[6]", "Shepperd et al. (2013)", "13 NASA sets", "Data-quality audit",
              "Extensive duplication and inconsistency; cleaned versions released"],
             ["[7]", "Ghotra et al. (2015)", "Cleaned NASA, PROMISE", "31 classifiers",
              "On clean data classifier choice matters; ensembles rank highest"],
             ["[8]", "Chawla et al. (2002)", "Various", "SMOTE",
              "Interpolated synthetic minority samples improve recall"],
             ["[9]", "Tantithamthavorn et al. (2020)", "101 datasets", "Rebalancing study",
              "Rebalancing raises recall and AUC; must be confined to training data"],
             ["[10]", "Chicco and Jurman (2020)", "Synthetic and real", "Metric analysis",
              "MCC is more reliable than accuracy or F1 under imbalance"],
             ["[11]", "Malhotra (2015)", "64 studies", "Systematic review",
              "Machine learning outperforms statistical models; NASA data dominate"],
             ["[13]", "Li, Jing and Zhu (2018)", "Survey", "Review of approaches",
              "Transfer learning and deep learning are the emerging directions"]],
            col_widths=[0.5, 1.35, 1.1, 1.1, 2.2], font_size=10)


# =========================================================================== #
def ch5_existing_proposed(b: ReportBuilder) -> None:
    b.chapter("Existing System and Proposed System")

    b.h2("5.1  The Existing System")
    b.p("In the majority of software organisations there is no computerised system that predicts which "
        "parts of a code base are likely to contain defects. Quality assurance is planned and executed "
        "using a combination of experience, convention and simple rules of thumb. The characteristic "
        "features of this existing practice are described below.")
    b.h3("5.1.1  Allocation of review effort by judgement")
    b.p("The selection of modules for inspection is normally made by a senior engineer or team lead on "
        "the basis of personal familiarity with the code. This works reasonably well in small and "
        "stable teams, but it scales poorly, it is not reproducible, it cannot be audited, and the "
        "knowledge on which it depends leaves the organisation when the individual does.")
    b.h3("5.1.2  Uniform or threshold-based application of testing")
    b.p("Where a systematic rule is used at all, it is usually a single threshold on a single metric, "
        "such as a requirement that every function whose cyclomatic complexity exceeds ten be "
        "inspected. Such rules are simple to apply but crude. They consider one metric in isolation, "
        "they cannot express interactions between metrics, and the threshold is generally inherited "
        "from published guidance rather than calibrated against the defect history of the project "
        "concerned.")
    b.h3("5.1.3  Reaction rather than prediction")
    b.p("Most defect data in industry is collected and analysed only after the defects have been found. "
        "Defect-density reports, escape analyses and root-cause reviews are valuable but retrospective; "
        "they describe where defects were, not where they are about to be discovered.")
    b.h3("5.1.4  Limitations of the existing system")
    b.bullets([
        "The allocation of review and testing effort is subjective and cannot be justified with "
        "evidence.",
        "Single-metric thresholds ignore the joint behaviour of the metrics and produce large numbers "
        "of both missed modules and unnecessary inspections.",
        "There is no quantitative estimate of risk attached to a module, so modules cannot be ranked.",
        "The historical defect data that the organisation already possesses is not exploited to inform "
        "future decisions.",
        "Because nothing is measured, the effectiveness of the allocation policy itself cannot be "
        "evaluated or improved.",
    ])

    b.h2("5.2  The Proposed System")
    b.p("The proposed system replaces judgement and single-metric thresholds with a supervised learning "
        "model trained on historical data. It accepts a table of static code metrics, one row per "
        "module, and returns for each module a probability of defect-proneness together with a binary "
        "classification obtained by applying a threshold to that probability. The modules can then be "
        "sorted by probability, and inspection effort applied from the top of the list downwards until "
        "the available budget is exhausted.")
    b.p("The system is designed around four principles. The first is honesty of evaluation: every "
        "quantity learned from data, including imputation medians, scaling parameters and synthetic "
        "over-sampled points, is computed only from training data, so the performance figures reported "
        "are achievable in practice. The second is reproducibility: a single random seed governs the "
        "data split, the cross-validation folds, the over-sampling and every stochastic learning "
        "algorithm, and all experimental settings are declared in one configuration file rather than "
        "being embedded in the code. The third is comparability: eight algorithms are trained and "
        "evaluated under identical conditions, with no algorithm receiving more tuning effort than "
        "another. The fourth is extensibility: adding a new classifier requires the registration of a "
        "single factory function and no change to the training loop.")
    b.h3("5.2.1  Advantages of the proposed system")
    b.bullets([
        "Risk is quantified on a continuous scale, so modules can be ranked and the inspection budget "
        "can be applied where it yields most.",
        "All available metrics are considered jointly, and interactions between them are captured by "
        "the non-linear models.",
        "The decision threshold can be moved to reflect the relative cost of a missed defect and an "
        "unnecessary inspection, which is a policy decision rather than a modelling one.",
        "The model is retrainable: as the project accumulates defect history, the model improves "
        "without any change to the software.",
        "The entire experiment is reproducible from one command, so results can be independently "
        "verified.",
        "The predictions are auditable, since feature-importance analysis shows which metrics drive "
        "the model's behaviour.",
    ])
    b.h3("5.2.2  Comparison")
    b.table("5.1", "Comparison between the existing practice and the proposed system",
            ["Aspect", "Existing practice", "Proposed system"],
            [["Basis of decision", "Individual experience and convention",
              "Model trained on historical defect data"],
             ["Metrics considered", "Usually one at a time, against a fixed threshold",
              "All 21 to 37 metrics jointly, with interactions"],
             ["Output", "A binary include or exclude decision", "A continuous risk probability and a ranking"],
             ["Cost sensitivity", "Not expressible", "Adjustable through the decision threshold"],
             ["Reproducibility", "Not reproducible", "Fully reproducible from a fixed seed"],
             ["Improvement over time", "Depends on staff retention", "Improves as defect history accumulates"],
             ["Evaluation", "Effectiveness is not measured",
              "Seven metrics on an independent hold-out set"]],
            col_widths=[1.4, 2.4, 2.4], font_size=11)


# =========================================================================== #
def ch6_modules(b: ReportBuilder) -> None:
    b.chapter("Modules")
    b.p("The system is implemented as an installable Python package named sdp, which contains eight "
        "modules, together with a set of five command-line scripts that orchestrate them and one test "
        "module. Each module has a single, clearly delimited responsibility, and the dependencies "
        "between them are acyclic. The modules are described below in the order in which they "
        "participate in a typical execution.")

    b.h2("6.1  Configuration Module")
    b.p("The configuration module reads the YAML file that declares every experimental setting, "
        "validates that the mandatory sections are present, and supplies defaults for optional keys so "
        "that the remainder of the code can rely on their existence. Centralising the settings in this "
        "way means that a change of dataset, balancing strategy, cross-validation design or model list "
        "requires no modification to any source file, which is important both for reproducibility and "
        "for the ablation studies reported in Chapter 15.")

    b.h2("6.2  Utilities Module")
    b.p("The utilities module provides the cross-cutting services used throughout the package: a "
        "console logger with a consistent timestamped format, a seeding function that fixes the state "
        "of every random number generator on which the system depends, path resolution that interprets "
        "the relative paths of the configuration file against the project root, and helpers for writing "
        "and reading JSON that correctly serialise NumPy numeric types.")

    b.h2("6.3  Data Loader Module")
    b.p("The data loader is responsible for obtaining the datasets and converting them into a uniform "
        "in-memory representation. It downloads the requested ARFF file from a public mirror of the "
        "PROMISE repository, caching it locally so that subsequent runs require no network access, and "
        "falls back to the OpenML service if the primary source is unavailable. It contains a compact "
        "parser for the Attribute-Relation File Format that extracts the attribute names from the "
        "header and reads the data section into a data frame, treating the question mark as a missing "
        "value. It then normalises the target column, which is necessary because the class attribute is "
        "named Defective in three of the four files and label in the fourth, and encodes it as an "
        "integer.")

    b.h2("6.4  Preprocessing Module")
    b.p("The preprocessing module contains both the frame-level cleaning operations and the "
        "construction of the learned transformation pipeline. Cleaning removes duplicated rows and "
        "columns of zero variance; neither operation estimates any parameter from the data, so both may "
        "safely be applied before the split. The module also performs the stratified division into "
        "training and test partitions, and builds the pipeline that chains median imputation, the "
        "logarithmic transformation, standardisation, optional synthetic over-sampling and the "
        "classifier itself into a single object.")

    b.h2("6.5  Models Module")
    b.p("The models module holds a registry that maps a short name to a factory function returning a "
        "configured estimator, together with a second registry of hyper-parameter search spaces used by "
        "the optional randomised search. Because every factory receives the random seed and the "
        "balancing mode, cost-sensitive class weighting can be applied uniformly to every algorithm "
        "that supports it. Adding a classifier to the study requires one entry in each registry and no "
        "other change.")

    b.h2("6.6  Evaluation Module")
    b.p("The evaluation module computes the seven performance measures from a vector of true labels and "
        "a vector of predictions, extracts a continuous score from any estimator irrespective of "
        "whether it exposes predicted probabilities or a decision function, runs stratified "
        "cross-validation over the training partition and assembles the per-model results into a sorted "
        "table.")

    b.h2("6.7  Visualization Module")
    b.p("The visualization module produces every figure that appears in this report, using a "
        "non-interactive rendering backend so that the system runs without a display. It generates the "
        "exploratory figures, the receiver operating characteristic and precision-recall curves, the "
        "confusion matrices, the model-comparison bar chart, the cross-validation box plot, the "
        "feature-importance chart and the cross-dataset heat maps.")

    b.h2("6.8  Exploratory Data Analysis Module")
    b.p("The exploratory analysis module drives the characterisation of a dataset. It writes a summary "
        "of the dataset dimensions, class balance and missing-value structure as JSON, a table of "
        "descriptive statistics including skewness and correlation with the target as CSV, and four "
        "figures.")

    b.h2("6.9  Command-Line Scripts")
    b.p("Five scripts provide the user interface to the package.")
    b.bullets([
        "download_data.py obtains the datasets named in the configuration file and reports the "
        "dimensions and class balance of each.",
        "run_eda.py performs the exploratory analysis for one dataset or for all of them.",
        "run_pipeline.py is the principal entry point. It executes the complete experiment: loading, "
        "cleaning, splitting, cross-validating, fitting, evaluating, plotting and persisting.",
        "predict.py loads a previously trained pipeline and scores a file of module metrics supplied by "
        "the user, appending a defect probability and a binary prediction.",
        "make_report_figures.py and make_extra_figures.py regenerate the diagrams and analyses "
        "reproduced in this report.",
    ])

    b.h2("6.10  Test Module")
    b.p("The test module contains the automated test suite described in Chapter 13. It exercises the "
        "parser, the target encoding, the cleaning operations, the stratification, the metric "
        "computations, the end-to-end training of every registered classifier under all three balancing "
        "modes, and the determinism of repeated runs.")

    b.table("6.1", "Summary of the implemented modules",
            ["Module", "Responsibility", "Lines"],
            [["sdp/config.py", "Load and validate the experiment configuration", "47"],
             ["sdp/utils.py", "Logging, seeding, path resolution, JSON persistence", "72"],
             ["sdp/data_loader.py", "Download, ARFF parsing, target normalisation", "153"],
             ["sdp/preprocessing.py", "Cleaning, splitting, transformation pipeline, SMOTE", "116"],
             ["sdp/models.py", "Classifier registry and hyper-parameter spaces", "107"],
             ["sdp/evaluate.py", "Metrics, cross-validation, hold-out evaluation", "114"],
             ["sdp/visualization.py", "All exploratory and evaluation figures", "193"],
             ["sdp/eda.py", "Exploratory data analysis driver", "65"],
             ["scripts/download_data.py", "Dataset acquisition command", "33"],
             ["scripts/run_eda.py", "Exploratory analysis command", "37"],
             ["scripts/run_pipeline.py", "Training and evaluation command", "188"],
             ["scripts/predict.py", "Scoring of previously unseen modules", "59"],
             ["tests/test_pipeline.py", "Automated test suite", "119"]],
            col_widths=[1.9, 3.5, 0.8], font_size=11)


# =========================================================================== #
def ch7_technology(b: ReportBuilder) -> None:
    b.chapter("Technology")
    b.p("This chapter describes the technologies on which the system is built and the reasons for "
        "which each was selected. All are open source and freely available, and the entire system runs "
        "on a standard personal computer without specialised hardware.")

    b.h2("7.1  Python")
    b.p("Python is a high-level, interpreted, dynamically typed general-purpose programming language "
        "created by Guido van Rossum and first released in 1991. It has become the dominant language "
        "for data analysis and machine learning, and it was chosen for this project for four reasons: "
        "the maturity and completeness of its scientific ecosystem; the readability of the resulting "
        "code, which matters in a report that must be understood by a reader who did not write it; the "
        "availability of the exact library implementations of the algorithms used in the reference "
        "literature; and its status as the language in which almost all published defect-prediction "
        "research is now conducted, which makes the work directly comparable. Version 3.13 was used for "
        "development; the code is compatible with version 3.9 and later.")

    b.h2("7.2  NumPy and pandas")
    b.p("NumPy provides the multidimensional array object and the vectorised numerical operations on "
        "which the whole scientific Python stack is founded. Operations expressed over whole arrays "
        "execute in compiled code rather than in the interpreter, which makes them one to two orders of "
        "magnitude faster than equivalent Python loops.")
    b.p("pandas builds on NumPy to provide the data frame, a two-dimensional labelled table with "
        "heterogeneous column types, together with facilities for reading and writing delimited files, "
        "handling missing data, grouping, joining and reshaping. In this project pandas is used to hold "
        "the parsed ARFF data, to compute the descriptive statistics of the exploratory analysis, and "
        "to assemble and export the result tables that appear in Chapter 15.")

    b.h2("7.3  scikit-learn")
    b.p("scikit-learn is the principal machine-learning library of the Python ecosystem. It supplies "
        "implementations of all eight classification algorithms used here, the preprocessing "
        "transformers, the cross-validation splitters, the metric functions and, most importantly for "
        "the design of this system, the Pipeline abstraction.")
    b.p("A pipeline chains a sequence of transformers and a final estimator into a single object that "
        "itself satisfies the estimator interface. When the pipeline is fitted, each transformer is "
        "fitted in turn on the output of its predecessor; when it is used to predict, the same fitted "
        "transformers are applied without refitting. This single abstraction is what guarantees the "
        "absence of information leakage in this project, because when a pipeline is passed to a "
        "cross-validation routine the transformers are refitted inside every fold using only that "
        "fold's training data. The library follows a uniform interface in which every estimator exposes "
        "fit, predict and, where meaningful, predict_proba, which is what allows the comparison loop in "
        "this project to treat eight very different algorithms identically.")

    b.h2("7.4  imbalanced-learn")
    b.p("imbalanced-learn extends scikit-learn with resampling algorithms for imbalanced data, "
        "including the implementation of SMOTE used here. Critically, it also provides a pipeline class "
        "that is aware of resampling: a resampler placed in such a pipeline is executed when the "
        "pipeline is fitted but is bypassed when it is used to predict. Without this behaviour it would "
        "be necessary to resample manually inside each cross-validation fold, which is the step that "
        "published studies most frequently omit.")

    b.h2("7.5  matplotlib and seaborn")
    b.p("matplotlib is the foundational plotting library for Python and produces all figures in this "
        "report. It is used with the Agg backend, which renders directly to an image file without "
        "requiring a graphical display, so that the analysis can be executed on a server or as part of "
        "an automated build. seaborn is a higher-level interface built on matplotlib that supplies the "
        "statistical plot types used in the exploratory analysis, in particular the box plots and the "
        "correlation heat maps, together with a consistent visual theme.")

    b.h2("7.6  Supporting Tools")
    b.bullets([
        "PyYAML parses the configuration file. YAML was preferred to JSON because it permits comments, "
        "which allows each experimental setting to be documented beside its value.",
        "joblib serialises fitted pipelines to disk. It is more efficient than the standard pickle "
        "module for objects containing large NumPy arrays.",
        "SciPy supplies the statistical distributions from which the randomised hyper-parameter search "
        "draws candidate values.",
        "pytest is the testing framework used for the automated test suite described in Chapter 13.",
        "requests performs the HTTP download of the dataset files.",
        "Graphviz renders the structural diagrams reproduced in Chapters 10, 11 and 12 from textual "
        "descriptions, so that the diagrams are regenerated automatically whenever the design changes.",
    ])

    b.h2("7.7  The Algorithms")
    b.p("Eight classification algorithms are compared. They are described here in outline; their "
        "configured hyper-parameters are given in Chapter 10.")
    b.h3("7.7.1  Logistic Regression")
    b.p("Logistic Regression models the log-odds of the positive class as a linear combination of the "
        "features and is fitted by maximising the penalised likelihood. It is fast, its coefficients "
        "are directly interpretable as the effect of each metric on the log-odds of defectiveness, and "
        "it provides a natural baseline against which non-linear models are judged.")
    b.h3("7.7.2  Decision Tree")
    b.p("A decision tree recursively partitions the feature space by selecting, at each node, the "
        "feature and threshold that best separate the classes according to an impurity criterion. Trees "
        "are highly interpretable and require no feature scaling, but a single tree has high variance: "
        "small changes in the training data can produce a substantially different tree.")
    b.h3("7.7.3  Random Forest")
    b.p("Random Forest, introduced by Breiman in 2001, addresses the variance of a single tree by "
        "constructing many trees on bootstrap resamples of the training data and restricting each split "
        "to a random subset of the features. Averaging the predictions of the resulting de-correlated "
        "trees reduces variance substantially without a corresponding increase in bias.")
    b.h3("7.7.4  Gradient Boosting")
    b.p("Gradient Boosting, formalised by Friedman in 2001, also builds an ensemble of trees but does "
        "so sequentially. Each new tree is fitted to the negative gradient of the loss function with "
        "respect to the current ensemble prediction, so that successive trees concentrate on the "
        "instances that the ensemble currently handles worst. The trees are deliberately shallow and "
        "their contributions are scaled by a small learning rate. Gradient boosting typically attains "
        "lower bias than bagging but is more sensitive to noise and to hyper-parameter settings.")
    b.h3("7.7.5  Support Vector Machine")
    b.p("The Support Vector Machine of Cortes and Vapnik seeks the hyperplane that separates the "
        "classes with the largest margin, admitting a controlled number of violations. Applying a "
        "radial basis function kernel allows a non-linear boundary to be constructed implicitly in a "
        "high-dimensional space. Because the algorithm returns a signed distance rather than a "
        "probability, the implementation used here wraps it in a calibration stage that converts the "
        "distance into a probability, so that the receiver operating characteristic and "
        "precision-recall curves can be computed consistently with the other models.")
    b.h3("7.7.6  k-Nearest Neighbours")
    b.p("The k-nearest-neighbours classifier stores the training set and classifies a new instance by a "
        "weighted vote among its k closest training instances. It makes no assumption about the form of "
        "the decision boundary, but it is sensitive to the scale of the features, which is one reason "
        "the standardisation step in the pipeline matters.")
    b.h3("7.7.7  Gaussian Naive Bayes")
    b.p("Gaussian Naive Bayes applies Bayes' theorem under the assumption that the features are "
        "conditionally independent given the class and that each follows a normal distribution within "
        "each class. The independence assumption is plainly violated by these highly collinear metrics, "
        "yet the classifier frequently performs competitively because its very low variance is an "
        "advantage on small, noisy datasets. This is the classifier that Menzies and colleagues found "
        "most effective in their 2007 study.")
    b.h3("7.7.8  Multi-Layer Perceptron")
    b.p("The multi-layer perceptron is a feed-forward neural network with one or more hidden layers of "
        "non-linear units, trained by backpropagation of error. Two hidden layers are used here. Early "
        "stopping on a held-out portion of the training data is enabled to limit overfitting, which is "
        "a serious risk given the small size of the datasets.")


# =========================================================================== #
def ch8_requirements(b: ReportBuilder) -> None:
    b.chapter("System Requirement")

    b.h2("8.1  Software Requirements")
    b.kv_lines([
        ("Operating system", "Windows 11 (developed and tested); Linux and macOS also supported"),
        ("Programming language", "Python 3.13 (version 3.9 or later is sufficient)"),
        ("Package manager", "pip 25.3"),
        ("Development environment", "PyCharm Community Edition / Visual Studio Code"),
        ("Core libraries", "NumPy 2.2, pandas 2.2, SciPy 1.18"),
        ("Machine learning", "scikit-learn 1.9, imbalanced-learn 0.14"),
        ("Visualisation", "matplotlib 3.11, seaborn 0.13"),
        ("Configuration and persistence", "PyYAML 6.0, joblib 1.6"),
        ("Testing framework", "pytest 9.1"),
        ("Diagram rendering", "Graphviz 12.2"),
        ("Document preparation", "Microsoft Word 2016 or later"),
    ])
    b.p("All libraries are declared with minimum versions in the requirements.txt file submitted with "
        "the source code, so that the environment can be recreated with a single command.")

    b.h2("8.2  Hardware Requirements")
    b.p("The system has modest hardware requirements because the datasets are small; the largest, JM1, "
        "occupies less than one megabyte. The configuration used for development is given below, "
        "together with the minimum on which the system has been confirmed to run.")
    b.table("8.1", "Hardware requirements",
            ["Component", "Minimum", "Used for development"],
            [["Processor", "Intel Core i3, dual core, 2.0 GHz", "Intel Core i5, quad core, 2.4 GHz"],
             ["Main memory", "4 GB", "8 GB"],
             ["Free disk space", "2 GB", "10 GB"],
             ["Display", "1366 × 768", "1920 × 1080"],
             ["Network", "Required once, to download the datasets", "Broadband"],
             ["Graphics accelerator", "Not required", "Not used"]],
            col_widths=[1.6, 2.3, 2.3], font_size=11)
    b.p("No graphics accelerator is required. None of the eight algorithms used benefits from one at "
        "this data scale, and the complete experiment over all four datasets, comprising thirty-two "
        "model fits together with their cross-validation, completes in approximately six minutes on the "
        "development machine.")

    b.h2("8.3  Functional Requirements")
    b.numbered([
        "The system shall download the specified benchmark datasets and cache them locally.",
        "The system shall parse files in the Attribute-Relation File Format and normalise the class "
        "attribute to a binary integer target.",
        "The system shall remove duplicate records and constant attributes before analysis.",
        "The system shall partition the data into training and test sets while preserving the class "
        "proportion in both.",
        "The system shall fit all learned transformations exclusively on training data.",
        "The system shall support three strategies for class imbalance: synthetic over-sampling, "
        "cost-sensitive class weighting, and no treatment.",
        "The system shall train and evaluate the eight configured classifiers and report seven "
        "performance measures for each.",
        "The system shall persist every fitted model and export all results in both CSV and JSON form.",
        "The system shall generate the figures required for analysis without requiring a display.",
        "The system shall score a user-supplied file of module metrics using a previously trained model.",
    ])

    b.h2("8.4  Non-Functional Requirements")
    b.bullets([
        "Reproducibility: two executions with the same configuration and seed shall produce numerically "
        "identical results. This is verified by an automated test.",
        "Configurability: the dataset, balancing strategy, cross-validation design, model list and "
        "random seed shall be modifiable without editing source code.",
        "Portability: the system shall run on Windows, Linux and macOS with no platform-specific code.",
        "Performance: a complete run over all four datasets shall complete within ten minutes on the "
        "specified minimum hardware.",
        "Maintainability: each module shall have a single responsibility and the dependency graph "
        "between modules shall be acyclic.",
        "Testability: the automated test suite shall execute in under one minute so that it can be run "
        "after every change.",
    ])


# =========================================================================== #
def ch9_system_analysis(b: ReportBuilder) -> None:
    b.chapter("System Analysis")
    b.p("System analysis is the study of a problem domain undertaken in order to establish what a "
        "system must do before any decision is taken about how it will do it. This chapter records the "
        "analysis performed for the present system: the feasibility of the undertaking, the "
        "identification of the principal components, the characteristics of the data that constrain the "
        "design, and the risks that were identified and mitigated.")

    b.h2("9.1  Feasibility Study")
    b.h3("9.1.1  Technical feasibility")
    b.p("The project is technically feasible. Every algorithm required is available in a mature, "
        "well-documented open-source library; the datasets are public and small; the computational "
        "demand is met by an ordinary laptop; and the necessary theoretical background is covered by "
        "the Soft Computing Techniques and Advanced Software Engineering courses of the programme. No "
        "component of the system required the development of a new algorithm.")
    b.h3("9.1.2  Economic feasibility")
    b.p("The project has no monetary cost. All software used is open source and licensed for academic "
        "use, the datasets are in the public domain, and the hardware was already available. The only "
        "resource consumed is the student's time.")
    b.h3("9.1.3  Operational feasibility")
    b.p("The resulting system is operationally practical. It is driven from the command line, requires "
        "no installation beyond a single package-manager invocation, and produces its output as CSV, "
        "JSON and PNG files that can be consumed by any downstream tool. In an industrial setting it "
        "could be executed as a step in a continuous-integration pipeline without modification.")
    b.h3("9.1.4  Schedule feasibility")
    b.p("The work was completed within the duration of the second semester. The literature survey and "
        "dataset acquisition occupied the first phase, the implementation of the pipeline and the "
        "classifier registry the second, the experimental runs and analysis the third, and the "
        "preparation of this report the fourth.")

    b.h2("9.2  Analysis of the Data")
    b.p("The characteristics of the data drive several design decisions, and were established before "
        "any model was built.")
    b.bullets([
        "Volume. The four datasets contain 1,162, 7,720, 679 and 327 modules respectively after "
        "cleaning. These are small by the standards of contemporary machine learning, which rules out "
        "high-capacity models and makes variance, rather than bias, the dominant source of error.",
        "Dimensionality. Twenty-one metrics are common to all four datasets; PC1 and CM1 carry a "
        "further sixteen. The ratio of instances to features is comfortable for KC1 and JM1 but is "
        "marginal for CM1, where 327 modules are described by 37 features.",
        "Class balance. The proportion of defective modules ranges from 8.1 per cent in PC1 to 25.3 per "
        "cent in KC1. Every dataset is imbalanced, and the degree of imbalance varies enough between "
        "them to allow its effect to be observed.",
        "Missing values. The cleaned datasets contain no missing values. The original files do, which "
        "is why median imputation is retained in the pipeline: the software supports both variants.",
        "Distribution. Every metric is strongly right-skewed, with sample skewness ranging from 0.77 to "
        "3.74 in KC1. A small number of very large modules dominates the upper tail of each "
        "distribution.",
        "Collinearity. The Halstead measures are algebraic functions of the same four token counts, so "
        "many pairs correlate above 0.9. The effective dimensionality is therefore far below the "
        "nominal dimensionality, which limits the benefit obtainable from feature selection.",
    ])

    b.h2("9.3  Identification of the Major Components")
    b.p("Six components were identified during analysis, and these became the modules described in "
        "Chapter 6: an acquisition component responsible for obtaining and parsing the data; a cleaning "
        "and partitioning component; a transformation component; a modelling component holding the "
        "classifier definitions; an evaluation component computing the performance measures; and a "
        "reporting component generating tables and figures. The interfaces between them were defined in "
        "terms of pandas data frames and scikit-learn estimator objects, both of which are standard and "
        "widely understood.")

    b.h2("9.4  Risk Analysis")
    b.table("9.1", "Risks identified during analysis and their mitigation",
            ["Risk", "Impact", "Mitigation adopted"],
            [["Information leakage between training and test data",
              "Reported results would be optimistic and the study worthless",
              "All learned steps placed inside a pipeline refitted within each fold; verified by test"],
             ["Use of the original, duplicate-laden datasets",
              "Inflated performance, incomparable with sound studies",
              "Cleaned D-double-prime versions used by default; the difference is measured and reported"],
             ["Class imbalance causing a degenerate majority-class model",
              "Recall near zero despite high accuracy",
              "SMOTE applied within training folds; accuracy de-emphasised in favour of F1, MCC and PF"],
             ["Unequal tuning effort between algorithms",
              "An unfair comparison favouring the tuned model",
              "Literature-standard defaults used for all models in the headline results"],
             ["Non-reproducible results",
              "Findings could not be verified by an examiner",
              "One seed governs every stochastic component; a test asserts run-to-run equality"],
             ["Dataset source becoming unavailable",
              "The experiment could not be re-executed",
              "Files cached locally after first download and a secondary source implemented"],
             ["Platform-specific failure of the kernel method",
              "The experiment would abort part-way",
              "Cross-validation configured to execute sequentially by default on Windows"]],
            col_widths=[1.8, 2.0, 2.4], font_size=10)

    b.h2("9.5  Analysis Outcome")
    b.p("The analysis established that the problem is a supervised binary classification task on small, "
        "imbalanced, skewed and collinear tabular data with noisy labels; that the principal threat to "
        "the validity of any result is methodological rather than computational; and that the system "
        "must therefore be designed so that the correct handling of training and test data is enforced "
        "structurally rather than left to the discipline of the programmer. This conclusion determined "
        "the central design decision of the project, namely the use of pipelines as the unit of "
        "modelling.")


# =========================================================================== #
def ch10_methodology(b: ReportBuilder) -> None:
    b.chapter("Methodology")
    b.p("This chapter describes the experimental method in sufficient detail for it to be reproduced "
        "independently. Figure 10.1 gives the overall flow, and the sections that follow treat each "
        "stage in turn.")
    b.figure(FIG / "fig4_1_methodology.png", "10.1",
             "Overall methodology of the defect-prediction pipeline")

    b.h2("10.1  Datasets")
    b.p("Four datasets from the NASA Metrics Data Program were selected. They are the most widely used "
        "benchmarks in the field, which permits direct comparison with published work, and they differ "
        "substantially in size, in the language of the system measured and in the proportion of "
        "defective modules, which allows the sensitivity of the conclusions to those factors to be "
        "assessed. The cleaned D-double-prime versions published by Shepperd and colleagues are used "
        "throughout.")
    b.table("10.1", "Characteristics of the four datasets after cleaning",
            ["Dataset", "Language", "System described", "Modules", "Features", "Defective", "Defect %"],
            [["KC1", "C++", "Storage management for ground data", "1,162", "21", "294", "25.3"],
             ["JM1", "C", "Real-time predictive ground system", "7,720", "21", "1,612", "20.9"],
             ["PC1", "C", "Flight software, earth-orbiting satellite", "679", "37", "55", "8.1"],
             ["CM1", "C", "Spacecraft instrument", "327", "37", "42", "12.8"]],
            col_widths=[0.7, 0.7, 2.0, 0.7, 0.7, 0.75, 0.68], font_size=10)
    b.figure(FIG / "fig_imbalance_all.png", "10.2",
             "Composition and class imbalance of the four datasets")

    b.h2("10.2  Data Cleaning")
    b.p("Two cleaning operations are applied before the data is partitioned. Neither estimates any "
        "quantity from the data, so applying them to the whole dataset introduces no leakage.")
    b.p("Duplicate removal discards records that are identical in every field. On the cleaned datasets "
        "this removes nothing, since Shepperd and colleagues have already performed it, but it removes "
        "897 of the 2,109 records of the original KC1 file. The operation is retained because it is "
        "essential whenever the original files are used: a duplicated record that falls on both sides "
        "of the train-test partition is a record the model has memorised rather than learned from, and "
        "its presence inflates every measure.")
    b.p("Constant-column removal discards attributes that take the same value in every record. Such "
        "columns carry no information, and they cause a division by zero during standardisation.")

    b.h2("10.3  Partitioning and Validation Design")
    b.p("The data is divided once into a training partition containing eighty per cent of the modules "
        "and a test partition containing the remaining twenty per cent. The division is stratified, "
        "meaning that the proportion of defective modules is preserved in both partitions. Without "
        "stratification a test set drawn from CM1, which contains only forty-two defective modules in "
        "total, could by chance contain very few positive instances, and the resulting recall would be "
        "meaningless.")
    b.figure(FIG / "fig_split_flow.png", "10.3",
             "Partitioning of KC1 and the point at which over-sampling is applied")
    b.p("Within the training partition, each model is assessed by stratified five-fold "
        "cross-validation. The training data is divided into five equally sized stratified blocks; each "
        "block serves once as a validation set while the remaining four are used for fitting, and the "
        "five resulting scores are averaged. The standard deviation across the folds provides an "
        "estimate of the variability of the measure, which is essential for judging whether a "
        "difference between two models is meaningful. Figure 10.4 illustrates the scheme.")
    b.figure(FIG / "fig_kfold.png", "10.4", "Stratified five-fold cross-validation")
    b.p("After cross-validation, each model is refitted on the entire training partition and evaluated "
        "once on the test partition. The test partition is used exactly once per model and takes no "
        "part in any fitting, transformation or selection decision. All headline figures reported in "
        "Chapter 15 are hold-out figures; the cross-validation results are reported alongside them as "
        "an indication of stability.")

    b.h2("10.4  Preprocessing")
    b.p("Three learned transformations are applied in sequence, all of them inside the pipeline.")
    b.h3("10.4.1  Median imputation")
    b.p("Missing values are replaced by the median of the corresponding feature, computed on the "
        "training folds only. The median is preferred to the mean because the distributions are heavily "
        "skewed and the mean is drawn upward by the extreme upper tail.")
    b.h3("10.4.2  Logarithmic transformation")
    b.p("Each feature x is replaced by log(1 + x). The transformation is applied for two reasons. The "
        "distributions are strongly right-skewed, and a linear or distance-based model fitted to "
        "untransformed values is dominated by a small number of very large modules. The logarithm "
        "compresses the upper tail while preserving order. The form log(1 + x) rather than log(x) is "
        "used because several metrics legitimately take the value zero, for which the logarithm is "
        "undefined, whereas log(1 + 0) = 0. This transformation follows the recommendation of Menzies "
        "and colleagues.")
    b.h3("10.4.3  Standardisation")
    b.p("Each feature is finally rescaled to zero mean and unit variance using statistics computed on "
        "the training folds. This is required by the algorithms that depend on distances or on the "
        "magnitude of coefficients, namely k-nearest neighbours, the support vector machine, logistic "
        "regression and the neural network. The tree-based models are invariant to monotone rescaling "
        "and are unaffected, but the same pipeline is applied to every model so that the comparison is "
        "not confounded by differences in preprocessing.")

    b.h2("10.5  Treatment of Class Imbalance")
    b.p("The Synthetic Minority Over-sampling Technique is applied to the training data only. For each "
        "minority instance, one of its five nearest minority neighbours is selected at random and a "
        "synthetic instance is generated at a uniformly random position on the line segment joining "
        "them. The process repeats until the two classes contain an equal number of instances. On the "
        "KC1 training partition this raises the count from 929 modules with 235 defective to 1,388 "
        "modules with 694 defective.")
    b.figure(FIG / "fig4_2_smote.png", "10.5", "Working principle of synthetic minority over-sampling")
    b.p("The placement of this step inside the pipeline is the single most important design decision in "
        "the experiment. Because the pipeline provided by imbalanced-learn executes the resampler "
        "during fitting but bypasses it during prediction, the synthetic instances are generated "
        "independently within every cross-validation fold and are never present in any data on which "
        "the model is evaluated. Two alternatives are supported for comparison: cost-sensitive learning "
        "through balanced class weights, in which the loss function penalises minority-class errors in "
        "inverse proportion to class frequency, and no treatment at all. The comparison between "
        "over-sampling and no treatment constitutes the ablation study of Section 15.5.")
    b.figure(FIG / "fig6_1_pipeline.png", "10.6",
             "Composition of the preprocessing and classification pipeline")

    b.h2("10.6  Classification Algorithms")
    b.p("Eight algorithms were selected to span the principal model families identified in the "
        "literature survey. Their configured hyper-parameters are given in Table 10.2. These are the "
        "library defaults except where the literature indicates a standard alternative, and no model "
        "received additional tuning for the headline results, so that the comparison is not confounded "
        "by unequal optimisation effort. A randomised hyper-parameter search over fifteen candidate "
        "configurations is implemented and can be enabled from the command line; its effect is reported "
        "in Section 15.7.")
    b.table("10.2", "The eight classifiers and their principal hyper-parameters",
            ["Classifier", "Family", "Principal settings"],
            [["Logistic Regression", "Linear", "L2 penalty, C = 1, maximum 2,000 iterations"],
             ["Decision Tree", "Single tree", "Maximum depth 8, minimum 5 samples per leaf, Gini impurity"],
             ["Random Forest", "Bagging ensemble", "300 trees, minimum 2 samples per leaf, sqrt(d) features per split"],
             ["Gradient Boosting", "Boosting ensemble", "200 trees, learning rate 0.05, maximum depth 3"],
             ["SVM", "Kernel method", "RBF kernel, C = 1, gamma = scale, sigmoid-calibrated probabilities"],
             ["k-Nearest Neighbours", "Instance based", "k = 7, distance weighting, Euclidean metric"],
             ["Gaussian Naive Bayes", "Probabilistic", "Default variance smoothing"],
             ["Multi-Layer Perceptron", "Neural network",
              "Hidden layers (64, 32), ReLU, Adam, alpha = 0.001, early stopping"]],
            col_widths=[1.5, 1.3, 3.4], font_size=10)

    b.h2("10.7  Evaluation Measures")
    b.p("All measures derive from the four cells of the confusion matrix, shown in Figure 10.7 with the "
        "defective class taken as positive.")
    b.figure(FIG / "fig_confmatrix_expl.png", "10.7",
             "The confusion matrix and the meaning of each cell in this problem",
             width_in=5.0)
    b.p("The measures are defined as follows.")
    b.bullets([
        "Accuracy is the proportion of all modules classified correctly. It is reported for "
        "completeness but is not used to rank the models, because under strong imbalance it rewards a "
        "model that ignores the minority class.",
        "Precision is the proportion of the modules flagged as defective that really are defective. It "
        "measures the efficiency of the inspection effort that the prediction triggers.",
        "Recall, also called the probability of detection, is the proportion of the genuinely defective "
        "modules that the model flags. It measures how much of the risk the model actually catches.",
        "The F1-score is the harmonic mean of precision and recall. It is used as the primary ranking "
        "criterion because it is high only when both components are high.",
        "The probability of false alarm is the proportion of clean modules that are incorrectly "
        "flagged. It measures the waste that the prediction imposes on the reviewers.",
        "The area under the receiver operating characteristic curve is the probability that a randomly "
        "chosen defective module receives a higher score than a randomly chosen clean one. It is "
        "independent of the decision threshold and of class prevalence, and is used as the secondary "
        "criterion.",
        "The Matthews Correlation Coefficient is the correlation between the predicted and the true "
        "labels, taking values in the interval from minus one to one. It is the most reliable "
        "single-figure summary under imbalance because it is high only when all four cells of the "
        "confusion matrix are favourable.",
    ])

    b.h2("10.8  Reproducibility")
    b.p("A single integer seed, fixed at 42, governs the training and test partition, the assignment of "
        "instances to cross-validation folds, the random choices made by the over-sampling algorithm "
        "and the initialisation of every stochastic learning algorithm. All experimental settings are "
        "declared in one configuration file, and each execution writes the settings that were actually "
        "in force to a summary file alongside its results. An automated test asserts that two "
        "executions with the same configuration produce numerically identical measures. Consequently "
        "every figure quoted in Chapter 15 can be regenerated exactly by re-running the submitted code.")


# =========================================================================== #
def ch11_dfd(b: ReportBuilder) -> None:
    b.chapter("DFD")
    b.p("A Data Flow Diagram is a graphical representation of the movement of data through a system. It "
        "shows the processes that transform data, the stores in which data rests, the external entities "
        "that supply or consume data, and the flows that connect them. It deliberately says nothing "
        "about the order in which processes execute or about the control logic that invokes them; it is "
        "a model of data movement alone, which is what makes it a useful complement to the sequence and "
        "architecture views presented elsewhere in this report.")

    b.h2("11.1  Components of a Data Flow Diagram")
    b.bullets([
        "A process transforms incoming data into outgoing data. It is drawn as a circle or rounded "
        "rectangle and is labelled with a verb phrase and a reference number.",
        "A data flow, drawn as a directed arrow, carries data from one element of the diagram to "
        "another and is labelled with the data it carries.",
        "A data store, drawn as an open rectangle or a cylinder, holds data at rest between processes. "
        "In this system the stores are directories and files on disk.",
        "An external entity, drawn as a square, lies outside the system boundary and either supplies "
        "data to the system or receives data from it.",
    ])

    b.h2("11.2  Rules Observed in Constructing the Diagrams")
    b.numbered([
        "Every process, store and entity carries a name that is meaningful without reference to "
        "explanatory text.",
        "Processes are numbered so that they can be referred to unambiguously in discussion.",
        "Every data flow is labelled with the data it carries, not with the action that produces it.",
        "Data cannot flow directly from one store to another, nor directly between two external "
        "entities; a process must always intervene.",
        "The diagram is balanced: the flows crossing the boundary of the context diagram are exactly "
        "the flows entering and leaving the level-1 diagram.",
    ])

    b.h2("11.3  Level-0 Data Flow Diagram (Context Diagram)")
    b.p("The context diagram treats the entire system as a single process. The researcher supplies the "
        "name of a dataset and the desired experimental configuration; the PROMISE repository supplies "
        "the dataset file; and the system returns performance tables, figures and trained models. This "
        "level establishes the boundary of the system and identifies the two external entities.")
    b.figure(FIG / "fig5_2_dfd.png", "11.1",
             "Level-1 data-flow diagram of the defect-prediction system", width_in=3.6)

    b.h2("11.4  Level-1 Data Flow Diagram")
    b.p("The level-1 diagram, shown in Figure 11.1, decomposes the single process of the context "
        "diagram into six numbered processes and four data stores. The processes are as follows.")
    b.bullets([
        "Process 1.0, Download, retrieves the ARFF file from the repository mirror and writes it to "
        "store D1. If the file is already present the process is bypassed.",
        "Process 2.0, Parse and clean, reads the raw rows from D1, converts them into a data frame, "
        "encodes the class attribute and removes duplicate and constant columns.",
        "Process 3.0, Split, divides the clean frame into a training set and a test set, preserving the "
        "class proportion. Its behaviour is governed by the configuration file.",
        "Process 4.0, Train and cross-validate, builds the pipeline for each classifier, performs "
        "stratified cross-validation on the training set and fits the final model, writing the fitted "
        "pipelines to store D2.",
        "Process 5.0, Evaluate, applies the fitted pipelines to the test set and computes the seven "
        "performance measures, writing them to store D3.",
        "Process 6.0, Visualise, reads the stored measures and the fitted models and produces the "
        "figures, writing them to store D4.",
    ])
    b.p("The four data stores are D1, the cache of downloaded dataset files; D2, the directory of "
        "serialised model pipelines; D3, the tabular results in CSV and JSON form; and D4, the "
        "directory of generated figures. The strictly one-directional flow from D1 through to D4 is a "
        "deliberate property of the design: no process writes to a store that an earlier process reads, "
        "so a run can be interrupted and resumed, and the outputs of runs made under different "
        "configurations can coexist without interference.")

    b.h2("11.5  Relationship to the Software Architecture")
    b.p("The processes of the level-1 diagram correspond directly to the modules described in Chapter "
        "6: process 1.0 and part of 2.0 are implemented by the data loader, the remainder of 2.0 and "
        "3.0 by the preprocessing module, 4.0 by the models and preprocessing modules under the "
        "direction of the pipeline script, 5.0 by the evaluation module and 6.0 by the visualization "
        "module. This correspondence was intentional; the data-flow analysis was performed first and "
        "the module boundaries were then drawn to match it.")
