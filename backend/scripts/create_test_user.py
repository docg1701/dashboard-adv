# backend/app/create_test_user.py
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession # Import AsyncSession for type hint
from sqlalchemy.future import select # Import select for async queries
from sqlalchemy.exc import IntegrityError
import os
import sys

# Adiciona o diretório 'backend' ao sys.path para permitir imports da 'app'
# Isso torna o script executável de qualquer lugar, desde que o CWD seja a raiz do projeto.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Use absolute imports again
from app.core.database import async_session_local # Absolute import - Use ASYNC session maker
from app.models.user import User                  # Absolute import
from app.models.enums import UserRole             # Absolute import
from app.core.security import hash_password       # Absolute import

# --- User details to create (as specified by user) ---
TEST_USER_EMAIL = "user@gmail.com"
TEST_USER_PASSWORD = "user@gmail.com" # Consider changing this later
TEST_USER_ROLE = UserRole.USER
# -----------------------------

async def create_user():
    print("Attempting to create test user...")
    if not async_session_local:
         print("Error: async_session_local is not configured in core.database.")
         return

    # Use async context manager for the session
    async with async_session_local() as db: # db type is AsyncSession
        try:
            # Check if user already exists using async query
            result = await db.execute(
                select(User).filter_by(email=TEST_USER_EMAIL)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"User with email {TEST_USER_EMAIL} already exists.")
                return

            # Create new user object
            hashed_password = hash_password(TEST_USER_PASSWORD)
            new_user = User(
                email=TEST_USER_EMAIL,
                hashed_password=hashed_password,
                role=TEST_USER_ROLE,
                is_active=True # Ensure user is active
            )
            db.add(new_user)
            await db.commit() # Await commit
            await db.refresh(new_user) # Await refresh
            print(f"Successfully created user: {TEST_USER_EMAIL} with role: {TEST_USER_ROLE.value}")

        except IntegrityError:
            await db.rollback() # Await rollback
            print(f"Failed to create user {TEST_USER_EMAIL}. IntegrityError.")
        except Exception as e:
            await db.rollback() # Await rollback
            print(f"An error occurred: {e}", exc_info=True) # Add exc_info for more details
        # Session is automatically closed/handled by async context manager

async def main():
    await create_user()

if __name__ == "__main__":
    print("Running user creation script...")
    if 'async_session_local' in locals() and async_session_local is not None:
        # Check if async_session_local was initialized correctly
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"An unexpected error occurred during script execution: {e}")
    else:
        # This case might happen if database.py had an error during initialization
        print("Cannot run main(): async_session_local is not defined or not initialized.")
        print("Check for errors during application startup or in core/database.py.")

    print("Script finished.")