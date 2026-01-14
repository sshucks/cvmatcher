# compute optimal weighting of categories to maximize AUC
from scipy.optimize import minimize
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve

validation_results = pd.read_csv("data/validation_data/validation_results/LLMParsed_JobBert.csv")

# remove rows with NaN in main score
validation_results = validation_results.dropna()

# Main AUC
y_true = validation_results['t1']
y_scores = validation_results['score']


import numpy as np
from scipy.optimize import minimize

def weighted_score(weights, df):
    return (
        weights[0] * df['education'] +
        weights[1] * df['professional_experience'] +
        weights[2] * df['hard_skills'] +
        weights[3] * df['soft_skills']
    )

def neg_auc_softmax(x, df):
    # convert unconstrained parameters → weights that sum to 1
    weights = np.exp(x) / np.exp(x).sum()

    print("Testing weights:", weights)
    scores = weighted_score(weights, df)
    return -roc_auc_score(df['t1'], scores)

x0 = np.zeros(4)  # starting point in unconstrained space

# build a large simplex → BIG steps
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
    args=(validation_results,),
    method="Nelder-Mead",
    options={
        "initial_simplex": initial_simplex,
        "xatol": 1e-3,   # tolerate bigger moves
        "fatol": 1e-3,
        "maxiter": 2000,
        "disp": True
    }
)

optimal_weights = np.exp(result.x) / np.exp(result.x).sum()
optimal_auc = -result.fun
print(f"Optimal Weights: Education: {optimal_weights[0]:.4f}, Professional Experience: {optimal_weights[1]:.4f}, Hard Skills: {optimal_weights[2]:.4f}, Soft Skills: {optimal_weights[3]:.4f}")
print(f"Optimal AUC-ROC: {optimal_auc:.4f}")

# compute optimal threshold for each category based on Youden's J statistic
def optimal_threshold(y_true, y_scores):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    j_scores = tpr - fpr
    optimal_idx = j_scores.argmax()
    return thresholds[optimal_idx]

# calculate score with optimal weights
optimal_scores = weighted_score(optimal_weights, validation_results)
threshold = optimal_threshold(validation_results['t1'], optimal_scores)
accuracy = ( (optimal_scores >= threshold) == validation_results['t1'] ).mean()
sensitivity = ((optimal_scores >= threshold) & (validation_results['t1'] == 1)).sum() / (validation_results['t1'] == 1).sum()
specificity = ((optimal_scores < threshold) & (validation_results['t1'] == 0)).sum() / (validation_results['t1'] == 0).sum()
print(f"Optimal Weights Score Optimal Threshold: {threshold:.4f}, Accuracy: {accuracy:.4f}, Sensitivity: {sensitivity:.4f}, Specificity: {specificity:.4f}")