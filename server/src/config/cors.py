from litestar.config.cors import CORSConfig

cors_config = CORSConfig(
    allow_origins=["http://localhost:8100"],
    allow_methods=["POST", "GET", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Origin", "Content-Type", "Authorization", "Access-Control-Allow-Headers", "Access-Control-Request-Method", "Access-Control-Request-Headers"],
    expose_headers=["Content-Length", "Access-Control-Allow-Headers", "Access-Control-Request-Method", "Access-Control-Request-Headers"],
    allow_credentials=True
)