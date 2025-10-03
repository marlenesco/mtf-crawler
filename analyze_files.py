#!/usr/bin/env python3
"""
Script per analizzare la struttura dei file Excel scaricati
e capire come estrarre e normalizzare i dati dei materiali.
"""

import pandas as pd
import os
import sys
from pathlib import Path

def analyze_excel_files():
    """Analizza tutti i file Excel nella cartella data/raw/"""

    raw_dir = "data/raw"
    if not os.path.exists(raw_dir):
        print("❌ Cartella data/raw non trovata")
        return

    # Trova tutti i file Excel
    excel_files = [f for f in os.listdir(raw_dir) if f.endswith('.xlsx')]

    print(f"📊 ANALISI DI {len(excel_files)} FILE EXCEL SCARICATI")
    print("=" * 60)

    for i, file in enumerate(excel_files, 1):
        # Estrai nome file senza hash
        filename = file.split('_', 1)[1] if '_' in file else file
        print(f"\n🔍 FILE {i}: {filename}")
        print("-" * 40)

        file_path = os.path.join(raw_dir, file)

        try:
            # Carica il file Excel
            excel_file = pd.ExcelFile(file_path)
            print(f"📋 Fogli disponibili: {excel_file.sheet_names}")

            # Analizza ogni foglio
            for sheet_name in excel_file.sheet_names:
                print(f"\n   📄 Foglio: {sheet_name}")

                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"   📐 Dimensioni: {df.shape[0]} righe × {df.shape[1]} colonne")

                if df.empty:
                    print("   ⚠️  Foglio vuoto")
                    continue

                # Mostra colonne (max 8)
                cols = [str(col)[:25] + "..." if len(str(col)) > 25 else str(col) for col in df.columns[:8]]
                print(f"   📊 Colonne: {cols}")

                # Cerca proprietà dei materiali nelle prime righe/colonne
                material_keywords = ['tensile', 'strength', 'modulus', 'elongation', 'density',
                                   'temperature', 'mpa', 'gpa', 'young', 'flexural', 'impact']

                found_properties = []

                # Cerca nelle colonne
                for col in df.columns:
                    col_str = str(col).lower()
                    for keyword in material_keywords:
                        if keyword in col_str:
                            found_properties.append(f"Col: {keyword}→{str(col)[:20]}")

                # Cerca nelle prime celle
                for row_idx in range(min(10, len(df))):
                    for col_idx in range(min(5, len(df.columns))):
                        cell_value = str(df.iloc[row_idx, col_idx]).lower()
                        for keyword in material_keywords:
                            if keyword in cell_value and len(cell_value) < 50:
                                found_properties.append(f"Cella: {keyword}→{cell_value[:20]}")

                if found_properties:
                    print(f"   🎯 Proprietà materiali trovate: {found_properties[:3]}")
                else:
                    print("   ⚠️  Nessuna proprietà materiale ovvia identificata")

                # Cerca valori numerici con unità
                numeric_with_units = []
                for col in df.columns[:5]:
                    sample_values = df[col].dropna().astype(str).tolist()[:3]
                    for val in sample_values:
                        if any(unit in val.lower() for unit in ['mpa', 'gpa', 'mm', 'kg', '%', '°c']):
                            numeric_with_units.append(val[:20])

                if numeric_with_units:
                    print(f"   📏 Valori con unità: {numeric_with_units[:3]}")

        except Exception as e:
            print(f"   ❌ Errore nell'analisi: {e}")

if __name__ == "__main__":
    analyze_excel_files()
