import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve
from scipy.optimize import minimize
import matplotlib.pyplot as plt


# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------
validation_results = pd.read_csv(
    "data/validation_data/validation_results/LLMParsed_GermanBERT.csv"
)

# Remove rows with NaN target or component scores
cols = ["education", "professional_experience", "hard_skills", "soft_skills", "t1"]
validation_results = validation_results.dropna(subset=cols)

# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------
def compute_auc(df, feature_col):
    df_clean = df.dropna(subset=[feature_col, "t1"])
    if df_clean.empty or df_clean["t1"].nunique() < 2:
        return None
    return roc_auc_score(df_clean["t1"], df_clean[feature_col])


def normalize_scores(scores, thresholds):
    """
    scores: (n_samples, 4)
    thresholds: (4,)
    """
    thresholds = thresholds.reshape(1, -1)  # broadcast-safe

    return np.where(
        scores <= thresholds,
        (scores / thresholds) * 0.5,
        0.5 + ((scores - thresholds) / (1 - thresholds)) * 0.5,
    )


def optimal_threshold(y_true, y_scores):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    j_scores = tpr - fpr
    return thresholds[np.argmax(j_scores)]


def weighted_score(weights, normalized_scores):
    """
    weights: (4,)
    normalized_scores: (n_samples, 4)
    """
    return normalized_scores @ weights


# comput auc for general score
main_auc = compute_auc(validation_results, "score")
print(f"Previous score AUC-ROC: {main_auc:.4f}")

# ------------------------------------------------------------------
# Compute optimal thresholds
# ------------------------------------------------------------------
features = [
    ("education", "Education"),
    ("professional_experience", "Professional Experience"),
    ("hard_skills", "Hard Skills"),
    ("soft_skills", "Soft Skills"),
]

optimal_thresholds = []

for col, label in features:
    threshold = optimal_threshold(validation_results["t1"], validation_results[col])
    optimal_thresholds.append(threshold)

    preds = validation_results[col] >= threshold
    y = validation_results["t1"]

    accuracy = (preds == y).mean()
    sensitivity = ((preds) & (y == 1)).sum() / (y == 1).sum()
    specificity = ((~preds) & (y == 0)).sum() / (y == 0).sum()

    print(
        f"{label} | Threshold={threshold:.4f} "
        f"Acc={accuracy:.4f} Sens={sensitivity:.4f} Spec={specificity:.4f}"
    )

thresholds = np.array(optimal_thresholds)

# ------------------------------------------------------------------
# Normalize component scores
# ------------------------------------------------------------------
scores = validation_results[[f[0] for f in features]].to_numpy()
normalized_scores = normalize_scores(scores, thresholds)

# ------------------------------------------------------------------
# Optimization target
# ------------------------------------------------------------------
def neg_auc_softmax(x, normalized_scores, y_true):
    weights = np.exp(x)
    weights /= weights.sum()

    combined_score = weighted_score(weights, normalized_scores)
    return -roc_auc_score(y_true, combined_score)


# ------------------------------------------------------------------
# Optimize weights
# ------------------------------------------------------------------
x0 = np.zeros(4)

initial_simplex = np.vstack([
    x0,
    x0 + np.array([1, 0, 0, 0]),
    x0 + np.array([0, 1, 0, 0]),
    x0 + np.array([0, 0, 1, 0]),
    x0 + np.array([0, 0, 0, 1]),
])

result = minimize(
    neg_auc_softmax,
    x0,
    args=(normalized_scores, validation_results["t1"]),
    method="Nelder-Mead",
    options=dict(
        initial_simplex=initial_simplex,
        xatol=1e-3,
        fatol=1e-3,
        maxiter=2000,
        disp=True,
    ),
)

optimal_weights = np.exp(result.x)
optimal_weights /= optimal_weights.sum()

print("\nOptimal weights:")
for (col, label), w in zip(features, optimal_weights):
    print(f"{label}: {w:.4f}")

print(f"\nOptimal AUC-ROC: {-result.fun:.4f}")

# calculate accuracy, sensitivity, specificity at optimal threshold
optimal_combined_scores = weighted_score(optimal_weights, normalized_scores)
optimal_thresh = optimal_threshold(validation_results["t1"], optimal_combined_scores)
preds = optimal_combined_scores >= optimal_thresh
y = validation_results["t1"]
accuracy = (preds == y).mean()
tpr = ((preds) & (y == 1)).sum() / (y == 1).sum()
fpr = ((~preds) & (y == 0)).sum() / (y == 0).sum()


print(
    f"\nAt optimal threshold {optimal_thresh:.4f}:\n"
    f"Accuracy: {accuracy:.4f}\n"
    f"TPR: {tpr:.4f}\n"
    f"FPR: {fpr:.4f}\n"
)


# draw auc curve for optimal weights
fpr, tpr, _ = roc_curve(validation_results["t1"], optimal_combined_scores)
plt.figure()
plt.plot(fpr, tpr, label="GermanBERT", color="red")
plt.plot([0, 1], [0, 1], 'k--', label="Random Guess")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve GermanBERT")
plt.legend()

# save figure
plt.savefig("validation/roc_curve_GermanBERT.png")