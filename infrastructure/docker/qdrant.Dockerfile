# Production Dockerfile for Qdrant Vector Database
# Optimized for AWS ECS Fargate deployment

FROM qdrant/qdrant:latest

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:6333/health || exit 1

# Expose ports
EXPOSE 6333 6334

# Use persistent storage
VOLUME ["/qdrant/storage"]

# Production configuration
ENV QDRANT__SERVICE__GRPC_PORT=6334
ENV QDRANT__LOG_LEVEL=INFO

# Start Qdrant
CMD ["./qdrant"]
