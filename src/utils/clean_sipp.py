import pandas as pd, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
df = pd.read_csv('data/processed/putusan_sipp_sidoarjo_negara_wanprestasi.csv')
print(f'SEBELUM: {len(df)} baris')
bad = df[df['Lama Proses'] <= 0]
print(f'Baris anomali (Lama Proses <= 0): {len(bad)}')
if len(bad) > 0:
    print(bad[['Nomor Perkara','Lama Proses']].to_string())
df_clean = df[df['Lama Proses'] > 0].copy()
df_clean.to_csv('data/processed/putusan_sipp_sidoarjo_negara_wanprestasi.csv', index=False, encoding='utf-8-sig')
print(f'SETELAH: {len(df_clean)} baris')
lp = df_clean['Lama Proses']
print(f'Min: {lp.min()}, Max: {lp.max()}, Mean: {lp.mean():.1f}')
