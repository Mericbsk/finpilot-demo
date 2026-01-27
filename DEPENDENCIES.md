# ============================================================================
# FinPilot Dependencies - Profile Overview
# ============================================================================
#
# KURULUM PROFİLLERİ:
#
# 1) CORE (Temel)
#    pip install -r requirements.txt
#    → Tarama, sinyal üretimi, temel API
#
# 2) OBSERVABILITY (İzleme)
#    pip install -r requirements.txt -r requirements-observability.txt
#    → Sentry, Prometheus, psutil, MLflow
#
# 3) ETL (Veri İşleme)
#    pip install -r requirements.txt -r requirements-etl.txt
#    → Büyük veri, batch processing
#
# 4) RL (Reinforcement Learning)
#    pip install -r requirements.txt -r requirements-rl.txt
#    → DRL modelleri, stable-baselines3
#
# 5) ALTDATA (Alternatif Veri)
#    pip install -r requirements.txt -r requirements-altdata.txt
#    → Sosyal medya, haber analizi
#
# 6) FULL (Tümü)
#    pip install -r requirements.txt -r requirements-observability.txt \
#                -r requirements-etl.txt -r requirements-rl.txt -r requirements-altdata.txt
#
# ============================================================================
# OPSİYONEL BAĞIMLILIKLAR DURUMU:
# ============================================================================
#
# | Paket          | Profil        | Yoksa Davranış           |
# |----------------|---------------|--------------------------|
# | redis          | observability | Memory-only cache        |
# | sentry-sdk     | observability | Error tracking disabled  |
# | prometheus     | observability | Metrics disabled         |
# | psutil         | observability | Memory metrics disabled  |
# | mlflow         | observability | Experiment tracking off  |
# | stable-baselines3 | rl         | DRL modelleri devre dışı |
#
# ============================================================================
