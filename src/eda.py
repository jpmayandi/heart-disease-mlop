"""EDA: cleaning + figures saved to reports/figures."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

from src import data  # noqa: E402

FIG_DIR = Path(__file__).resolve().parents[1] / "reports" / "figures"


def run() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    raw = data.load_raw()
    print("Raw shape:", raw.shape)
    print("Missing values:\n", raw.isna().sum()[raw.isna().sum() > 0])

    df = data.clean(raw)
    path = data.save_clean(df)
    print("Clean shape:", df.shape, "->", path)
    print(df.describe().T.round(2))

    sns.set_theme(style="whitegrid")

    # 1. Histograms of numeric features
    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for ax, col in zip(axes.ravel(), data.NUMERIC_FEATURES):
        sns.histplot(data=df, x=col, hue=data.TARGET, kde=True, ax=ax,
                     palette="Set1")
        ax.set_title(f"Distribution of {col}")
    axes.ravel()[-1].axis("off")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "histograms.png", dpi=150)
    plt.close(fig)

    # 2. Correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df.corr(numeric_only=True), annot=True, fmt=".2f",
                cmap="coolwarm", ax=ax)
    ax.set_title("Correlation heatmap")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "correlation_heatmap.png", dpi=150)
    plt.close(fig)

    # 3. Class balance
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.countplot(data=df, x=data.TARGET, hue=data.TARGET, ax=ax,
                  palette="Set2", legend=False)
    ax.set_title("Class balance (0 = no disease, 1 = disease)")
    for p in ax.patches:
        ax.annotate(int(p.get_height()), (p.get_x() + p.get_width() / 2,
                                          p.get_height()), ha="center",
                    va="bottom")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "class_balance.png", dpi=150)
    plt.close(fig)

    # 4. Boxplots by target
    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    for ax, col in zip(axes, data.NUMERIC_FEATURES):
        sns.boxplot(data=df, x=data.TARGET, y=col, ax=ax)
        ax.set_title(col)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "boxplots_by_target.png", dpi=150)
    plt.close(fig)

    print("Figures saved to", FIG_DIR)


if __name__ == "__main__":
    run()
