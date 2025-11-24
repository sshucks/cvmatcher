import pandas as pd
from sklearn.metrics import roc_auc_score

validation_results = pd.read_csv("data/validation_data/validation_results/previous_group.csv")

# remove rows with NaN scores
validation_results = validation_results.dropna(subset=['score'])


# Calculate AUC-ROC
y_true = validation_results['t1']
y_scores = validation_results['score']

auc_roc = roc_auc_score(y_true, y_scores)
print(f"AUC-ROC: {auc_roc:.4f}")