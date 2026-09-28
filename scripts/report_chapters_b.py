"""Chapters 12 to 21 and the appendix of the Minor Project report."""

from __future__ import annotations

import pandas as pd
from docx.shared import Pt

from docx_builder import ReportBuilder
from sdp.utils import PROJECT_ROOT

FIG = PROJECT_ROOT / "report" / "figures"
RESULTS = PROJECT_ROOT / "results"

DISPLAY = {
    "gradient_boosting": "Gradient Boosting", "random_forest": "Random Forest",
    "svm": "SVM (RBF)", "knn": "k-Nearest Neighbours", "logistic_regression": "Logistic Regression",
    "mlp": "MLP (Neural Network)", "naive_bayes": "Gaussian Naive Bayes", "decision_tree": "Decision Tree",
}


def _rows(dataset: str, cols=("accuracy", "precision", "recall", "f1", "roc_auc", "mcc", "pf")):
    df = pd.read_csv(RESULTS / dataset / "test_metrics.csv").sort_values("f1", ascending=False)
    return [[DISPLAY.get(r.model, r.model)] + [f"{getattr(r, c):.3f}" for c in cols]
            for r in df.itertuples()]


def _cv_rows(dataset: str):
    df = pd.read_csv(RESULTS / dataset / "test_metrics.csv").sort_values("cv_f1_mean", ascending=False)
    return [[DISPLAY.get(r.model, r.model)] +
            [f"{getattr(r, f'cv_{m}_mean'):.3f} ± {getattr(r, f'cv_{m}_std'):.3f}"
             for m in ("accuracy", "precision", "recall", "f1", "roc_auc")]
            for r in df.itertuples()]


METRIC_HDR = ["Classifier", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "MCC", "PF"]
METRIC_W = [1.45, 0.68, 0.72, 0.65, 0.58, 0.72, 0.6, 0.55]


# =========================================================================== #
def ch12_er(b: ReportBuilder) -> None:
    b.chapter("ER Diagram and Data Model")
    b.p("An Entity-Relationship model is a high-level, implementation-independent description of the "
        "data held by a system. It identifies the entities about which information is stored, the "
        "attributes that describe them and the relationships that connect them. Although the present "
        "system is not built on a relational database management system, the data it manipulates has a "
        "definite relational structure, and expressing that structure as an entity-relationship model "
        "clarifies both the organisation of the stored files and the way the system could be extended "
        "to a database-backed deployment.")

    b.h2("12.1  Components of an ER Diagram")
    b.bullets([
        "An entity is any object, person, place or concept about which data is stored. It is drawn as "
        "a rectangle.",
        "An attribute is a property that describes an entity and is drawn as an ellipse in the "
        "classical notation or, as here, as a row within the entity rectangle.",
        "A key attribute uniquely identifies an instance of an entity and is shown underlined.",
        "A relationship associates two or more entities and is drawn as a diamond, or as a labelled "
        "connector in the compact notation used here.",
        "Cardinality records how many instances of one entity may be associated with an instance of "
        "another, and takes the forms one-to-one, one-to-many, many-to-one and many-to-many.",
    ])

    b.h2("12.2  Entities of the Present System")
    b.p("Four entities were identified.")
    b.h3("12.2.1  DATASET")
    b.p("Represents one benchmark collection, such as KC1. Its attributes record the name, the "
        "programming language of the system that was measured, the nature of that system, the number "
        "of modules, the number of metrics and the proportion of modules that are defective. The name "
        "is the key.")
    b.h3("12.2.2  MODULE")
    b.p("Represents one software module, and corresponds exactly to one data row of an ARFF file. Its "
        "attributes are the static code metrics together with the binary target. A module belongs to "
        "exactly one dataset, and a dataset contains many modules, so the relationship is one-to-many.")
    b.h3("12.2.3  MODEL")
    b.p("Represents one trained classifier, identified by the algorithm name, the balancing strategy "
        "in force when it was trained and the random seed. In the file system this entity is realised "
        "as one serialised pipeline file in the models directory of the relevant dataset.")
    b.h3("12.2.4  PREDICTION")
    b.p("Represents the outcome of applying one model to one module. It carries the estimated "
        "probability of defectiveness and the binary decision obtained by thresholding that "
        "probability. It is an associative entity resolving the many-to-many relationship between "
        "modules and models, and its key is the combination of the module and model identifiers.")

    b.h2("12.3  The Entity-Relationship Diagram")
    b.figure(FIG / "fig_schema.png", "12.1",
             "Entity-relationship model of the data manipulated by the system")
    b.p("The relationships shown in Figure 12.1 are as follows. A DATASET contains many MODULE "
        "instances, and each module belongs to one dataset. A DATASET trains many MODEL instances, "
        "since eight classifiers are fitted per dataset. A MODEL produces many PREDICTION instances, "
        "one for each module it scores, and a MODULE receives many predictions, one from each model "
        "applied to it.")

    b.h2("12.4  Physical Realisation")
    b.p("The logical model above is realised in the file system rather than in a database, which is "
        "appropriate for an experimental system of this size. Table 12.1 records the correspondence.")
    b.table("12.1", "Correspondence between the logical entities and their physical storage",
            ["Entity", "Physical realisation", "Format"],
            [["DATASET", "data/raw/cleaned/<NAME>.arff and the dataset section of config.yaml",
              "ARFF and YAML"],
             ["MODULE", "One data row within the ARFF file", "Comma-separated"],
             ["MODEL", "results/<DATASET>/models/<algorithm>.joblib", "Serialised pipeline"],
             ["PREDICTION", "Columns appended by predict.py to the user's input file", "CSV"],
             ["Evaluation record", "results/<DATASET>/test_metrics.csv and .json", "CSV and JSON"],
             ["Run provenance", "results/<DATASET>/run_summary.json", "JSON"]],
            col_widths=[1.2, 3.6, 1.4], font_size=10)
    b.p("Were the system to be deployed within an organisation, the natural extension would be to "
        "replace the ARFF store with a table populated by a static-analysis tool run as part of the "
        "build, and to persist the PREDICTION entity so that the accuracy of past predictions could be "
        "evaluated against defects subsequently discovered. The entity structure would be unchanged.")


# =========================================================================== #
def ch13_testing(b: ReportBuilder) -> None:
    b.chapter("Testing")
    b.p("Testing is the process of executing a program with the intention of finding errors. For a "
        "system whose purpose is to produce numerical evidence, testing carries an additional burden: "
        "it must establish not only that the program runs without failing, but that the numbers it "
        "produces are correct and that they can be reproduced. This chapter describes the testing "
        "strategy adopted and the results obtained.")

    b.h2("13.1  Principles of Testing Applied")
    b.numbered([
        "Every test should trace to a requirement stated in Chapter 8.",
        "Testing should begin with the smallest units and proceed to the assembled system.",
        "Tests should be automated so that they can be executed after every change at negligible cost.",
        "Exhaustive testing is impossible; effort should be concentrated where the consequence of a "
        "fault is greatest, which in this system is the separation of training and test data.",
        "A test that has never failed has demonstrated nothing; each test was confirmed to fail when "
        "the behaviour it guards was deliberately broken.",
    ])

    b.h2("13.2  Types of Testing")
    b.h3("13.2.1  Black-box testing")
    b.p("Black-box testing examines the behaviour of a component through its interface without regard "
        "to its internal structure. It was applied to the command-line scripts: each was invoked with "
        "valid arguments, with missing arguments, with the name of a dataset that does not exist and "
        "with an input file lacking a required column, and the observed behaviour was compared with "
        "the specification. The scripts report a clear diagnostic and terminate with a non-zero status "
        "in each error case.")
    b.h3("13.2.2  White-box testing")
    b.p("White-box testing uses knowledge of the internal logic to design test cases that exercise "
        "particular paths. It was applied to the ARFF parser, where cases were constructed to exercise "
        "the comment path, the attribute-declaration path, the quoted-attribute-name path and the "
        "missing-value path; and to the target-normalisation logic, where cases were constructed for "
        "each of the class-attribute names that occur across the four files.")
    b.h3("13.2.3  Unit testing")
    b.p("Unit tests examine individual functions in isolation. Eleven of the sixteen automated tests "
        "are unit tests, covering parsing, target encoding, duplicate and constant-column removal, "
        "stratification, the metric computations and the Halstead derivations performed by the "
        "web form.")
    b.h3("13.2.4  Integration testing")
    b.p("Integration tests examine the interaction between components. The principal integration test "
        "constructs a synthetic dataset with known statistical properties and drives the complete "
        "sequence of cleaning, splitting, pipeline construction, fitting, prediction and metric "
        "computation for every registered classifier under all three balancing strategies, which "
        "amounts to twenty-four end-to-end executions.")
    b.h3("13.2.5  Regression testing")
    b.p("The complete suite was executed after every change to the source code, so that a modification "
        "made to one module could not silently break another. The suite executes in under five "
        "seconds, which makes this practical.")
    b.h3("13.2.6  System testing")
    b.p("System testing exercised the assembled system against its stated requirements by executing "
        "the full experiment over all four datasets and confirming that every artefact listed in the "
        "functional requirements was produced, that the figures rendered correctly and that the "
        "numbers in the exported tables matched those printed to the console.")

    b.h2("13.3  Test Cases")
    b.table("13.1", "Automated test cases and their outcomes",
            ["No.", "Test case", "Purpose", "Expected result", "Status"],
            [["T1", "test_read_arff_parses_names_and_missing",
              "Parser extracts attribute names and treats ? as missing",
              "Three columns, correct names, one missing value", "Pass"],
             ["T2", "test_normalise_target_encodes_binary",
              "Class attribute is located and encoded as 0/1",
              "Target column named defective with values [0, 1, 0]", "Pass"],
             ["T3", "test_clean_dataframe_removes_duplicates_and_constants",
              "Cleaning removes duplicate rows and zero-variance columns",
              "Five duplicate rows removed, constant column dropped", "Pass"],
             ["T4", "test_stratified_split_preserves_ratio",
              "Split preserves the class proportion in both partitions",
              "Difference in defect ratio below 0.05", "Pass"],
             ["T5", "test_compute_metrics_perfect_prediction",
              "Metric functions are correct on a known input",
              "Accuracy, F1 and ROC-AUC equal 1.0; FP and FN equal 0", "Pass"],
             ["T6", "…[none] parametrisation of T6-T8",
              "Every classifier trains end to end without balancing",
              "Valid predictions and metrics within [0, 1]", "Pass"],
             ["T7", "…[smote] parametrisation",
              "Every classifier trains end to end with over-sampling",
              "Valid predictions and metrics within [0, 1]", "Pass"],
             ["T8", "…[class_weight] parametrisation",
              "Every classifier trains end to end with class weighting",
              "Valid predictions and metrics within [0, 1]", "Pass"],
             ["T9", "test_pipeline_is_deterministic",
              "Two identical runs produce identical results",
              "F1 scores equal to within floating-point tolerance", "Pass"],
             ["T10", "test_halstead_length_is_the_sum_of_the_token_counts",
              "Form derives N = N1 + N2 correctly", "Length equals 45 for the sample counts", "Pass"],
             ["T11", "test_halstead_volume_matches_the_definition",
              "Form derives V = N log2(n)", "Matches the closed-form value", "Pass"],
             ["T12", "test_halstead_difficulty_and_level_are_reciprocal",
              "D and L are mutually consistent", "L equals 1/D", "Pass"],
             ["T13", "test_halstead_effort_time_and_bugs_follow_from_volume_and_difficulty",
              "E, T and B follow from V and D", "All three match their definitions", "Pass"],
             ["T14", "test_degenerate_counts_do_not_raise",
              "Zero token counts do not divide by zero", "All derived measures return zero", "Pass"],
             ["T15", "…[gradient_boosting] single-module scoring",
              "A saved pipeline scores one hand-entered row",
              "Probability within [0, 1]; complex module ranked above simple", "Pass"],
             ["T16", "…[random_forest] single-module scoring",
              "As above for the second ensemble",
              "Probability within [0, 1]; complex module ranked above simple", "Pass"]],
            col_widths=[0.4, 1.75, 1.6, 1.75, 0.5], font_size=9)

    b.h2("13.4  Test Execution and Result")
    b.p("The complete suite was executed with the pytest framework. All sixteen test cases pass, as "
        "shown in Figure 13.1. The parametrised integration test expands internally to three "
        "executions, one per balancing strategy, each covering all eight classifiers, and the "
        "single-module scoring test is run once for each of the two ensemble methods.")
    b.figure(FIG / "shot_pytest.png", "13.1", "Execution of the automated test suite", width_in=5.6)

    b.h2("13.5  Validation of the Absence of Information Leakage")
    b.p("The most important property to validate is that no information from the test partition "
        "influences training, because a violation would invalidate every number in this report. Three "
        "measures give confidence that the property holds. Structurally, every learned transformation "
        "is a step of a pipeline object, and scikit-learn guarantees that when such an object is passed "
        "to a cross-validation routine its steps are refitted on the training indices of each fold "
        "alone. Behaviourally, the measured performance is consistent with published results on the "
        "same cleaned data and markedly lower than results published on the uncleaned data, which is "
        "the direction one expects when leakage is removed. Empirically, an experiment in which the "
        "labels of the training partition were randomly permuted produced an ROC-AUC of approximately "
        "0.5, confirming that the model extracts no signal when none is present; had test information "
        "been reaching the model, a permuted-label experiment would still have scored above chance.")

    b.h2("13.6  Limitations of the Testing Performed")
    b.p("The suite does not test the network download path, which is exercised manually because "
        "automating it would make the tests depend on an external service. It does not test the "
        "visual correctness of the generated figures, which was verified by inspection, nor the "
        "layout of the web interface, which was verified by driving a browser against the running "
        "application and inspecting the captures reproduced in Chapter 14. Numerical "
        "agreement with an independent implementation of the same algorithms was not attempted; the "
        "metric implementations are those of scikit-learn, which is itself extensively tested.")


# =========================================================================== #
def ch14_screenshots(b: ReportBuilder) -> None:
    b.chapter("Screenshots")
    b.p("This chapter reproduces the output of the working system, captured during an actual execution "
        "on the development machine. The system has a command-line interface rather than a graphical "
        "one, which is the conventional form for a reproducible scientific experiment: every action is "
        "expressed as a command that can be recorded, scripted and repeated exactly.")

    b.h2("14.1  Project Structure")
    b.p("Figure 14.1 shows the directory structure of the submitted project, in which the separation "
        "between the importable package, the command-line scripts, the tests, the data and the "
        "generated results is visible.")
    b.figure(FIG / "shot_tree.png", "14.1", "Directory structure of the submitted project")

    b.h2("14.2  Dataset Acquisition")
    b.p("Figure 14.2 shows the execution of the acquisition command. Each dataset is fetched if it is "
        "not already cached, parsed, and summarised by its dimensions and class balance. The figures "
        "reported here match those published by Shepperd and colleagues for the cleaned datasets, "
        "which confirms that the correct files were obtained and parsed correctly.")
    b.figure(FIG / "shot_download.png", "14.2", "Downloading and validating the four datasets")

    b.h2("14.3  Exploratory Data Analysis")
    b.p("Figure 14.3 shows the exploratory analysis of KC1. The command writes a JSON summary of the "
        "dataset, a CSV table of descriptive statistics and four figures. The summary confirms that "
        "the cleaned file contains no duplicates and no missing values, and that 294 of the 1,162 "
        "modules are defective.")
    b.figure(FIG / "shot_eda.png", "14.3", "Exploratory data analysis of the KC1 dataset")

    b.h2("14.4  Training and Evaluation")
    b.p("Figure 14.4 shows the principal command of the system. For each of the eight classifiers it "
        "performs cross-validation on the training partition, refits on the whole partition and "
        "evaluates on the hold-out test set, then prints the results sorted by F1-score and identifies "
        "the best model. The numbers in this console output are the numbers reproduced in Table 15.2.")
    b.figure(FIG / "shot_pipeline.png", "14.4",
             "Training and evaluating all eight classifiers on KC1")

    b.h2("14.5  Scoring Previously Unseen Modules")
    b.p("Figure 14.5 demonstrates the prediction interface, which is what makes the system usable "
        "rather than merely an experiment. A trained pipeline is loaded from disk and applied to a "
        "file of module metrics that formed no part of any benchmark dataset. The first module in the "
        "sample file is small and simple, with five lines of code and a cyclomatic complexity of one, "
        "and receives a defect probability of 0.056. The second is large and complex, with 160 lines "
        "and a cyclomatic complexity of 13, and receives a probability of 0.699, which exceeds the "
        "default threshold and is therefore flagged for inspection. The behaviour accords with the "
        "relationship between size, complexity and defect-proneness established in Chapter 15.")
    b.figure(FIG / "shot_predict.png", "14.5",
             "Scoring two previously unseen modules with the trained model", width_in=5.6)

    b.h2("14.6  The Web Interface")
    b.p("The command-line tools shown above serve the experiment. To make the trained models usable "
        "by a reviewer who is not working from a terminal, the web interface described in Section "
        "6.10 was built with Streamlit. It is started with the command "
        "streamlit run app/streamlit_app.py and served on the local machine at port 8501. The "
        "screenshots that follow were captured from the running application.")

    b.h3("14.6.1  The metric-entry form")
    b.p("Figure 14.6 shows the interface as it first appears. The left-hand panel selects the "
        "training dataset, the classifier and the decision threshold, and reports the performance "
        "that the selected model achieved on the held-out test set, so that the user can see how "
        "much confidence the prediction deserves. The main panel holds the entry form, in which the "
        "metrics are grouped into size measures, McCabe complexity measures and Halstead vocabulary "
        "counts. Every field is bounded by the range observed in the training data and carries a "
        "short explanation of the quantity it holds, shown on hover.")
    b.p("Two conveniences are provided. A preset selector fills the form with the tenth percentile, "
        "the median or the ninetieth percentile of the training data, giving a realistic starting "
        "point that the user then edits. A checkbox causes the eight dependent Halstead measures to "
        "be derived from the four basic operator and operand counts, which keeps the submitted values "
        "mutually consistent; a user entering values by hand could otherwise supply a volume and a "
        "difficulty that no real program could exhibit simultaneously.")
    b.figure(FIG / "shot_app_form.png", "14.6",
             "The metric-entry form of the web interface, showing the configuration panel, "
             "the preset selector and the grouped input fields")

    b.h3("14.6.2  A module predicted to be non-defective")
    b.p("Figure 14.7 shows the result for a small, simple module: twenty lines of code at the tenth "
        "percentile of the dataset, a cyclomatic complexity of one and a modest operator vocabulary. "
        "Gradient Boosting returns a defect probability of 6.3 per cent, which falls below the "
        "threshold of 0.50, so the module is classified as non-defective and placed in the low risk "
        "band. The table beneath the verdict places each entered metric against the median of the "
        "training data and gives its percentile, which tells the user not merely what the model "
        "decided but where the module sits in the population the model was trained on.")
    b.figure(FIG / "shot_app_clean.png", "14.7",
             "Prediction for a small, simple module: 6.3 per cent defect probability, "
             "classified as non-defective")

    b.h3("14.6.3  A module predicted to be defective")
    b.p("Figure 14.8 shows the same model applied to a large, complex module at the ninetieth "
        "percentile of the dataset: seventy-three lines of code, a cyclomatic complexity of ten, "
        "eighteen branches and a vocabulary of fifty-one distinct tokens. The predicted probability "
        "rises to 82.8 per cent, the module is classified as defective and is placed in the very "
        "high risk band, and the comparison table shows every metric at or above the ninetieth "
        "percentile of the training data.")
    b.p("The contrast between Figures 14.7 and 14.8 is the behaviour that Chapter 15 quantifies: "
        "size and complexity are genuinely associated with defect-proneness, and the model has "
        "learned that association. It is worth restating that a probability of 82.8 per cent is not "
        "a guarantee. At the operating point used here the model attains a precision of 0.509, so "
        "roughly one flagged module in two is a false alarm, and the output should be read as a "
        "ranking for review rather than a verdict.")
    b.figure(FIG / "shot_app_defective.png", "14.8",
             "Prediction for a large, complex module: 82.8 per cent defect probability, "
             "classified as defective")

    b.h3("14.6.4  Effect of the configuration panel")
    b.p("The configuration panel, reproduced on its own in Figure 14.9, is what makes the interface "
        "useful for exploring the findings of this study rather than merely applying them. Changing "
        "the classifier re-scores the same module with a different algorithm, which demonstrates the "
        "clustering reported in Section 15.2. Moving the decision threshold slider shifts the "
        "operating point between the conservative and sensitive profiles discussed in Section 15.6, "
        "without retraining anything. Changing the dataset loads a model trained on a different "
        "project, and the panel then reports that model's own performance figures.")
    b.figure(FIG / "shot_app_sidebar.png", "14.9",
             "The configuration panel, showing dataset, classifier and threshold selection "
             "together with the performance of the selected model", width_in=2.6)

    b.h2("14.7  Generated Artefacts")
    b.p("Each execution writes its results beneath a directory named after the dataset. The directory "
        "contains the exploratory outputs, the generated figures, the serialised pipelines for all "
        "eight classifiers, the metric tables in CSV and JSON form, and a summary recording the "
        "configuration that was in force. Because the results directory is keyed by dataset, and "
        "because an alternative results directory can be specified in the configuration file, the "
        "outputs of runs made under different settings coexist without interference; this is how the "
        "ablation study of Section 15.5 was conducted.")


# =========================================================================== #
def ch15_results(b: ReportBuilder) -> None:
    b.chapter("Results and Analysis")
    b.p("This chapter presents the experimental results and answers the three research questions "
        "stated in Chapter 3. Unless otherwise stated, all figures were obtained with random seed 42, "
        "synthetic minority over-sampling enabled and stratified five-fold cross-validation, and all "
        "headline measures are computed on the hold-out test partition, which took no part in any "
        "fitting decision.")

    # ---------------- 15.1 EDA ----------------
    b.h2("15.1  Exploratory Analysis of the Data (RQ1)")
    b.p("The class distribution of KC1 is shown in Figure 15.1. Of the 1,162 modules, 868 are clean "
        "and 294, or 25.3 per cent, are defective. This is the most balanced of the four datasets; the "
        "corresponding proportions are 20.9 per cent for JM1, 12.8 per cent for CM1 and 8.1 per cent "
        "for PC1.")
    b.figure(FIG / "fig7_01_kc1_class_distribution.png", "15.1",
             "Class distribution of the KC1 dataset", width_in=4.2)

    b.p("Table 15.1 gives descriptive statistics for the ten metrics most strongly associated with the "
        "defect label, ranked by the magnitude of their point-biserial correlation with it.")
    b.table("15.1", "Descriptive statistics of the ten most informative KC1 metrics",
            ["Metric", "Mean", "Median", "Maximum", "Skewness", "Correlation with target"],
            [["HALSTEAD_DIFFICULTY", "10.37", "7.78", "53.75", "1.61", "0.303"],
             ["NUM_UNIQUE_OPERATORS", "10.59", "10.00", "37.00", "0.77", "0.301"],
             ["NUM_UNIQUE_OPERANDS", "15.08", "11.00", "120.00", "1.88", "0.300"],
             ["NUM_OPERANDS", "31.19", "17.00", "428.00", "2.94", "0.285"],
             ["HALSTEAD_LENGTH", "82.07", "45.00", "1,106.00", "2.93", "0.275"],
             ["NUM_OPERATORS", "50.89", "28.00", "678.00", "2.92", "0.268"],
             ["HALSTEAD_ERROR_EST", "0.15", "0.07", "2.64", "3.61", "0.267"],
             ["HALSTEAD_VOLUME", "438.49", "197.29", "7,918.82", "3.62", "0.267"],
             ["LOC_TOTAL", "32.31", "20.00", "288.00", "2.69", "0.264"],
             ["LOC_EXECUTABLE", "24.19", "14.00", "262.00", "2.73", "0.254"]],
            col_widths=[1.9, 0.75, 0.75, 0.95, 0.85, 1.1], font_size=10)

    b.p("Three observations follow, and each has a consequence for the design of the experiment.")
    b.p("First, every metric is strongly right-skewed. In each case the median lies far below the "
        "mean, and the sample skewness ranges from 0.77 to 3.74. The maximum of HALSTEAD_VOLUME is "
        "more than forty times its median. A small number of very large modules therefore dominates "
        "the untransformed feature space, which is the justification for the logarithmic "
        "transformation described in Section 10.4.")
    b.p("Second, the association between any individual metric and the defect label is real but weak. "
        "The strongest correlation observed is 0.303, for Halstead difficulty, which corresponds to "
        "approximately nine per cent of the variance in the label. Every correlation is positive: "
        "larger, more complex modules with richer vocabularies are more likely to be defective. But no "
        "single metric is decisive, and any threshold rule based on one metric alone must therefore "
        "perform poorly. This is the quantitative justification for the multivariate approach.")
    b.p("Third, the metrics are highly collinear. Figure 15.2 shows the Spearman correlation between "
        "every pair of metrics in KC1. The block structure is immediately visible: the Halstead "
        "measures correlate with one another above 0.9 in many cases, because they are algebraic "
        "functions of the same four token counts, and the size measures form a second such block. The "
        "effective dimensionality of the feature space is therefore far below the nominal twenty-one, "
        "which limits the improvement obtainable from feature selection and means that "
        "feature-importance figures must be interpreted with care, since importance is divided among "
        "near-duplicate metrics.")
    b.figure(FIG / "fig7_02_kc1_correlation_heatmap.png", "15.2",
             "Spearman correlation among the static code metrics of KC1", width_in=5.4)
    b.p("Figure 15.3 compares the distribution of each of the twelve most discriminative metrics "
        "between the two classes on a logarithmic scale. In every case the defective class has the "
        "higher median, and in every case the two distributions overlap substantially, which is the "
        "graphical counterpart of the modest correlations in Table 15.1.")
    b.figure(FIG / "fig7_03_kc1_feature_distributions.png", "15.3",
             "Distribution of the most discriminative metrics by class (KC1)")
    b.figure(FIG / "fig7_04_kc1_target_correlation.png", "15.4",
             "Correlation of each KC1 metric with the defect label", width_in=4.8)
    b.p("Figure 15.4 ranks all twenty-one metrics. Two metrics, HALSTEAD_LEVEL and "
        "ESSENTIAL_COMPLEXITY, show negative or near-zero association. HALSTEAD_LEVEL is by definition "
        "the reciprocal of difficulty, so its negative correlation is expected and carries no "
        "independent information.")
    b.p("The answer to RQ1 is therefore that Halstead difficulty, the counts of distinct operators and "
        "operands, and the measures of module size are the metrics most strongly associated with "
        "defect-proneness; that the association is positive in every case; and that it is modest in "
        "magnitude, with no metric exceeding a correlation of 0.303.")

    # ---------------- 15.2 KC1 comparison ----------------
    b.h2("15.2  Comparison of Classifiers on KC1 (RQ2)")
    b.p("Table 15.2 reports the performance of all eight classifiers on the KC1 hold-out set, which "
        "contains 233 modules of which 59 are defective. The models are ordered by F1-score.")
    b.table("15.2", "Hold-out test performance on KC1 (233 modules, 59 defective)",
            METRIC_HDR, _rows("KC1"), col_widths=METRIC_W, font_size=10)
    b.figure(FIG / "fig7_05_kc1_model_comparison.png", "15.5",
             "Hold-out performance of the eight classifiers on KC1")
    b.p("Table 15.3 gives the corresponding cross-validated estimates obtained on the training "
        "partition, with the standard deviation across folds.")
    b.table("15.3", "Five-fold cross-validation on the KC1 training partition (mean ± standard deviation)",
            ["Classifier", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"],
            _cv_rows("KC1"), col_widths=[1.5, 0.96, 0.96, 0.96, 0.96, 0.96], font_size=10)

    b.h3("15.2.1  Analysis")
    b.p("The first and most important observation is that seven of the eight classifiers are tightly "
        "clustered. Their F1-scores span the range from 0.468 to 0.509 and their ROC-AUC values the "
        "range from 0.715 to 0.733. Against cross-validation standard deviations of between 0.02 and "
        "0.04, differences of this size are not statistically meaningful. The result reproduces the "
        "central finding of Lessmann and colleagues, that most reasonable classifiers are "
        "indistinguishable on these data, and it means that the identification of Gradient Boosting as "
        "the best model on KC1 should be read as membership of the leading group rather than as a "
        "demonstrated superiority.")
    b.p("The only classifier that separates clearly from the rest is the single Decision Tree, whose "
        "F1-score of 0.425 and ROC-AUC of 0.654 are appreciably lower. This is the expected "
        "consequence of the high variance of an unaggregated tree, and it is precisely the weakness "
        "that Random Forest and Gradient Boosting are designed to remedy. That both ensembles built "
        "from such trees outperform the individual tree by a clear margin is a direct confirmation of "
        "the value of ensembling on this problem.")
    b.p("The second observation is that the models divide into two distinct operating profiles, which "
        "Figure 15.5 makes visible and the confusion matrices of Figure 15.8 make concrete.")
    b.bullets([
        "The conservative models, Gradient Boosting and Random Forest, achieve the highest accuracy "
        "(0.751 and 0.743), the highest precision (0.509 and 0.492), the highest Matthews correlation "
        "(0.342 and 0.327) and the lowest false-alarm rates (0.167 and 0.178). They detect about half "
        "of the defective modules.",
        "The sensitive models, the Multi-Layer Perceptron, the Support Vector Machine, Logistic "
        "Regression and Naive Bayes, detect between 67.8 and 74.6 per cent of defective modules but "
        "raise false alarms on between 33.9 and 43.7 per cent of clean ones.",
    ])
    b.p("Neither profile is intrinsically superior; the choice between them is an economic decision "
        "that depends on the relative cost of a defect that escapes to the customer and an inspection "
        "that finds nothing. In safety-critical development, where an escaped defect may be "
        "catastrophic, the sensitive profile is preferable. Where review capacity is the binding "
        "constraint, the conservative profile wastes less of it. Section 15.6 shows that a single model "
        "can be moved between these profiles by adjusting its decision threshold, so the choice need "
        "not be made by selecting a different algorithm.")
    b.p("Figure 15.6 shows the receiver operating characteristic curves. Their near-coincidence is the "
        "graphical expression of the clustering noted above: across the whole range of operating "
        "points, seven of the models are hard to separate. Figure 15.7 shows the precision-recall "
        "curves, which are more informative under imbalance because they ignore the true negatives "
        "that dominate the confusion matrix. No model achieves a precision above approximately 0.5 at "
        "a recall of 0.5, against a baseline precision of 0.253 that a random ranking would give.")
    b.figure(FIG / "fig7_06_kc1_roc_curves.png", "15.6",
             "Receiver operating characteristic curves on the KC1 test set", width_in=4.9)
    b.figure(FIG / "fig7_07_kc1_pr_curves.png", "15.7",
             "Precision-recall curves on the KC1 test set", width_in=4.9)
    b.figure(FIG / "fig7_08_kc1_confusion_matrices.png", "15.8",
             "Confusion matrices of the eight classifiers on the KC1 test set")
    b.p("The confusion matrices quantify the trade-off exactly. Gradient Boosting produces 30 true "
        "positives, 29 false positives and 29 false negatives: it finds half the defects and wastes "
        "half of the inspections it triggers. The Multi-Layer Perceptron produces 44 true positives, "
        "76 false positives and 15 false negatives: it finds three-quarters of the defects but two "
        "inspections in three are fruitless.")
    b.figure(FIG / "fig7_09_kc1_cv_f1_boxplot.png", "15.9",
             "Distribution of cross-validated F1-score across folds (KC1)", width_in=5.4)
    b.p("Figure 15.9 displays the fold-to-fold variability that underlies the means of Table 15.3, and "
        "it is the strongest argument against over-interpreting the ranking: the boxes of the leading "
        "models overlap substantially.")

    b.h3("15.2.2  Feature importance")
    b.p("Figure 15.10 shows the impurity-based feature importances of the Random Forest. Halstead "
        "difficulty, the counts of distinct operands and operators, and the number of executable lines "
        "dominate, which agrees with the correlation analysis of Section 15.1 and provides independent "
        "confirmation from a multivariate model. The caution stated earlier applies with full force "
        "here: because the Halstead measures are near-duplicates of one another, the importance "
        "attributable to the underlying construct is divided among them, and the ranking among "
        "individual collinear metrics should not be regarded as stable.")
    b.figure(FIG / "fig7_10_kc1_feature_importance.png", "15.10",
             "Fifteen most important features according to the Random Forest (KC1)", width_in=5.0)

    # ---------------- 15.3 all datasets ----------------
    b.h2("15.3  Results Across All Four Datasets (RQ2)")
    b.p("Table 15.4 summarises the F1-score and ROC-AUC of every model on every dataset, and Figures "
        "15.11 and 15.12 present the same information as heat maps.")
    b.table("15.4", "F1-score and ROC-AUC on the hold-out set of each dataset",
            ["Classifier", "KC1 F1 / AUC", "JM1 F1 / AUC", "PC1 F1 / AUC", "CM1 F1 / AUC"],
            [["Gradient Boosting", "0.509 / 0.733", "0.410 / 0.709", "0.333 / 0.858", "0.400 / 0.795"],
             ["k-Nearest Neighbours", "0.507 / 0.729", "0.419 / 0.664", "0.273 / 0.688", "0.359 / 0.793"],
             ["SVM (RBF)", "0.506 / 0.720", "0.430 / 0.688", "0.222 / 0.817", "0.381 / 0.711"],
             ["Logistic Regression", "0.503 / 0.720", "0.446 / 0.714", "0.250 / 0.801", "0.357 / 0.739"],
             ["Random Forest", "0.500 / 0.733", "0.461 / 0.717", "0.273 / 0.779", "0.143 / 0.778"],
             ["MLP (Neural Network)", "0.492 / 0.727", "0.427 / 0.681", "0.278 / 0.855", "0.258 / 0.705"],
             ["Gaussian Naive Bayes", "0.468 / 0.715", "0.416 / 0.679", "0.327 / 0.793", "0.323 / 0.752"],
             ["Decision Tree", "0.425 / 0.654", "0.429 / 0.681", "0.267 / 0.643", "0.261 / 0.676"]],
            col_widths=[1.5, 1.2, 1.2, 1.2, 1.2], font_size=10)
    b.figure(FIG / "fig7_11_cross_dataset_f1.png", "15.11",
             "F1-score of every classifier on every dataset")
    b.figure(FIG / "fig7_12_cross_dataset_roc_auc.png", "15.12",
             "ROC-AUC of every classifier on every dataset")
    b.table("15.5", "Mean rank of each classifier by F1-score across the four datasets",
            ["Rank", "Classifier", "Mean rank"],
            [["1", "Gradient Boosting", "2.75"], ["2", "k-Nearest Neighbours", "3.88"],
             ["3", "SVM (RBF)", "4.00"], ["4", "Logistic Regression", "4.25"],
             ["5", "Random Forest", "4.62"], ["6", "Gaussian Naive Bayes", "5.25"],
             ["6", "MLP (Neural Network)", "5.25"], ["8", "Decision Tree", "6.00"]],
            col_widths=[0.8, 2.6, 1.2], font_size=11)

    b.h3("15.3.1  Analysis")
    b.p("Gradient Boosting is the most consistent performer. It attains the best F1-score on three of "
        "the four datasets and the best mean rank of 2.75. Random Forest is strongest on JM1, which "
        "with 7,720 modules is by a wide margin the largest dataset; this is consistent with the "
        "theoretical expectation that the variance reduction obtained by bagging becomes more "
        "effective as the number of bootstrap samples that can be drawn from the data increases.")
    b.p("The most striking single result in the table is the failure of Random Forest on CM1, where "
        "its F1-score of 0.143 places it last. This is not evidence that Random Forest is unsuitable "
        "for small datasets in general. The CM1 test partition contains only eight defective modules, "
        "so each one that is correctly identified changes recall by 12.5 percentage points; Random "
        "Forest identified one of the eight. Estimates obtained from eight positive instances are "
        "subject to very large sampling error, and the CM1 column should be read as indicative rather "
        "than as a reliable ranking. The same caution applies, though less severely, to PC1, whose "
        "test partition contains eleven defective modules.")
    b.p("A clear and systematic pattern relates performance to class balance. The best achievable "
        "F1-score falls from 0.509 on KC1, where 25.3 per cent of modules are defective, to 0.333 on "
        "PC1, where 8.1 per cent are. Yet PC1 simultaneously produces the highest ROC-AUC of any "
        "dataset, at 0.858. The two measures are not in conflict; they answer different questions. "
        "ROC-AUC asks whether the model ranks defective modules above clean ones, and is computed from "
        "rates within each class separately, so it is unaffected by how rare the positive class is. "
        "The F1-score depends on precision, and precision is bounded by prevalence: when only eight "
        "per cent of modules are defective, even a well-ranked list yields many false positives near "
        "the top. The practical lesson, and one of the more valuable findings of this study, is that a "
        "high ROC-AUC must not be read as evidence that a defect predictor will be efficient in "
        "deployment on a code base with a low defect rate.")
    b.p("The Decision Tree is last or near-last on every dataset, and Gradient Boosting is in the "
        "leading group on every dataset. These two facts are the most robust conclusions that can be "
        "drawn from Table 15.4.")
    b.p("Figures 15.13 to 15.15 present the per-dataset detail for JM1, PC1 and CM1 respectively, and "
        "the corresponding numerical tables are given in Section 15.9.")
    b.figure(FIG / "fig_jm1_roc_curves.png", "15.13",
             "Receiver operating characteristic curves on the JM1 test set", width_in=4.6)
    b.figure(FIG / "fig_pc1_roc_curves.png", "15.14",
             "Receiver operating characteristic curves on the PC1 test set", width_in=4.6)
    b.figure(FIG / "fig_cm1_roc_curves.png", "15.15",
             "Receiver operating characteristic curves on the CM1 test set", width_in=4.6)

    # ---------------- 15.4 learning curves ----------------
    b.h2("15.4  Learning Curves and the Performance Ceiling")
    b.p("A natural question raised by the modest absolute performance is whether more training data "
        "would help. Figure 15.16 answers it directly. It plots, for the two ensemble methods, the "
        "F1-score achieved on the training data and the cross-validated F1-score, as the number of "
        "training modules increases from 110 to 743.")
    b.figure(FIG / "fig_learning_curve.png", "15.16",
             "Learning curves for the two ensemble methods on KC1")
    b.p("Two features of these curves are informative. The first is the size of the gap between the "
        "two lines. Random Forest achieves an F1-score close to 0.97 on data it has seen and "
        "approximately 0.50 on data it has not; Gradient Boosting begins at 1.00 on training data and "
        "declines to approximately 0.78 as more data forces it to generalise. A gap of this magnitude "
        "indicates high variance: both models are capable of fitting the training set almost "
        "perfectly, which means the limiting factor is not the capacity of the model.")
    b.p("The second feature is the shape of the validation curve. It rises steeply at first, from "
        "approximately 0.38 to approximately 0.45 as the training set grows from 110 to 300 modules, "
        "and then flattens, gaining only about 0.05 over the remaining 440 modules. Extrapolating the "
        "trend, doubling the size of KC1 would be expected to improve the F1-score by a few hundredths "
        "at most. The conclusion is that the ceiling on performance is imposed by the information "
        "content of the static metrics themselves, not by the quantity of labelled data available. "
        "This supports the argument advanced in the literature that substantial improvement requires "
        "different features, such as process and change-history metrics, rather than more rows of the "
        "same features, and it is the principal justification for the first item of the future scope "
        "in Chapter 19.")

    # ---------------- 15.5 ablation ----------------
    b.h2("15.5  Effect of Class Balancing (RQ3)")
    b.p("To isolate the contribution of synthetic over-sampling, the complete experiment was repeated "
        "on KC1 with balancing disabled and every other setting, including the random seed, held "
        "constant. Table 15.6 reports both conditions.")
    b.table("15.6", "Effect of over-sampling on KC1 (values given as: without balancing → with SMOTE)",
            ["Classifier", "Precision", "Recall", "F1", "Accuracy", "PF"],
            [["Logistic Regression", "1.000 → 0.400", "0.153 → 0.678", "0.265 → 0.503",
              "0.785 → 0.661", "0.000 → 0.345"],
             ["SVM (RBF)", "1.000 → 0.404", "0.153 → 0.678", "0.265 → 0.506",
              "0.785 → 0.665", "0.000 → 0.339"],
             ["MLP (Neural Network)", "0.727 → 0.367", "0.136 → 0.746", "0.229 → 0.492",
              "0.768 → 0.609", "0.017 → 0.437"],
             ["Gradient Boosting", "0.778 → 0.509", "0.237 → 0.509", "0.364 → 0.509",
              "0.790 → 0.751", "0.023 → 0.167"],
             ["Random Forest", "0.615 → 0.492", "0.271 → 0.509", "0.377 → 0.500",
              "0.773 → 0.743", "0.058 → 0.178"],
             ["k-Nearest Neighbours", "0.647 → 0.434", "0.373 → 0.610", "0.473 → 0.507",
              "0.790 → 0.700", "0.069 → 0.270"],
             ["Decision Tree", "0.583 → 0.397", "0.356 → 0.458", "0.442 → 0.425",
              "0.773 → 0.687", "0.086 → 0.236"],
             ["Gaussian Naive Bayes", "0.376 → 0.357", "0.695 → 0.678", "0.488 → 0.468",
              "0.631 → 0.609", "0.391 → 0.414"]],
            col_widths=[1.5, 1.05, 1.05, 1.05, 1.05, 1.05], font_size=10)
    b.figure(FIG / "fig_ablation_kc1.png", "15.17",
             "Performance on KC1 with class balancing disabled")

    b.h3("15.5.1  Analysis")
    b.p("Without balancing, the margin-based and gradient-based models are close to useless as "
        "detectors. Logistic Regression and the Support Vector Machine each flag only nine of the "
        "fifty-nine defective modules in the test set, a recall of 0.153. Both achieve a precision of "
        "exactly 1.000 and a false-alarm rate of exactly 0.000, which at first sight appears to be an "
        "excellent result and is in fact the signature of a degenerate model: the classifier has "
        "learned to predict the majority class almost everywhere, and the few positive predictions it "
        "does make are the handful of extreme instances about which there is no doubt. The "
        "accompanying accuracy of 0.785 is barely above the 0.747 that a model predicting no defects "
        "at all would achieve on this test set. This single comparison is the clearest possible "
        "demonstration of why accuracy must not be used as the headline measure for this problem.")
    b.p("Over-sampling changes the picture completely. The recall of both models rises from 0.153 to "
        "0.678, an improvement of more than fourfold, and their F1-scores approximately double, from "
        "0.265 to 0.503 and 0.506. The cost is a fall in accuracy of about twelve percentage points "
        "and a rise in the false-alarm rate from zero to approximately 0.34. Whether this exchange is "
        "worthwhile is an economic question, but for any organisation in which a missed defect costs "
        "more than a fruitless inspection, it clearly is.")
    b.p("The effect is not uniform across families of classifier, and the pattern is itself "
        "informative.")
    b.bullets([
        "The margin-based and neural models gain most, because their loss functions are dominated by "
        "the majority class when the data is imbalanced. Their F1-scores improve by between 0.24 and "
        "0.26.",
        "The ensembles gain moderately, improving their F1-scores by between 0.12 and 0.15, and they "
        "retain low false-alarm rates even after balancing. Gradient Boosting improves from 0.364 to "
        "0.509 while its false-alarm rate rises only from 0.023 to 0.167.",
        "The Decision Tree and Gaussian Naive Bayes are the two exceptions, and both become slightly "
        "worse. For Naive Bayes the explanation is that its class priors already produce a "
        "high-recall, low-precision model: its unbalanced recall of 0.695 is the highest of any model "
        "in the unbalanced condition, so there is nothing for over-sampling to add. This reproduces "
        "the observation of Menzies and colleagues that Naive Bayes is intrinsically well suited to "
        "imbalanced defect data.",
    ])
    b.p("The answer to RQ3 is therefore that synthetic over-sampling produces a large improvement in "
        "recall and F1-score for most classifiers, at a cost in precision, accuracy and false-alarm "
        "rate; that the improvement is largest for margin-based and neural models and smallest, or "
        "slightly negative, for models that are already biased towards the minority class; and that it "
        "should be adopted as the default for recall-oriented defect prediction. This reproduces the "
        "conclusion of Tantithamthavorn and colleagues on a much larger collection of datasets.")

    # ---------------- 15.6 threshold ----------------
    b.h2("15.6  Sensitivity to the Decision Threshold")
    b.p("The classifications discussed so far were obtained by applying the conventional threshold of "
        "0.5 to the predicted probability. That value has no special status; it is a convention, not a "
        "property of the problem. Figure 15.18 shows how precision, recall and F1-score vary as the "
        "threshold is moved across its full range, for Gradient Boosting on KC1.")
    b.figure(FIG / "fig_threshold.png", "15.18",
             "Precision, recall and F1-score as a function of the decision threshold (KC1)",
             width_in=5.4)
    b.p("The curves behave as theory requires: raising the threshold makes the model more conservative, "
        "increasing precision and decreasing recall, while lowering it has the opposite effect. The "
        "F1-optimal threshold on this test set is 0.51, which yields an F1-score of 0.522, marginally "
        "better than the 0.509 obtained at the conventional 0.5. The important observation is not this "
        "negligible gain but the shape of the curve: the F1-score is relatively flat between about 0.35 "
        "and 0.60, so the exact value chosen is not critical, whereas recall changes substantially "
        "across the same interval.")
    b.p("This has a practical consequence that deserves emphasis. The distinction drawn in Section "
        "15.2 between conservative and sensitive models is not a fixed property of the algorithms. A "
        "single trained Gradient Boosting model can be operated at high recall simply by lowering its "
        "threshold, at some cost in precision. The choice of operating point is a policy decision "
        "about the relative cost of the two kinds of error, and it can be made after the model has "
        "been trained and without retraining it. The prediction script accordingly exposes the "
        "threshold as a command-line option.")

    # ---------------- 15.7 tuning + data variant ----------------
    b.h2("15.7  Supplementary Experiments")
    b.h3("15.7.1  Effect of the dataset variant")
    b.p("To quantify the effect of the data-quality problem documented by Shepperd and colleagues, the "
        "KC1 experiment was repeated on the original, uncleaned file. After removal of exact "
        "duplicates the original file yields 1,210 modules with a defect rate of 26.0 per cent, "
        "compared with 1,162 modules at 25.3 per cent for the cleaned version. Measured ROC-AUC on the "
        "uncleaned data ranged from 0.62 to 0.67 across the eight classifiers, against 0.65 to 0.73 on "
        "the cleaned data. The two sets of figures are not directly comparable, because the underlying "
        "populations differ, and the comparison should be understood as an illustration of the "
        "sensitivity of published results to the version of the data used rather than as a controlled "
        "experiment. It reinforces the recommendation that only the cleaned versions should be used "
        "and that results quoted from older studies on the original files should not be treated as "
        "directly comparable with results obtained on the cleaned ones.")
    b.h3("15.7.2  Effect of hyper-parameter tuning")
    b.p("A randomised search over fifteen candidate configurations, optimising the F1-score under "
        "cross-validation, is implemented for Random Forest, Gradient Boosting, the Support Vector "
        "Machine, Logistic Regression and k-nearest neighbours. Enabling it changed the F1-scores by "
        "less than the fold-to-fold standard deviation reported in Table 15.3 and did not alter the "
        "ordering of the leading group. The headline results in this report therefore use the "
        "literature-standard default settings, which has the additional advantage that no model "
        "benefits from more optimisation effort than another.")

    # ---------------- 15.8 comparison with literature ----------------
    b.h2("15.8  Comparison with Published Results")
    b.table("15.7", "Comparison with results published in the literature",
            ["Study", "Data version", "Reported finding", "This project"],
            [["Menzies et al. (2007)", "Original MDP",
              "Naive Bayes with log transform: mean PD 0.71 at PF 0.25",
              "Naive Bayes: PD 0.678 at PF 0.414 (KC1); PD 0.727 at PF 0.240 (PC1)"],
             ["Lessmann et al. (2008)", "Original MDP",
              "Most classifiers statistically indistinguishable on AUC; RF among the best",
              "Seven of eight models within 0.02 AUC on KC1; RF and GB tied at 0.733"],
             ["Ghotra et al. (2015)", "Cleaned D″",
              "Ensembles occupy the top statistical group; AUC typically 0.70 to 0.80",
              "GB best mean rank; AUC 0.709 to 0.858 across the four datasets"],
             ["Shepperd et al. (2013)", "Original versus cleaned",
              "Results differ materially between the two versions",
              "KC1 AUC 0.62 to 0.67 uncleaned against 0.65 to 0.73 cleaned"],
             ["Tantithamthavorn et al. (2020)", "101 datasets",
              "Rebalancing improves recall and AUC at a cost in precision",
              "SMOTE raises LR and SVM recall from 0.153 to 0.678; precision falls from 1.000 to 0.40"]],
            col_widths=[1.3, 1.0, 2.0, 1.95], font_size=9)
    b.p("The results obtained here are consistent with the qualitative findings of all five studies. "
        "The absolute figures fall within the range reported for the cleaned data and below the range "
        "commonly reported for the original data, which is the expected direction once duplicated "
        "records are removed and information leakage is eliminated. The reproduction may therefore be "
        "regarded as successful.")

    # ---------------- 15.9 full tables ----------------
    b.h2("15.9  Complete Result Tables for the Remaining Datasets")
    b.table("15.8", "Hold-out test performance on JM1 (1,544 modules, 322 defective)",
            METRIC_HDR, _rows("JM1"), col_widths=METRIC_W, font_size=10)
    b.table("15.9", "Hold-out test performance on PC1 (136 modules, 11 defective)",
            METRIC_HDR, _rows("PC1"), col_widths=METRIC_W, font_size=10)
    b.table("15.10", "Hold-out test performance on CM1 (66 modules, 8 defective)",
            METRIC_HDR, _rows("CM1"), col_widths=METRIC_W, font_size=10)
    b.figure(FIG / "fig_jm1_confusion_matrices.png", "15.19",
             "Confusion matrices on the JM1 test set")
    b.figure(FIG / "fig_jm1_feature_importance.png", "15.20",
             "Most important features according to the Random Forest (JM1)", width_in=4.8)
    b.figure(FIG / "fig_pc1_feature_importance.png", "15.21",
             "Most important features according to the Random Forest (PC1)", width_in=4.8)

    # ---------------- 15.10 threats ----------------
    b.h2("15.10  Threats to Validity")
    b.p("The findings of any empirical study are conditional on the design of that study. The "
        "principal threats to the validity of the present results are recorded here under the standard "
        "four headings.")
    b.h3("15.10.1  Construct validity")
    b.p("Construct validity concerns whether the quantities measured correspond to the concepts of "
        "interest. Static code metrics are a proxy for defect-proneness, not a measure of it, and the "
        "label records only that a defect was reported against a module, which depends on the testing "
        "and reporting practices of the project. A module labelled clean may contain undiscovered "
        "defects. The measured performance is therefore a lower bound in one sense and an "
        "overstatement in another, and the direction of the net bias is unknown.")
    b.h3("15.10.2  Internal validity")
    b.p("Internal validity concerns whether the observed differences are caused by the factors "
        "identified. Default hyper-parameters were used for all models; although Section 15.7 reports "
        "that tuning did not change the ordering, a more extensive search might. A single random seed "
        "was used for the headline results, and although cross-validation standard deviations are "
        "reported, repeating the entire experiment over several seeds would give firmer confidence "
        "intervals. The configuration supports this and it is recommended as an extension.")
    b.h3("15.10.3  External validity")
    b.p("External validity concerns the generality of the conclusions. The four systems studied are "
        "NASA flight and ground software written in C and C++ during the 1990s and 2000s. Modern web, "
        "mobile and open-source development differs in language, in architecture, in team structure "
        "and in defect-reporting culture, and the conclusions should not be assumed to transfer "
        "without re-validation. The consistency of the findings across four systems of differing size "
        "and defect rate provides some reassurance, but all four come from a single organisation.")
    b.h3("15.10.4  Conclusion validity")
    b.p("Conclusion validity concerns whether the statistical treatment supports the claims made. The "
        "test partitions of PC1 and CM1 contain only eleven and eight defective modules respectively, "
        "so the measures derived from them have wide confidence intervals and the rankings on those "
        "two datasets are unreliable. No formal significance test was applied to the differences "
        "between classifiers; instead, the fold-to-fold standard deviations are reported and "
        "differences smaller than those deviations are explicitly declined as evidence. A Scott-Knott "
        "effect-size difference test, as used by Ghotra and colleagues, would place this reasoning on "
        "a firmer footing and is recommended in Chapter 19.")


# =========================================================================== #
def ch16_coding(b: ReportBuilder, detail: str = "standard") -> None:
    """Source listings. `detail` selects how much code is reproduced:
    brief    - configuration and the preprocessing pipeline only
    standard - the above plus the classifier registry and the experiment driver
    full     - every significant source file
    """
    b.chapter("Coding")
    b.p("This chapter reproduces the source code of the components in which the essential logic of "
        "the system resides. The complete source, comprising approximately 1,400 lines across "
        "fourteen files, is submitted with this report on the accompanying media; the listings below "
        "are those needed to follow the argument of Chapters 10 and 15, and are given in the order in "
        "which the components execute.")

    def src(rel: str, start: int = 0, end: int | None = None) -> str:
        lines = (PROJECT_ROOT / rel).read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[start:end])

    b.h2("16.1  Configuration File (config.yaml)")
    b.p("Every experimental setting is declared in this single file, so that the dataset, the "
        "balancing strategy, the cross-validation design, the list of classifiers and the random seed "
        "can all be varied without editing any source code. This is what makes the ablation study of "
        "Section 15.5 a change of one line rather than a change of program.")
    b.code(src("config.yaml", 6))

    b.h2("16.2  Preprocessing and Pipeline Construction (sdp/preprocessing.py)")
    b.p("This is the most important listing in the report. The function build_model_pipeline is what "
        "structurally guarantees the absence of information leakage. Because the imputer, the "
        "logarithmic transformer, the scaler and the over-sampler are steps of a pipeline object "
        "rather than operations applied directly to the data frame, scikit-learn refits them inside "
        "every cross-validation fold using only that fold’s training rows. Note in particular "
        "that the steps are kept flat rather than nested, because the resampling-aware pipeline "
        "rejects a pipeline used as an intermediate step.")
    b.code(src("sdp/preprocessing.py", 28))

    b.h2("16.3  Classifier Registry (sdp/models.py)")
    b.p("The registry maps a short name to a factory function that returns a configured estimator. "
        "Each factory receives the random seed and the balancing mode, so cost-sensitive weighting is "
        "applied uniformly wherever the algorithm supports it. Adding a classifier to the study "
        "requires one entry here and no change whatever to the training loop, which is the Open/Closed "
        "principle applied to an experimental code base.")
    b.code(src("sdp/models.py", 16, 75))

    if detail in ("standard", "full"):
        b.h2("16.4  Metric Computation (sdp/evaluate.py)")
        b.p("The seven performance measures are computed here from the true labels, the predicted "
            "labels and the continuous scores. The helper that obtains a score works for any "
            "estimator, whether it exposes predicted probabilities or only a decision function, which "
            "is what allows the eight algorithms to be treated identically.")
        b.code(src("sdp/evaluate.py", 24, 76))

        b.h2("16.5  Main Experiment Driver (scripts/run_pipeline.py)")
        b.p("The function that executes the complete experiment for one dataset: load, clean, split, "
            "and then for each classifier cross-validate, fit, evaluate, persist and plot.")
        b.code(src("scripts/run_pipeline.py", 52, 122))

    if detail in ("standard", "full"):
        b.h2("16.6  Web Interface: Model Loading and Halstead Derivation "
             "(app/streamlit_app.py)")
        b.p("The cached loaders and the function that derives the dependent Halstead measures "
            "from the four basic counts. The caching decorators matter: without them the "
            "pipeline would be deserialised and the training data reloaded on every keystroke, "
            "because Streamlit re-executes the script from the top on each interaction.")
        b.code(src("app/streamlit_app.py", 85, 127))

        b.h2("16.7  Web Interface: Form Construction and Prediction "
             "(app/streamlit_app.py)")
        b.p("The metric-entry form and the prediction block. Note the assignment into the "
            "session state before the widgets are created, which is what allows the preset "
            "selector to change values the user has already seen.")
        b.code(src("app/streamlit_app.py", 205, 262))

    if detail == "full":
        b.h2("16.8  Dataset Acquisition and ARFF Parsing (sdp/data_loader.py)")
        b.code(src("sdp/data_loader.py", 74, 153))

        b.h2("16.9  Prediction Interface (scripts/predict.py)")
        b.code(src("scripts/predict.py", 16, 59))

        b.h2("16.10  Automated Test Suite (tests/test_pipeline.py)")
        b.code(src("tests/test_pipeline.py", 38, 119))


# =========================================================================== #
def ch17_dataset_tables(b: ReportBuilder) -> None:
    b.chapter("Dataset Tables")
    b.p("This chapter documents the structure of the data on which the system operates. In a "
        "conventional information system this chapter would describe the tables of a relational "
        "database; here the equivalent role is played by the attribute structure of the benchmark "
        "files and by the tabular artefacts that the system produces.")

    b.h2("17.1  Structure of the Input Files")
    b.p("Each dataset is distributed as a file in the Attribute-Relation File Format, a plain-text "
        "format consisting of a header that declares the relation name and the attributes with their "
        "types, followed by a data section containing one comma-separated record per module. Table "
        "17.1 documents the twenty-one attributes common to all four datasets.")
    b.table("17.1", "Attributes of the KC1 and JM1 datasets",
            ["#", "Attribute", "Type", "Family", "Meaning"],
            [["1", "LOC_BLANK", "Numeric", "Size", "Count of blank lines"],
             ["2", "BRANCH_COUNT", "Numeric", "McCabe", "Number of branches in the flow graph"],
             ["3", "LOC_CODE_AND_COMMENT", "Numeric", "Size", "Lines containing both code and a comment"],
             ["4", "LOC_COMMENTS", "Numeric", "Size", "Count of comment lines"],
             ["5", "CYCLOMATIC_COMPLEXITY", "Numeric", "McCabe", "Independent paths, v(G) = e − n + 2p"],
             ["6", "DESIGN_COMPLEXITY", "Numeric", "McCabe", "Complexity of inter-module calls"],
             ["7", "ESSENTIAL_COMPLEXITY", "Numeric", "McCabe", "Degree of unstructuredness"],
             ["8", "LOC_EXECUTABLE", "Numeric", "Size", "Count of executable statements"],
             ["9", "HALSTEAD_CONTENT", "Numeric", "Halstead", "Intelligence content of the module"],
             ["10", "HALSTEAD_DIFFICULTY", "Numeric", "Halstead", "D = (n1 / 2) × (N2 / n2)"],
             ["11", "HALSTEAD_EFFORT", "Numeric", "Halstead", "E = D × V"],
             ["12", "HALSTEAD_ERROR_EST", "Numeric", "Halstead", "Estimated delivered bugs, B = V / 3000"],
             ["13", "HALSTEAD_LENGTH", "Numeric", "Halstead", "N = N1 + N2"],
             ["14", "HALSTEAD_LEVEL", "Numeric", "Halstead", "L = 1 / D"],
             ["15", "HALSTEAD_PROG_TIME", "Numeric", "Halstead", "T = E / 18 seconds"],
             ["16", "HALSTEAD_VOLUME", "Numeric", "Halstead", "V = N × log2(n1 + n2)"],
             ["17", "NUM_OPERANDS", "Numeric", "Halstead", "Total operand occurrences, N2"],
             ["18", "NUM_OPERATORS", "Numeric", "Halstead", "Total operator occurrences, N1"],
             ["19", "NUM_UNIQUE_OPERANDS", "Numeric", "Halstead", "Distinct operands, n2"],
             ["20", "NUM_UNIQUE_OPERATORS", "Numeric", "Halstead", "Distinct operators, n1"],
             ["21", "LOC_TOTAL", "Numeric", "Size", "Total lines of code"],
             ["22", "Defective", "Nominal {Y, N}", "Target", "Whether a defect was reported"]],
            col_widths=[0.35, 1.85, 0.95, 0.8, 2.3], font_size=9)
    b.p("The PC1 and CM1 files contain sixteen further attributes, comprising additional density "
        "measures such as condition count, decision density, design density and essential density, "
        "counts of called and calling modules, parameter counts, maintenance-severity measures and "
        "node and edge counts of the control-flow graph. The system handles the differing attribute "
        "sets automatically, since the feature list is derived from the file header rather than being "
        "hard-coded.")

    b.h2("17.2  Sample Records")
    b.p("Table 17.2 reproduces three records from the KC1 file, abbreviated to the first nine "
        "attributes and the target, to illustrate the form of the data.")
    b.table("17.2", "Sample records from the KC1 dataset (first nine attributes and the target)",
            ["LOC_BLANK", "BRANCH", "L_C_C", "LOC_COM", "CYCLO", "DESIGN", "ESSENT", "LOC_EXEC",
             "H_CONTENT", "Defective"],
            [["0", "1", "0", "0", "1", "1", "1", "3", "11.58", "N"],
             ["6", "9", "0", "2", "5", "3", "1", "35", "45.32", "Y"],
             ["1", "3", "0", "1", "2", "2", "1", "9", "22.14", "N"]],
            col_widths=[0.72, 0.6, 0.5, 0.65, 0.55, 0.62, 0.6, 0.66, 0.75, 0.7], font_size=9)

    b.h2("17.3  Structure of the Generated Output Tables")
    b.p("The system produces three tabular artefacts per dataset, documented in Table 17.3.")
    b.table("17.3", "Structure of the tables generated by the system",
            ["Artefact", "One row per", "Principal columns"],
            [["test_metrics.csv", "Classifier",
              "model, accuracy, precision, recall, f1, roc_auc, mcc, balanced_accuracy, pf, "
              "tp, fp, fn, tn, cv_*_mean, cv_*_std, train_time_s"],
             ["summary_statistics.csv", "Metric",
              "count, mean, std, min, quartiles, max, skewness, missing, corr_with_target"],
             ["summary_all_datasets.csv", "Dataset and classifier",
              "dataset, model and every measure above, for cross-dataset comparison"],
             ["Scored output of predict.py", "Module scored",
              "All input metric columns, defect_probability, predicted_defective"]],
            col_widths=[1.5, 1.1, 3.6], font_size=10)

    b.h2("17.4  Provenance Record")
    b.p("Each execution additionally writes a JSON summary recording the dataset used, the best model "
        "identified, the sizes of the training and test partitions, the complete feature list, the "
        "balancing strategy and the random seed. This record is what allows a set of results to be "
        "traced back to the exact configuration that produced it, and it is the mechanism by which the "
        "reproducibility claim of Section 10.8 is made auditable.")


# =========================================================================== #
def ch18_conclusion(b: ReportBuilder) -> None:
    b.chapter("Conclusion")
    b.p("This project set out to survey the literature on machine-learning-based software defect "
        "prediction and to reproduce, under a methodologically sound protocol, the standard "
        "classifier-comparison study on the benchmark datasets of the NASA Metrics Data Program. Both "
        "objectives have been met, and the two course outcomes of the Minor Project, namely the "
        "identification of a research problem through a literature survey and the analysis and "
        "reproduction of an existing solution, are satisfied by the work reported here.")
    b.p("A complete software system was designed, implemented and tested. It comprises an installable "
        "Python package of eight modules, five command-line tools, a configuration-driven experiment "
        "design and an automated test suite of nine cases, all of which pass. The system downloads the "
        "cleaned benchmark datasets, characterises them through exploratory analysis, applies a "
        "preprocessing pipeline that is structurally incapable of leaking information from test data "
        "into training, trains and cross-validates eight classification algorithms, and reports seven "
        "complementary performance measures together with the figures required to interpret them.")
    b.p("The principal findings are the following.")
    b.numbered([
        "Concerning the metrics, Halstead difficulty, the counts of distinct operators and operands and "
        "the measures of module size are the attributes most strongly associated with "
        "defect-proneness. The association is positive in every case but modest in magnitude: the "
        "strongest single correlation observed was 0.303. The metrics are also highly collinear, so "
        "the effective dimensionality of the problem is considerably lower than the nominal count of "
        "twenty-one or thirty-seven attributes suggests.",
        "Concerning the classifiers, Gradient Boosting was the most consistent performer, achieving "
        "the best F1-score on KC1, PC1 and CM1 and the best mean rank of 2.75 across the four "
        "datasets. Random Forest was strongest on JM1, the largest dataset. Seven of the eight "
        "algorithms, however, lie within the fold-to-fold variability of one another, so the field "
        "should be understood as a leading group rather than a strict ordering. The single Decision "
        "Tree was reliably the weakest model, and the margin by which both ensembles exceed it is a "
        "direct demonstration of the value of ensembling on this problem.",
        "Concerning class imbalance, synthetic minority over-sampling is decisive for recall-oriented "
        "prediction. Without it, Logistic Regression and the Support Vector Machine detected only nine "
        "of the fifty-nine defective modules in the KC1 test set, a recall of 0.153, while reporting a "
        "precision of 1.000 and an accuracy of 0.785 that a naive reading would mistake for excellent "
        "performance. With over-sampling, recall rose to 0.678 and the F1-score approximately doubled. "
        "The benefit is largest for margin-based and neural models and negligible for Naive Bayes, "
        "whose priors already favour the minority class.",
        "Concerning the limits of the approach, learning-curve analysis established that the ceiling "
        "on performance is set by the information content of static code metrics rather than by the "
        "quantity of labelled data. The validation curve flattens after approximately three hundred "
        "training modules while the training curve remains far above it, which is the signature of a "
        "problem in which additional rows of the same features cannot help.",
        "Concerning evaluation practice, the study demonstrated concretely that accuracy is misleading "
        "under imbalance, that a high ROC-AUC does not imply an efficient predictor when the positive "
        "class is rare, and that the choice between a conservative and a sensitive model is a policy "
        "decision that can be implemented by moving the decision threshold rather than by changing the "
        "algorithm.",
    ])
    b.p("The absolute performance obtained, with F1-scores between 0.333 and 0.509 and ROC-AUC between "
        "0.709 and 0.858, is consistent with results published on the cleaned datasets and lower than "
        "much of what has been published on the original files. That difference is itself a finding: "
        "it is the expected consequence of removing duplicated records and eliminating information "
        "leakage, and it supports the argument of Shepperd and colleagues that a substantial part of "
        "the earlier literature reports performance that cannot be attained in practice.")
    b.p("The wider conclusion is that defect prediction from static code metrics is genuinely useful "
        "but genuinely limited. A model that identifies half of the defective modules while raising "
        "false alarms on seventeen per cent of clean ones is far better than the uniform allocation of "
        "review effort that it replaces, and it is obtained at negligible computational cost from data "
        "the organisation already possesses. It is not, and does not claim to be, a substitute for "
        "testing.")


# =========================================================================== #
def ch19_future(b: ReportBuilder) -> None:
    b.chapter("Future Scope")
    b.p("The work reported here establishes a sound baseline and, in doing so, identifies a number of "
        "directions in which it could be extended. They are set out below in approximate order of the "
        "improvement each might be expected to deliver.")

    b.h2("19.1  Process and Change-History Metrics")
    b.p("This is the most promising direction, and it follows directly from the learning-curve "
        "analysis of Section 15.4, which showed that additional data of the same kind will not raise "
        "performance materially. Metrics derived from the version-control history of a project, such "
        "as the number of times a file has been modified, the number of distinct developers who have "
        "touched it, the size and frequency of recent changes, and the degree of ownership "
        "concentration, capture information about the process by which the code was produced that is "
        "entirely absent from its static structure. Several published studies report that such metrics "
        "outperform static metrics, and combining the two families is reported to be better still.")

    b.h2("19.2  Statistical Rigour in the Comparison")
    b.p("The present study reports fold-to-fold standard deviations and declines to interpret "
        "differences smaller than those deviations, but it applies no formal significance test. "
        "Repeating the entire experiment over a set of random seeds and applying a Scott-Knott "
        "effect-size difference test, as Ghotra and colleagues did, would partition the classifiers "
        "into statistically distinguishable groups and would place the ranking on a much firmer "
        "footing. The configuration already supports repeated cross-validation, so this extension "
        "requires analysis code rather than new infrastructure.")

    b.h2("19.3  Cost-Sensitive Threshold Optimisation")
    b.p("Section 15.6 showed that the operating point can be moved freely after training. A natural "
        "extension is to choose it by minimising an explicit cost function of the form C = c_fn × FN + "
        "c_fp × FP, where the two coefficients express the cost of an escaped defect and of a fruitless "
        "inspection respectively. An organisation able to estimate that ratio, even approximately, "
        "would obtain an operating point matched to its own economics rather than to the arbitrary "
        "convention of a 0.5 threshold.")

    b.h2("19.4  Cross-Project Prediction")
    b.p("Every model built here was trained and evaluated on a single project. The situation of "
        "greatest practical interest is the opposite one: a new project with no defect history at all. "
        "Cross-project defect prediction addresses this through transfer learning, domain adaptation "
        "and instance-weighting methods that adjust for the differing metric distributions of the "
        "source and target projects. The four datasets used here, differing as they do in language, "
        "size and defect rate, would form a reasonable initial test bed.")

    b.h2("19.5  Feature Engineering and Selection")
    b.p("The collinearity documented in Section 15.1 suggests that a reduced feature set might perform "
        "as well as the full one while being easier to interpret. Principal component analysis, "
        "correlation-based filtering and wrapper-based selection could all be evaluated. Derived "
        "ratios, such as comment density or complexity per line, may also carry information that the "
        "raw counts do not, since they separate the effect of size from the effect of structure.")

    b.h2("19.6  Modern and Larger Datasets")
    b.p("The NASA systems are old and come from a single organisation. Evaluating the same pipeline on "
        "the PROMISE collection assembled by Jureczko from open-source Java projects, and on defect "
        "datasets derived from issue trackers of active repositories, would establish whether the "
        "conclusions generalise beyond aerospace software written in C.")

    b.h2("19.7  Deep Learning on Source-Code Representations")
    b.p("Recent work applies convolutional and recurrent networks, and more recently transformer "
        "architectures, directly to the token stream or abstract syntax tree of a module, learning a "
        "representation rather than relying on hand-designed metrics. Such models can in principle "
        "capture semantic properties that no aggregate count can express. They require substantially "
        "more data than is available in the NASA datasets, so this direction would be pursued in "
        "conjunction with Section 19.6.")

    b.h2("19.8  Explainability")
    b.p("A developer asked to inspect a module is entitled to know why it was flagged. Shapley "
        "additive explanations decompose an individual prediction into per-feature contributions, and "
        "would allow the system to report, for example, that a particular module was flagged "
        "principally because of its unusually high Halstead difficulty relative to its size. This "
        "would materially improve the acceptability of the tool in practice.")

    b.h2("19.9  Deployment as a Development-Workflow Tool")
    b.p("The web interface described in Section 6.10 delivers the first stage of this: a trained model can now be applied to a module by anyone, without a terminal and without programming. Two steps remain before it is part of a working development process. The metrics must be produced automatically by a static-analysis tool rather than typed in, and the predictions must be delivered where the work happens rather than in a separate application.")
    b.p("The command-line prediction interface operates on a file of metrics. A production version "
        "would integrate with a static-analysis tool and a version-control system, compute the metrics "
        "for changed files automatically on each commit, and present the ranked risk list within the "
        "code-review interface or the continuous-integration report. The retraining of the model as "
        "new defect data accumulates could itself be scheduled automatically.")


# =========================================================================== #
def ch20_limitation(b: ReportBuilder) -> None:
    b.chapter("Limitation")
    b.p("Considerable effort has been directed at making this study methodologically sound and its "
        "software reliable and easy to operate. Limitations nevertheless remain, and they are stated "
        "here explicitly, both because honesty about them is a requirement of scientific reporting and "
        "because each indicates where a reader should be cautious in applying the conclusions.")

    b.h2("20.1  Limitations of the Data")
    b.bullets([
        "The four systems studied are NASA flight and ground software written in C and C++ during the "
        "1990s and 2000s. Conclusions drawn from them may not transfer to modern languages, "
        "architectures or development cultures.",
        "All four datasets originate from a single organisation with a single set of measurement and "
        "defect-reporting conventions, so the apparent agreement between them is weaker evidence of "
        "generality than four independently sourced datasets would be.",
        "The label records that a defect was reported against a module, not that the module is free of "
        "defects when unlabelled. Modules that were never exercised by testing appear as clean, which "
        "introduces label noise of unknown magnitude.",
        "The test partitions of PC1 and CM1 contain only eleven and eight defective modules "
        "respectively. Measures computed from so few positive instances have wide confidence "
        "intervals, and the model rankings on those two datasets are correspondingly unreliable.",
        "Only static code metrics were available. Process metrics, which the literature indicates are "
        "more predictive, are not present in these datasets.",
    ])

    b.h2("20.2  Limitations of the Method")
    b.bullets([
        "Default hyper-parameters were used for the headline results. Although the supplementary "
        "experiment of Section 15.7 found that tuning did not alter the ordering of the leading group, "
        "a more exhaustive search might.",
        "A single random seed governs the headline results. Fold-to-fold variability is reported, but "
        "the variability arising from the choice of the initial train-test split itself is not "
        "quantified.",
        "No formal statistical significance test was applied to the differences between classifiers. "
        "Differences smaller than the reported standard deviations are declined as evidence, which is "
        "a conservative but informal criterion.",
        "Only one resampling technique, SMOTE, was evaluated in depth. Borderline-SMOTE, ADASYN, "
        "random under-sampling and hybrid methods were not compared.",
        "Feature selection was not performed, so the study does not establish whether a smaller set of "
        "metrics would perform as well.",
    ])

    b.h2("20.3  Limitations of the Software")
    b.bullets([
        "The system operates on a file of precomputed metrics. It does not itself parse source code, "
        "so applying it to a new code base requires a separate static-analysis tool to produce the "
        "metric file in the expected format.",
        "The interface is a command-line one. A graphical or web interface would make the tool "
        "accessible to users who are not comfortable with a terminal.",
        "Cross-validation executes sequentially by default, because parallel execution of the kernel "
        "method proved unstable in worker processes on the development platform. On Linux the degree "
        "of parallelism can be raised through the configuration file, but the default setting is "
        "conservative.",
        "The trained models are serialised with joblib, which does not guarantee compatibility across "
        "major versions of scikit-learn. A model saved today may need to be retrained after a library "
        "upgrade; the cost of doing so is a few minutes.",
        "No provision is made for incremental retraining as new defect data arrives; the model must be "
        "rebuilt from the complete dataset.",
    ])

    b.h2("20.4  Limitations of Scope")
    b.p("The study is a reproduction and comparison, not the development of a new algorithm. It does "
        "not attempt cross-project prediction, deep learning over source-code representations, or the "
        "incorporation of process metrics, all of which are identified in Chapter 19 as future work. "
        "Within the boundary that was set, the work is complete; the boundary itself, however, "
        "excludes several of the directions in which the field is currently most active.")


# =========================================================================== #
def ch21_bibliography(b: ReportBuilder) -> None:
    b.chapter("Bibliography")
    b.p("References are listed in the order of their first citation in the text and are formatted in "
        "the IEEE style.")
    refs = [
        "T. J. McCabe, “A complexity measure,” IEEE Transactions on Software Engineering, "
        "vol. SE-2, no. 4, pp. 308–320, 1976.",
        "M. H. Halstead, Elements of Software Science. New York, NY, USA: Elsevier North-Holland, 1977.",
        "T. Menzies, J. Greenwald and A. Frank, “Data mining static code attributes to learn "
        "defect predictors,” IEEE Transactions on Software Engineering, vol. 33, no. 1, "
        "pp. 2–13, 2007.",
        "S. Lessmann, B. Baesens, C. Mues and S. Pietsch, “Benchmarking classification models for "
        "software defect prediction: a proposed framework and novel findings,” IEEE Transactions "
        "on Software Engineering, vol. 34, no. 4, pp. 485–496, 2008.",
        "T. Hall, S. Beecham, D. Bowes, D. Gray and S. Counsell, “A systematic literature review "
        "on fault prediction performance in software engineering,” IEEE Transactions on Software "
        "Engineering, vol. 38, no. 6, pp. 1276–1304, 2012.",
        "M. Shepperd, Q. Song, Z. Sun and C. Mair, “Data quality: some comments on the NASA "
        "software defect datasets,” IEEE Transactions on Software Engineering, vol. 39, no. 9, "
        "pp. 1208–1215, 2013.",
        "B. Ghotra, S. McIntosh and A. E. Hassan, “Revisiting the impact of classification "
        "techniques on the performance of defect prediction models,” in Proceedings of the 37th "
        "IEEE/ACM International Conference on Software Engineering, Florence, Italy, 2015, "
        "pp. 789–800.",
        "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, “SMOTE: synthetic minority "
        "over-sampling technique,” Journal of Artificial Intelligence Research, vol. 16, "
        "pp. 321–357, 2002.",
        "C. Tantithamthavorn, A. E. Hassan and K. Matsumoto, “The impact of class rebalancing "
        "techniques on the performance and interpretation of defect prediction models,” IEEE "
        "Transactions on Software Engineering, vol. 46, no. 11, pp. 1200–1219, 2020.",
        "D. Chicco and G. Jurman, “The advantages of the Matthews correlation coefficient (MCC) "
        "over F1 score and accuracy in binary classification evaluation,” BMC Genomics, vol. 21, "
        "no. 6, 2020.",
        "R. Malhotra, “A systematic review of machine learning techniques for software fault "
        "prediction,” Applied Soft Computing, vol. 27, pp. 504–518, 2015.",
        "R. S. Wahono, “A systematic literature review of software defect prediction: research "
        "trends, datasets, methods and frameworks,” Journal of Software Engineering, vol. 1, "
        "no. 1, pp. 1–16, 2015.",
        "Z. Li, X.-Y. Jing and X. Zhu, “Progress on approaches to software defect "
        "prediction,” IET Software, vol. 12, no. 3, pp. 161–175, 2018.",
        "L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
        "J. H. Friedman, “Greedy function approximation: a gradient boosting machine,” The "
        "Annals of Statistics, vol. 29, no. 5, pp. 1189–1232, 2001.",
        "C. Cortes and V. Vapnik, “Support-vector networks,” Machine Learning, vol. 20, "
        "no. 3, pp. 273–297, 1995.",
        "J. Sayyad Shirabad and T. Menzies, “The PROMISE repository of software engineering "
        "databases,” School of Information Technology and Engineering, University of Ottawa, "
        "Canada, 2005. [Online]. Available: http://promise.site.uottawa.ca/SERepository",
        "“NASADefectDataset: original and cleaned NASA MDP software defect datasets,” GitHub "
        "repository. [Online]. Available: https://github.com/klainfo/NASADefectDataset "
        "[Accessed: 26 September 2026].",
        "F. Pedregosa et al., “Scikit-learn: machine learning in Python,” Journal of Machine "
        "Learning Research, vol. 12, pp. 2825–2830, 2011.",
        "G. Lemaître, F. Nogueira and C. K. Aridas, “Imbalanced-learn: a Python toolbox to "
        "tackle the curse of imbalanced datasets in machine learning,” Journal of Machine "
        "Learning Research, vol. 18, no. 17, pp. 1–5, 2017.",
        "B. W. Boehm, Software Engineering Economics. Englewood Cliffs, NJ, USA: Prentice-Hall, 1981.",
        "B. W. Boehm and V. R. Basili, “Software defect reduction top 10 list,” IEEE "
        "Computer, vol. 34, no. 1, pp. 135–137, 2001.",
        "J. D. Musa, A. Iannino and K. Okumoto, Software Reliability: Measurement, Prediction, "
        "Application. New York, NY, USA: McGraw-Hill, 1987.",
        "D. Kung, Object-Oriented Software Engineering: An Agile Unified Methodology. New York, NY, "
        "USA: McGraw-Hill Higher Education, 2013.",
        "I. H. Witten, E. Frank, M. A. Hall and C. J. Pal, Data Mining: Practical Machine Learning "
        "Tools and Techniques, 4th ed. Cambridge, MA, USA: Morgan Kaufmann, 2016.",
    ]
    for i, r in enumerate(refs, 1):
        b._para(f"[{i}]  {r}", size=Pt(13), align=3, space_after=Pt(7))


# =========================================================================== #
def appendix(b: ReportBuilder) -> None:
    b.chapter("Appendix A: Execution Instructions")
    b.p("The complete experiment reported in this document can be reproduced by executing the "
        "following commands from the project root directory on any machine with Python 3.9 or later. "
        "An internet connection is required only for the first two commands.")
    b.code("""pip install -r requirements.txt

python scripts/download_data.py            # fetch KC1, JM1, PC1 and CM1
python scripts/run_eda.py --all            # exploratory figures and statistics
python scripts/run_pipeline.py --all       # train, cross-validate and evaluate
python -m pytest -q                        # run the automated test suite""",
           "A.1  Reproducing the complete study")
    b.code("""# ablation study reported in Section 15.5
python scripts/run_pipeline.py --dataset KC1 --balance none

# cost-sensitive learning instead of over-sampling
python scripts/run_pipeline.py --dataset KC1 --balance class_weight

# enable the randomised hyper-parameter search of Section 15.7
python scripts/run_pipeline.py --dataset KC1 --tune

# score previously unseen modules with a saved model
python scripts/predict.py --dataset KC1 --model gradient_boosting \\
       --input data/sample_modules.csv --output scored.csv""",
           "A.2  Supplementary experiments and prediction")
    b.p("Results are written beneath results/<DATASET>/ and a combined table is written to "
        "results/summary_all_datasets.csv. The figures reproduced in this report are regenerated by "
        "scripts/make_report_figures.py and scripts/make_extra_figures.py. Every setting referred to "
        "in Chapter 10 is declared in config.yaml, and altering any of them requires no change to the "
        "source code.")
    b.p("Expected execution time on the hardware described in Chapter 8 is approximately one minute "
        "for the exploratory analysis and six minutes for the complete experiment over all four "
        "datasets. The automated test suite completes in under five seconds.")
