import logging
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from src.core.config import settings

logger = logging.getLogger(__name__)

API_KEY_NAME = "X-Internal-API-Key"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key_header: str = Security(api_key_header_auth)):
    """
    Verifies the provided API key from the request header against the one in settings.
    Raises HTTPException 401 if the key is invalid or missing.
    """
    if not settings.INTERNAL_API_KEY:
        logger.critical("INTERNAL_API_KEY is not configured in settings. API cannot be secured.")
        # This is a server configuration error. Depending on policy,
        # you might allow requests in dev or strictly deny.
        # Forcing denial is safer.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key security is not configured on the server.",
        )

    if api_key_header == settings.INTERNAL_API_KEY:
        logger.debug(f"'{API_KEY_NAME}' verified successfully.")
        return True # API key is valid
    else:
        logger.warning(f"Invalid '{API_KEY_NAME}' received. Access denied.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key.",
        )

if __name__ == "__main__":
    # This part is for basic demonstration if you run this file directly.
    # In a real scenario, FastAPI handles the Security dependency.

    # Mock settings for testing this function directly (not a real test case)
    class MockSettings:
        INTERNAL_API_KEY: str | None = "test_secret_key"

    original_settings = settings # Save original
    # settings = MockSettings() # type: ignore # Temporarily override for local test

    async def test_verify():
        print(f"Current settings.INTERNAL_API_KEY: {settings.INTERNAL_API_KEY}")
        if not settings.INTERNAL_API_KEY:
            print("Skipping direct test: INTERNAL_API_KEY not set in actual settings loaded by Pydantic.")
            return

        valid_key = settings.INTERNAL_API_KEY
        invalid_key = "wrong_key"

        print(f"\nTesting with valid key: {valid_key}")
        try:
            await verify_api_key(valid_key)
            print("Valid key check: PASSED")
        except HTTPException as e:
            print(f"Valid key check: FAILED with {e.detail}")

        print(f"\nTesting with invalid key: {invalid_key}")
        try:
            await verify_api_key(invalid_key)
            print("Invalid key check: FAILED (should have raised HTTPException)")
        except HTTPException as e:
            if e.status_code == status.HTTP_401_UNAUTHORIZED:
                print(f"Invalid key check: PASSED (Correctly raised 401 - {e.detail})")
            else:
                print(f"Invalid key check: FAILED with unexpected status {e.status_code} - {e.detail}")

        # Test missing key (FastAPI's Security wrapper handles this by not calling if auto_error=False,
        # or by raising its own 403 if auto_error=True and header is missing.
        # Direct call like this doesn't fully simulate FastAPI's behavior for missing header)
        print(f"\nTesting with missing key (simulated by empty string):")
        try:
            await verify_api_key("") # Simulating a provided but empty key
            print("Missing key check (empty string): FAILED (should have raised HTTPException)")
        except HTTPException as e:
             if e.status_code == status.HTTP_401_UNAUTHORIZED:
                print(f"Missing key check (empty string): PASSED (Correctly raised 401 - {e.detail})")
             else:
                print(f"Missing key check (empty string): FAILED with unexpected status {e.status_code} - {e.detail}")

    # settings = original_settings # Restore original settings

    # To run this test, you'd need an asyncio event loop:
    # import asyncio
    # asyncio.run(test_verify())
    # And ensure your .env has INTERNAL_API_KEY set.
    # For now, this __main__ is more illustrative.
    pass
