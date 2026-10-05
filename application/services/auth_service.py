from application.ports.password_hasher import PasswordHasher
from application.ports.token_service import TokenServicePort
from domain.exceptions.auth_exceptions import InvalidCredentialsException
from domain.repositories.user_repository import UserRepositoryPort
from application.ports.logger import LoggerPort


class AuthService:
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        password_hasher: PasswordHasher,
        token_service: TokenServicePort,
        logger: LoggerPort,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.logger = logger

    def login(self, username: str, password: str) -> str:
        self.logger.info(f"Intento de login para usuario: {username}")
        user = self.user_repository.get_by_username(username)
        if not user:
            self.logger.warning(f"Login fallido: usuario {username} no encontrado")
            raise InvalidCredentialsException()

        if not self.password_hasher.verify(password, user.hashed_password):
            self.logger.warning(f"Login fallido: contraseña incorrecta para {username}")
            raise InvalidCredentialsException()

        # Generar token con el ID del usuario y username (puedes agregar roles si lo deseas)
        payload = {
            "sub": str(user.id),
            "username": user.username,
        }
        self.logger.info(f"Login exitoso para usuario: {username}")
        return self.token_service.generate_token(payload)
