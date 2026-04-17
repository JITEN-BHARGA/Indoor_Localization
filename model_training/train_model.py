import argparse
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler


def load_and_clean_data(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if path.suffix.lower() == '.xlsx':
        df = pd.read_excel(path)
    elif path.suffix.lower() == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError('Supported file types: .xlsx, .csv')

    df = df.loc[:, ~df.columns.astype(str).str.contains(r'^Unnamed')]
    required = ['Location', 'Sequence Number', 'SSID', 'MAC Address', 'RSSI value']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

    df = df[required].copy()
    df['Location'] = df['Location'].astype(str).str.strip()
    df['MAC Address'] = df['MAC Address'].astype(str).str.strip().str.upper()
    df['RSSI value'] = pd.to_numeric(df['RSSI value'], errors='coerce')
    df['Sequence Number'] = pd.to_numeric(df['Sequence Number'], errors='coerce')
    df = df.dropna(subset=['Location', 'MAC Address', 'RSSI value', 'Sequence Number'])
    df['Sequence Number'] = df['Sequence Number'].astype(int)
    return df


def build_fingerprint_dataset(df: pd.DataFrame):
    df = df.copy()
    df['obs_id'] = df['Location'].astype(str) + '__' + df['Sequence Number'].astype(str)
    pivot_df = df.pivot_table(
        index='obs_id',
        columns='MAC Address',
        values='RSSI value',
        aggfunc='mean'
    ).fillna(-100)
    y = df.groupby('obs_id')['Location'].first().loc[pivot_df.index]
    return pivot_df, y


def save_plot(fig_path: Path, fig_fn):
    plt.figure(figsize=(8, 5))
    fig_fn()
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Train Wi-Fi indoor localization model')
    parser.add_argument('--input', required=True, help='Input dataset path')
    parser.add_argument('--output_dir', default='backend/artifacts', help='Artifacts folder')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_and_clean_data(args.input)
    X_df, y_series = build_fingerprint_dataset(df)

    X = X_df.values
    y = y_series.values
    feature_columns = list(X_df.columns)

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.25, random_state=42, stratify=y_encoded
    )

    model = Pipeline([
        ('scaler', StandardScaler()),
        ('mlp', MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=300,
            random_state=42,
            early_stopping=True,
        ))
    ])

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    mlp = model.named_steps['mlp']

    bundle = {
        'model': model,
        'label_encoder': label_encoder,
        'feature_columns': feature_columns,
    }
    joblib.dump(bundle, output_dir / 'location_model.joblib')

    fingerprint_ref = X_df.copy()
    fingerprint_ref['Location'] = y_series.values
    fingerprint_ref.to_csv(output_dir / 'fingerprint_reference.csv', index=False)

    metadata = {
        'accuracy': float(accuracy),
        'final_training_loss': float(mlp.loss_),
        'best_validation_accuracy': float(mlp.best_validation_score_),
        'class_names': list(label_encoder.classes_),
        'num_features': len(feature_columns),
        'num_samples': len(X_df),
    }
    with open(output_dir / 'model_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    report = classification_report(y_test, y_pred, target_names=label_encoder.classes_, digits=4)
    with open(output_dir / 'classification_report.txt', 'w', encoding='utf-8') as f:
        f.write(f'Accuracy: {accuracy:.4f}\n')
        f.write(f'Final training loss: {mlp.loss_:.4f}\n')
        f.write(f'Best validation accuracy: {mlp.best_validation_score_:.4f}\n\n')
        f.write(report)

    cm = confusion_matrix(y_test, y_pred)

    save_plot(output_dir / 'location_distribution.png', lambda: y_series.value_counts().sort_index().plot(kind='bar', title='Sample Count by Location'))
    save_plot(output_dir / 'rssi_distribution.png', lambda: plt.hist(df['RSSI value'].dropna(), bins=25))
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(mlp.loss_curve_) + 1), mlp.loss_curve_)
    plt.title('Training Loss Curve')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.tight_layout()
    plt.savefig(output_dir / 'training_loss_curve.png', dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(mlp.validation_scores_) + 1), mlp.validation_scores_)
    plt.title('Validation Accuracy Curve')
    plt.xlabel('Epoch')
    plt.ylabel('Validation Accuracy')
    plt.tight_layout()
    plt.savefig(output_dir / 'validation_accuracy_curve.png', dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    plt.imshow(cm)
    plt.title('Confusion Matrix')
    plt.xticks(range(len(label_encoder.classes_)), label_encoder.classes_, rotation=45, ha='right')
    plt.yticks(range(len(label_encoder.classes_)), label_encoder.classes_)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, str(cm[i, j]), ha='center', va='center')
    plt.tight_layout()
    plt.savefig(output_dir / 'confusion_matrix.png', dpi=150)
    plt.close()

    print('Training complete')
    print(f'Accuracy: {accuracy:.4f}')
    print(f'Artifacts saved to: {output_dir.resolve()}')


if __name__ == '__main__':
    main()
