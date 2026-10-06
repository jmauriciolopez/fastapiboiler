from pathlib import Path

from shared.infrastructure.config.settings import Settings


def test_authentication_secrets_load_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=sqlite:///./test.db\n"
        "JWT_SECRET_KEY=jwt-secret-from-file\n"
        "API_KEY=api-key-from-file\n",
        encoding="utf-8",
    )

    loaded_settings = Settings(_env_file=env_file)

    assert loaded_settings.jwt_secret_key == "jwt-secret-from-file"
    assert loaded_settings.api_key == "api-key-from-file"
