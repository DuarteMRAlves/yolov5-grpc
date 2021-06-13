# Define workdir folder for all stages
# Must be renewed in the beggining of each stage
ARG WORKSPACE=/workspace
ARG PROTO_FILE=visualization_service.proto
ARG SRC=visualization

# --------------------------------------
# Builder stage to generate .proto files
# --------------------------------------

FROM python:3.9.5-slim-buster as builder
# Renew build args
ARG WORKSPACE
ARG PROTO_FILE
ARG SRC

COPY ${SRC}/requirements-build.txt ${WORKSPACE}/

WORKDIR ${WORKSPACE}

RUN pip install --upgrade pip && \
    pip install -r requirements-build.txt && \
    rm requirements-build.txt

# Path for the protos folder to copy
ARG PROTOS_FOLDER_DIR=protos

COPY ${PROTOS_FOLDER_DIR}/${PROTO_FILE} ${WORKSPACE}/

# Compile proto file
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. ${PROTO_FILE}

# -----------------------------
# Stage to generate final image
# -----------------------------

FROM python:3.9.5-slim-buster
# Renew build args
ARG WORKSPACE
ARG PROTO_FILE
ARG SRC

ARG USER=worker
ARG GROUP=workers

# Create non-privileged user to run
RUN addgroup --system ${GROUP} && \
    adduser --system --no-create-home --ingroup ${GROUP} ${USER} && \
    mkdir ${WORKSPACE} && \
    chown -R ${USER}:${GROUP} ${WORKSPACE}

COPY ${SRC}/requirements.txt ${WORKSPACE}/

WORKDIR ${WORKSPACE}

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

# COPY .proto file to root to meet ai4eu specifications
COPY --from=builder --chown=${USER}:${GROUP} ${WORKSPACE}/${PROTO_FILE} /

# Copy generated .py files to workspace
COPY --from=builder --chown=${USER}:${GROUP} ${WORKSPACE}/*.py ${WORKSPACE}/

# Copy code to workspace
COPY --chown=${USER}:${GROUP} ${SRC} ${WORKSPACE}/

# Change to non-privileged user
USER ${USER}

# Expose port 8061 according to ai4eu specifications
EXPOSE 8061
# Expose 8062 for web visualization
EXPOSE 8062

CMD ["gunicorn", \
    "--threads", "4", \
    "--workers", "1", \
    "--bind", "0.0.0.0:8062", \
    "app:create_app()"]