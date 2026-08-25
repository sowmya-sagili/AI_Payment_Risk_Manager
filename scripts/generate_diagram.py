import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')

    # Define boxes: (x, y, width, height, text, color)
    boxes = [
        (3.5, 7.0, 3, 0.8, "Streamlit Dashboard\n(Frontend)", "#4dabf7"),
        (3.5, 5.5, 3, 0.8, "FastAPI REST API\n(Backend)", "#3bc9db"),
        (3.5, 4.0, 3, 0.8, "Risk Engine\n(Policy Logic)", "#20c997"),
        (1.5, 2.5, 2.5, 0.8, "XGBoost Model\n(ML Predictor)", "#a9e34b"),
        (6.0, 2.5, 2.5, 0.8, "AI Investigation\n(Explainability)", "#ffa94d"),
        (3.5, 1.0, 3, 0.8, "SQLite Database\n(History & Analytics)", "#ced4da")
    ]

    for x, y, w, h, text, color in boxes:
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor=color)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=11, fontweight='bold', color='black')

    # Draw arrows
    arrows = [
        (5.0, 7.0, 5.0, 6.3),  # Streamlit -> FastAPI
        (5.0, 5.5, 5.0, 4.8),  # FastAPI -> Risk Engine
        (4.5, 4.0, 2.75, 3.3), # Risk Engine -> Model
        (2.75, 2.5, 4.5, 4.0), # Model -> Risk Engine (Return)
        (5.5, 4.0, 7.25, 3.3), # Risk Engine -> Investigation
        (5.0, 4.0, 5.0, 1.8),  # Risk Engine -> DB
    ]

    for x1, y1, x2, y2 in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=2, color="gray"))

    plt.title("AI Payment Risk Manager Architecture", fontsize=16, fontweight='bold', pad=20)
    
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    plt.savefig(os.path.join(docs_dir, "architecture.png"), bbox_inches='tight', dpi=300)
    print("Generated architecture.png")

if __name__ == "__main__":
    create_architecture_diagram()
