FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

WORKDIR /app
COPY src/pk_stack_lab/__init__.py pk_stack_lab/__init__.py
COPY src/pk_stack_lab/aws.py pk_stack_lab/aws.py
COPY src/pk_stack_lab/config.py pk_stack_lab/config.py
COPY src/pk_stack_lab/runtime.py pk_stack_lab/runtime.py
# Exact runtime closure matches the committed uv.lock (boto3/botocore 1.43.86).
RUN pip install --no-cache-dir --no-deps \
    boto3==1.43.86 botocore==1.43.86 jmespath==1.1.0 \
    python-dateutil==2.9.0.post0 s3transfer==0.19.2 six==1.17.0 urllib3==2.7.0
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["python", "-m", "pk_stack_lab.runtime"]
