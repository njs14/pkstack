FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

WORKDIR /app
COPY requirements-runtime.txt /tmp/requirements-runtime.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements-runtime.txt
COPY src/pk_stack_lab/__init__.py pk_stack_lab/__init__.py
COPY src/pk_stack_lab/aws.py pk_stack_lab/aws.py
COPY src/pk_stack_lab/config.py pk_stack_lab/config.py
COPY src/pk_stack_lab/runtime.py pk_stack_lab/runtime.py
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["python", "-m", "pk_stack_lab.runtime"]
