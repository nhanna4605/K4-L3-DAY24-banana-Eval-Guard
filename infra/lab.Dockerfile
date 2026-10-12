# Lab24 runtime: Python 3.11 (NeMo 0.10 needs <=3.11), gcc for Annoy, CPU torch for BGE-M3 / bge-reranker.
FROM python:3.11-slim
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends build-essential git && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY requirements /tmp/requirements
RUN pip install -q --upgrade pip && \
    pip install -q torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -q -r /tmp/requirements/requirements.txt -c /tmp/requirements/constraints-core.txt && \
    python -m spacy download en_core_web_lg -q && \
    pip check
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 HF_HOME=/hfcache
CMD ["bash"]
# requirements leave pyarrow/pandas unpinned: the latest wheels need NumPy 2, the lab pins NumPy 1.26.4
RUN pip install -q "pyarrow==17.0.0" "pandas==2.2.3" -c /tmp/requirements/constraints-core.txt && pip check && python -c "import pyarrow, pandas, datasets, numpy; print(pyarrow.__version__, pandas.__version__, numpy.__version__)"
