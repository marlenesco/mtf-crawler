#!/usr/bin/env python3

import pandas as pd
import os

def analyze_files():
    print("📊 ANALISI FILE EXCEL - MTF CRAWLER")
    print("="*50)

    raw_dir = "data/raw"
    excel_files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]

    print(f"File Excel trovati: {len(excel_files)}")

    for i, file in enumerate(excel_files, 1):
        filename = file.split('_', 1)[1] if '_' in file else file
        print(f"\n🔍 FILE {i}: {filename}")
        print("-" * 30)

        file_path = f"{raw_dir}/{file}"

        try:
            # Analizza fogli disponibili
            excel_file = pd.ExcelFile(file_path)
            print(f"Fogli: {excel_file.sheet_names}")

            # Analizza primo foglio
            df = pd.read_excel(file_path, sheet_name=0)
            print(f"Dimensioni: {df.shape[0]} righe × {df.shape[1]} colonne")

            # Mostra nomi colonne
            print(f"Colonne: {list(df.columns)}")

            # Cerca proprietà materiali
            material_props = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(kw in col_str for kw in ['tensile', 'strength', 'modulus', 'elongation', 'density']):
                    material_props.append(col)

            if material_props:
                print(f"🎯 Proprietà materiali: {material_props}")

            # Mostra prime 2 righe
            print("\nPrime righe di esempio:")
            for idx in range(min(2, len(df))):
                row_data = {}
                for col in df.columns[:5]:  # Prime 5 colonne
                    value = df.iloc[idx, df.columns.get_loc(col)]
                    if pd.notna(value):
                        row_data[str(col)[:15]] = str(value)[:20]
                print(f"  Riga {idx}: {row_data}")

        except Exception as e:
            print(f"❌ Errore: {e}")

if __name__ == "__main__":
    analyze_files()
