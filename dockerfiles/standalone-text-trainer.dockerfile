FROM python:3.11-slim

RUN mkdir -p /workspace/scripts /cache /app/checkpoints

COPY scripts/verify_datasets.py /workspace/scripts/verify_datasets.py
COPY scripts/run_text_trainer.sh /workspace/scripts/run_text_trainer.sh
RUN chmod +x /workspace/scripts/run_text_trainer.sh

WORKDIR /workspace/scripts

ENTRYPOINT ["./run_text_trainer.sh"]
