import pandas as pd
import os

def quick_analysis():
    raw_dir = "data/raw"
    files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]

    print(f"📊 File Excel trovati: {len(files)}")

    for i, file in enumerate(files, 1):
        filename = file.split('_', 1)[1] if '_' in file else file
        print(f"\n🔍 FILE {i}: {filename}")

        file_path = f"{raw_dir}/{file}"

        try:
            # Analizza primo foglio
            df = pd.read_excel(file_path, sheet_name=0)
            print(f"   Dimensioni: {df.shape[0]} righe x {df.shape[1]} colonne")
            print(f"   Colonne: {list(df.columns)}")

            # Mostra prime 2 righe per capire la struttura
            print("   Prime righe:")
            for idx, row in df.head(2).iterrows():
                print(f"     Riga {idx}: {row.to_dict()}")

        except Exception as e:
            print(f"   Errore: {e}")

if __name__ == "__main__":
    quick_analysis()
