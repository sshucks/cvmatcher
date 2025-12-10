import pandas as pd
from sklearn.metrics import roc_auc_score

validation_results = pd.read_csv("data/validation_data/validation_results/LLMParsed_PreviousGroup.csv")

# remove rows with NaN in main score
validation_results = validation_results.dropna(subset=['score'])

# Main AUC
y_true = validation_results['t1']
y_scores = validation_results['score']

# Function to compute AUC for a column safely
def compute_auc(df, feature_col):
    df_clean = df.dropna(subset=[feature_col, 't1'])
    if df_clean.empty:
        return None
    return roc_auc_score(df_clean['t1'], df_clean[feature_col])

for col, label in [
    ("education", "Education"),
    ("professional_experience", "Professional Experience"),
    ("hard_skills", "Hard Skills"),
    ("soft_skills", "Soft Skills")
]:
    auc = compute_auc(validation_results, col)
    if auc is not None:
        print(f"{label} AUC-ROC: {auc:.4f}")
    else:
        print(f"{label} AUC-ROC: Not enough valid data")
        
# compute optimal threshold for each category based on Youden's J statistic
from sklearn.metrics import roc_curve
def optimal_threshold(y_true, y_scores):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    j_scores = tpr - fpr
    optimal_idx = j_scores.argmax()
    return thresholds[optimal_idx]

for col, label in [
    ("score", "General Score"),
    ("education", "Education"),
    ("professional_experience", "Professional Experience"),
    ("hard_skills", "Hard Skills"),
    ("soft_skills", "Soft Skills")
]:
    df_clean = validation_results.dropna(subset=[col, 't1'])
    if not df_clean.empty:
        threshold = optimal_threshold(df_clean['t1'], df_clean[col])
        # compute metrics at this threshold
        accuracy = ( (df_clean[col] >= threshold) == df_clean['t1'] ).mean()
        sensitivity = ((df_clean[col] >= threshold) & (df_clean['t1'] == 1)).sum() / (df_clean['t1'] == 1).sum()
        specificity = ((df_clean[col] < threshold) & (df_clean['t1'] == 0)).sum() / (df_clean['t1'] == 0).sum()
        print(f"{label} Optimal Threshold: {threshold:.4f}, Accuracy: {accuracy:.4f}, Sensitivity: {sensitivity:.4f}, Specificity: {specificity:.4f}")
    else:
        print(f"{label} Optimal Threshold: Not enough valid data")
        
