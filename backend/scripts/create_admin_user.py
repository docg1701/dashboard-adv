import asyncio
import logging
import sys
import os

# Adiciona o diretório 'backend' ao sys.path para permitir imports da 'app'
# Isso torna o script executável de qualquer lugar, desde que o CWD seja a raiz do projeto.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# --- CONFIGURAÇÃO DE LOG PRIMEIRO ---
# Este bloco DEVE ser a primeira coisa a ser executada para garantir que um
# logger esteja configurado antes que qualquer módulo da aplicação (que pode usar o logger)
# seja importado.
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# --- FIM DA CONFIGURAÇÃO DE LOG ---

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Agora, importe os módulos da aplicação
from app.core.database import get_db_contextmanager
from app.models.user import User
from app.models.enums import UserRole
# Corrigido para usar 'hash_password' como no seu arquivo original
from app.core.security import hash_password

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin@gmail.com" # Script will hash this

async def create_initial_admin_user():
    logger.info("Attempting to create initial admin user...")

    async with get_db_contextmanager() as db: # Use the context manager for session
        # Check if admin user already exists
        stmt = select(User).where(User.email == ADMIN_EMAIL)
        result = await db.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            logger.info(f"User with email {ADMIN_EMAIL} already exists. Role: {existing_user.role}. Active: {existing_user.is_active}")
            if existing_user.role != UserRole.ADMIN:
                logger.info(f"User {ADMIN_EMAIL} exists but is not an ADMIN. Updating role to ADMIN.")
                existing_user.role = UserRole.ADMIN
                db.add(existing_user)
                await db.commit()
                await db.refresh(existing_user)
                logger.info("User role updated to ADMIN.")
            if not existing_user.is_active:
                logger.info(f"User {ADMIN_EMAIL} exists but is not active. Activating user.")
                existing_user.is_active = True
                db.add(existing_user)
                await db.commit()
                await db.refresh(existing_user)
                logger.info("User activated.")
            return

        # If user does not exist, create new admin user
        logger.info(f"Creating new admin user: {ADMIN_EMAIL}")
        hashed_admin_password = hash_password(ADMIN_PASSWORD)

        new_admin_user = User(
            email=ADMIN_EMAIL,
            hashed_password=hashed_admin_password,
            role=UserRole.ADMIN,
            is_active=True
            # A linha 'full_name' foi removida pois não existe no modelo User.
        )

        db.add(new_admin_user)
        await db.commit()
        await db.refresh(new_admin_user)
        logger.info(f"Admin user {ADMIN_EMAIL} created successfully.")

async def main():
    await create_initial_admin_user()

if __name__ == "__main__":
    logger.info("Running admin user creation script...")
    asyncio.run(main())
    logger.info("Script finished.")
