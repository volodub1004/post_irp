# Builder - has GLIBC 2.39 for CatBoost
FROM ubuntu:24.04 AS builder

WORKDIR /build

# Install Python 3.12 and deps
RUN apt-get update && apt-get install -y \
    python3.12 python3.12-dev python3.12-venv python3-pip \
    wget unzip g++ make libicu-dev git libmsgpack-dev \
    libcurl4-openssl-dev pkg-config \
    nlohmann-json3-dev \
    ninja-build \
    clang \
    lld \
    && rm -f /usr/bin/python /usr/bin/python3 \
    && ln -s /usr/bin/python3.12 /usr/bin/python \
    && ln -s /usr/bin/python3.12 /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

# Download and install CMake 3.28.0 (LightGBM needs this version)
RUN wget https://github.com/Kitware/CMake/releases/download/v3.28.0/cmake-3.28.0-linux-x86_64.tar.gz \
    && tar -xzf cmake-3.28.0-linux-x86_64.tar.gz --strip-components=1 -C /usr/local \
    && rm cmake-3.28.0-linux-x86_64.tar.gz

# Install build-time Python packages pybind11 + Conan
RUN pip install pybind11 "conan>=2.4.1" --break-system-packages

# Clone git submodules (they're not included in Docker build context)
WORKDIR /build
RUN git clone --depth 1 --recurse-submodules https://github.com/microsoft/LightGBM.git LightGBM || \
    (echo "Warning: LightGBM clone failed" && mkdir -p LightGBM)
RUN git clone --depth 1 --recurse-submodules https://github.com/catboost/catboost.git catboost || \
    (echo "Warning: CatBoost clone failed" && mkdir -p catboost)
RUN git clone --depth 1 https://github.com/rapidfuzz/rapidfuzz-cpp.git rapid_fuzz || \
    (echo "Warning: rapid_fuzz clone failed" && mkdir -p rapid_fuzz)

# Copy build across
COPY cpp /build/cpp
COPY CMakeLists.txt /build/

ENV CMAKE_PREFIX_PATH="/usr/local/lib/python3.12/site-packages/pybind11/share/cmake/pybind11"

# Build CatBoost inside the container
RUN cd /build/catboost && \
    python3 build/build_native.py \
      --build-root-dir $(pwd)/catboost_native_build \
      --targets catboostmodel \
      --build-type Release \
      --parallel-build-jobs $(nproc)

# Make
RUN cmake . && make -j

# FastAPI runtime
FROM ubuntu:24.04 AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.12 python3.12-venv python3-pip \
    libicu-dev libgomp1 libstdc++6 libc6 \
    libcurl4 ca-certificates \
    && rm -f /usr/bin/python /usr/bin/python3 \
    && ln -s /usr/bin/python3.12 /usr/bin/python \
    && ln -s /usr/bin/python3.12 /usr/bin/python3 \
    && pip install --timeout=300 --retries=5 fastapi uvicorn --break-system-packages \
    && rm -rf /var/lib/apt/lists/*

# Copy FastAPI code
COPY api /app/api

# Create the build directory structure
RUN mkdir -p /app/build/cpp

# Copy the built .so from builder
COPY --from=builder /build/cpp/email_predictor*.so /app/build/cpp/

# Copy dynamic dependencies
COPY --from=builder /build/LightGBM/lib_lightgbm.so /app/build/cpp/
COPY --from=builder /build/catboost/catboost_native_build/catboost/libs/model_interface/libcatboostmodel.so /app/build/cpp/

# Copy data + models
COPY cpp/model /app/cpp/model
COPY cpp/data /app/cpp/data

# Set environment variables
ENV PYTHONPATH=/app
ENV LD_LIBRARY_PATH=/app/build/cpp

# Verify libraries can be found
RUN ldconfig -p | grep -E "(libcatboost|lib_lightgbm)" || echo "Libraries not in system path, relying on LD_LIBRARY_PATH"

# Test that the library can be loaded
RUN python3 -c "import sys; sys.path.append('/app'); import ctypes; ctypes.CDLL('/app/build/cpp/libcatboostmodel.so')" || echo "Direct library load test failed"

# Start FastAPI
CMD ["uvicorn", "api.rest_api:app", "--host", "0.0.0.0", "--port", "8000"]