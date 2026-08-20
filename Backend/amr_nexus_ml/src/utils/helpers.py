# src/utils/helpers.py
def generate_shap_summary(shap_values, feature_names, mdr_prob, top_n=3):
    pairs = [(feature_names[i], shap_values[0][i]) for i in range(len(feature_names))]
    pairs.sort(key=lambda x: abs(x[1]), reverse=True)
    top = pairs[:top_n]
    parts = []
    for f, v in top:
        direction = "increasing" if v > 0 else "decreasing"
        if abs(v) > 0.1:
            parts.append(f"{f.replace('_', ' ')} ({direction})")
    if not parts:
        parts = ["a combination of factors"]
    summary = f"This prediction was primarily driven by {', '.join(parts)}. " \
              f"The model predicts a {mdr_prob*100:.1f}% probability of multidrug resistance."
    return summary