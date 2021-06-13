ARG USER=worker
ARG GROUP=workers
ARG WORKSPACE=/workspace
ARG PROTO_FILE=yolov5_service.proto
ARG SRC_DIR=yolov5

# -------------------------------
# Builder to generate python code
# -------------------------------
FROM python:3.6.12-slim-buster AS proto_builder
# Renew build args
ARG WORKSPACE
ARG PROTO_FILE

ARG PROTOS_FOLDER_DIR=protos

RUN pip install --upgrade pip && \
    pip install grpcio==1.35.0 grpcio-tools==1.35.0 protobuf==3.14.0

COPY ${PROTOS_FOLDER_DIR} ${WORKSPACE}/
WORKDIR ${WORKSPACE}/

# Compile proto file and remove it
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ${PROTO_FILE}


# ----------------------------------
# Builder to download model to cache
# ----------------------------------
FROM ultralytics/yolov5:latest as cache_builder
# Renew build args
ARG USER
ARG GROUP
ARG WORKSPACE
ARG PROTO_FILE
ARG SRC_DIR

WORKDIR ${WORKSPACE}/

# Create non-privileged user to run
RUN addgroup --system ${GROUP} && \
    adduser --system --ingroup ${GROUP} ${USER} && \
    chown -R ${USER}:${GROUP} ${WORKSPACE}

# Copy script to load cache
COPY --chown=${USER}:${GROUP} ${SRC_DIR}/load_cache.py .

# Change to non-privileged user so that cache files go to user home
USER ${USER}

ENV HOME=/home/${USER}

# Import model to user cache
RUN python load_cache.py

# ------------------------------
# Final image to run the service
# ------------------------------
#FROM pytorch/pytorch:1.7.1-cuda11.0-cudnn8-runtime
FROM ultralytics/yolov5:latest
# Renew build args
ARG USER
ARG GROUP
ARG WORKSPACE
ARG PROTO_FILE
ARG SRC_DIR

WORKDIR ${WORKSPACE}/

# Create non-privileged user to run
RUN addgroup --system ${GROUP} && \
    adduser --system --ingroup ${GROUP} ${USER} && \
    chown -R ${USER}:${GROUP} ${WORKSPACE}

RUN pip install --upgrade pip && \
    pip install grpcio==1.35.0 grpcio-reflection==1.35.0

# COPY .proto file to root to meet ai4eu specifications
COPY --from=proto_builder --chown=${USER}:${GROUP} ${WORKSPACE}/${PROTO_FILE} /

# Copy generated code to workspace
COPY --from=proto_builder --chown=${USER}:${GROUP} ${WORKSPACE}/*.py ${WORKSPACE}/

# Copy cache
COPY --from=cache_builder --chown=${USER}:${GROUP} /home/${USER}/.cache/torch/ /home/${USER}/.cache/torch/

# Copy modet .pt file
COPY --from=cache_builder --chown=${USER}:${GROUP} ${WORKSPACE}/*.pt ${WORKSPACE}/

# Copy code
COPY --chown=${USER}:${GROUP} ${SRC_DIR}/yolov5_service.py .

# Change to non-privileged user
USER ${USER}

ENV HOME=/home/${USER}

# Expose port 8061 according to ai4eu specifications
EXPOSE 8061

WORKDIR ${WORKSPACE}/

CMD ["python", "yolov5_service.py", "run"]