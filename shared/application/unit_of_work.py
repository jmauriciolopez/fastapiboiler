"""Unit of Work — owns the transaction boundary for a single use-case.

Services call ``uow.commit()`` after all mutations are complete.
Repositories no longer call ``session.commit()`` themselves; they only
flush/add to the session, letting the UoW decide when to finalise.
"""

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Thin wrapper around an :class:`AsyncSession` that owns commit/rollback."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self) -> None:
        """Flush pending changes to the DB without committing."""
        await self._session.flush()
