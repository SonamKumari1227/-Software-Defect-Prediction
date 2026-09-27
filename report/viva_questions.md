# Viva-Voce Preparation: Software Defect Prediction using Machine Learning

The questions are grouped by theme and ordered roughly from basic to advanced.
Each answer is written the way it can be spoken in a viva - concise, then one
supporting detail.

---

## A. Problem and motivation

**1. What is software defect prediction and why is it useful?**
It is the task of identifying, before testing, which software modules are likely to contain defects, using measurable properties of the code. It lets a team focus limited testing and code-review effort on the ~20 % of modules that typically contain ~80 % of the defects, reducing cost and improving reliability.

**2. What is a "module" in your datasets?**
A function, procedure or method - the smallest unit for which NASA's MDP tools computed static metrics. Each row of the dataset is one module.

**3. Why static code metrics rather than, say, test results?**
Static metrics are available as soon as the code is written, need no execution, and are cheap to compute automatically. They are therefore usable early in the life-cycle, which is exactly when defect prediction has the most value.

**4. How does this project relate to the Minor Project course outcomes?**
CO-1 asks for identifying a research problem through a literature survey; I surveyed the defect-prediction literature (Menzies et al. 2007, Lessmann et al. 2008, Hall et al. 2012, Shepperd et al. 2013). CO-2 asks to analyse an existing solution and reproduce it; I reproduced the standard benchmarking methodology on the NASA datasets and extended it with a leakage-free pipeline, SMOTE and additional metrics.

---

## B. Dataset

**5. Which datasets did you use and where do they come from?**
KC1, JM1, PC1 and CM1 from the NASA Metrics Data Program, distributed through the PROMISE repository. I used the cleaned "D''" versions published by Shepperd et al. (2013).

**6. Why the cleaned versions?**
Shepperd et al. showed the original files contain many duplicated, inconsistent and implausible rows (KC1 alone is ~43 % duplicates). Duplicates across train/test splits inflate accuracy artificially, so results on the raw files are unreliable. Using the cleaned versions is now the accepted practice.

**7. What are the features?**
Three families: (i) size - lines of code, blank, comment and executable lines; (ii) McCabe complexity - cyclomatic, design and essential complexity, branch count; (iii) Halstead metrics - number of unique/total operators and operands, and derived measures such as length, volume, difficulty, effort, programming time and estimated bugs. PC1 and CM1 also include a few extra density/call metrics, giving 37 features instead of 21.

**8. What is cyclomatic complexity?**
The number of linearly independent paths through a module's control-flow graph: E - N + 2P. Higher values mean more decision points, more test cases needed, and more room for mistakes.

**9. What are Halstead metrics?**
Metrics derived from counting operators and operands: vocabulary n = n1 + n2, length N = N1 + N2, volume V = N log2 n, difficulty D = (n1/2)·(N2/n2), effort E = D·V. They estimate the mental effort needed to write or understand the code.

**10. How imbalanced are the classes?**
Between 8 % (PC1) and 25 % (KC1) defective. A classifier that always predicts "non-defective" would already achieve 75-92 % accuracy, which is why accuracy alone is misleading here.

---

## C. Preprocessing

**11. What preprocessing steps did you apply, and why?**
Remove duplicates and constant columns; median imputation for missing values; a log1p transform because every metric is strongly right-skewed; standardisation so that distance- and gradient-based models (k-NN, SVM, logistic regression, MLP) treat features equally.

**12. Why log1p and not log?**
Many metrics are legitimately zero (e.g. blank lines); log(0) is undefined while log1p(0) = 0.

**13. Does tree-based learning need scaling?**
No - trees split on thresholds and are invariant to monotone transforms. Applying the same pipeline to all models keeps the comparison fair and the code simple; it does not harm the trees.

**14. What is data leakage and how did you prevent it?**
Leakage is when information from the test data influences training. I prevented it by (a) splitting before any learned transformation and (b) placing imputation, scaling and SMOTE inside a scikit-learn/imblearn Pipeline, so they are fitted only on the training fold in every cross-validation iteration.

**15. What is SMOTE?**
Synthetic Minority Over-sampling Technique (Chawla et al. 2002). For each minority sample it picks one of its k nearest minority neighbours and creates a new synthetic point along the line segment between them, until the classes are balanced. It is applied only to training data - never to the test set.

**16. Why not simply duplicate minority rows (random over-sampling)?**
Duplication makes models over-fit the exact copies. SMOTE generates new, plausible points and gives a smoother decision boundary.

**17. What alternatives to SMOTE did you consider?**
`class_weight='balanced'` (cost-sensitive learning) and no balancing. All three are selectable with `--balance` so their effect can be compared.

---

## D. Models

**18. Which models did you compare and why those?**
Eight baselines that span the main families: linear (logistic regression), probabilistic (Gaussian naive Bayes), instance-based (k-NN), kernel (SVM-RBF), single tree, bagging ensemble (random forest), boosting ensemble (gradient boosting) and neural (MLP). This mirrors the benchmarking studies of Lessmann et al. (2008) and Ghotra et al. (2015).

**19. How does a random forest work?**
It trains many decision trees on bootstrap samples of the data, each split considering only a random subset of features, and averages their votes. The randomness de-correlates the trees so the ensemble has lower variance than any single tree.

**20. How does gradient boosting differ from random forest?**
Random forest builds trees independently and in parallel (bagging); gradient boosting builds them sequentially, each new shallow tree fitting the residual errors of the ensemble so far (boosting). Boosting usually has lower bias but is more sensitive to noise and hyper-parameters.

**21. Why does your SVM sit inside `CalibratedClassifierCV`?**
An SVM outputs a signed distance from the hyperplane, not a probability. Platt scaling (sigmoid calibration) converts the score to a probability so I can compute ROC-AUC and precision-recall curves consistently with the other models.

**22. Why did naive Bayes perform reasonably well despite its independence assumption?**
Naive Bayes is a low-variance model; on small, noisy datasets that often matters more than the biased independence assumption. Menzies et al. (2007) reported the same finding on these datasets.

**23. What hyper-parameters did you use? Did you tune them?**
Sensible defaults from the literature (e.g. 300 trees, `max_depth=8` for the single tree, k=7). A `RandomizedSearchCV` option (`--tune`) is implemented and searches F1-optimal settings for RF, GB, SVM, LR and k-NN. The report's main results use the defaults so that comparison is fair and reproducible.

---

## E. Evaluation

**24. Explain your validation strategy.**
A stratified 80/20 hold-out split is made once. On the 80 % training part I run stratified k-fold cross-validation to estimate each model's stability. The final model is then re-fitted on the full training part and scored once on the untouched 20 %.

**25. Why stratified?**
So that every fold and the test set contain the same proportion of defective modules; otherwise a fold might contain almost no positives, making recall/F1 meaningless.

**26. Define precision, recall and F1 for this problem.**
Precision = of the modules flagged defective, how many really are (TP/(TP+FP)). Recall = of the truly defective modules, how many we caught (TP/(TP+FN)). F1 is their harmonic mean, which penalises a model that is good at only one of the two.

**27. Which metric matters most for defect prediction?**
Usually recall (missing a real defect is expensive) balanced against the probability of false alarm PF = FP/(FP+TN), because every false alarm wastes review effort. F1, ROC-AUC and MCC summarise that trade-off; I report all of them.

**28. What is ROC-AUC?**
The area under the curve of true-positive rate against false-positive rate for every possible threshold. It equals the probability that a randomly chosen defective module receives a higher score than a randomly chosen clean one; 0.5 is chance, 1.0 is perfect. It is threshold-independent and insensitive to class imbalance.

**29. What is MCC and why include it?**
Matthews Correlation Coefficient - a correlation between predicted and true labels in [-1, 1] that uses all four cells of the confusion matrix. Chicco & Jurman (2020) show it is more reliable than accuracy or F1 on imbalanced data.

**30. Why is accuracy lower with SMOTE than without?**
Without balancing, models predict the majority class most of the time, giving high accuracy but poor recall. SMOTE shifts the decision boundary towards the minority class: recall and F1 rise, accuracy and precision fall. That is the intended trade-off.

**31. Why are ROC-AUC values on these datasets only ~0.7-0.8, not 0.95+?**
Static metrics capture size and complexity but not semantics, requirements changes or developer experience, so there is an inherent ceiling. Published results on the cleaned NASA data are in the same range (Shepperd et al. 2013; Ghotra et al. 2015).

**32. Could a model with 90 % accuracy be useless here?**
Yes - on PC1 (8 % defective) a constant "non-defective" predictor scores 92 % accuracy with zero recall. That is why I report balanced metrics.

---

## F. Implementation and engineering

**33. Describe the software architecture.**
A Python package `sdp` with single-responsibility modules (data loading, preprocessing, models, evaluation, visualisation), a YAML configuration file, thin command-line scripts, and pytest tests. All learned steps are scikit-learn pipelines so a trained model is one serialisable object.

**34. How do you guarantee reproducibility?**
One `random_seed` controls the split, the CV folds, SMOTE and every stochastic model; every setting is in `config.yaml`; results are written with the effective configuration; and a unit test asserts two runs give identical metrics.

**35. How would you use the trained model in practice?**
`scripts/predict.py` loads a saved pipeline and scores a CSV of module metrics, outputting a defect probability and a label. In a real team it could run in CI on every commit, ranking changed files for review.

**36. What did the tests cover?**
ARFF parsing, target encoding, duplicate/constant removal, stratification, metric computation, an end-to-end fit/predict smoke test for every model under all three balancing modes, and determinism.

---

## G. Critical thinking / limitations

**37. What are the threats to validity?**
*Construct*: static metrics are a proxy for defect-proneness. *Internal*: default hyper-parameters may favour some models; a single seed. *External*: NASA projects are old, C/C++ flight software - results may not transfer to modern web or mobile code. *Conclusion*: the smaller datasets (CM1: 327 rows) give high-variance estimates.

**38. Why do results differ so much between datasets?**
Different projects, languages, defect ratios and sample sizes. Cross-project transfer is a well-known open problem in this field.

**39. If you had more time, what would you improve?**
Repeated CV with several seeds and statistical tests (Scott-Knott ESD); cost-sensitive threshold tuning; feature selection; testing on modern datasets (e.g. Apache/Jureczko); process metrics (churn, ownership); and explainability with SHAP.

**40. Is a defect predictor a replacement for testing?**
No - it is a prioritisation tool. It tells the team where to look first; it cannot confirm that a module is correct.
