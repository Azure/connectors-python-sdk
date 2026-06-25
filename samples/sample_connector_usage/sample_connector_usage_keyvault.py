# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Key Vault Connector SDK Sample

This sample demonstrates how to use the Azure Key Vault connector SDK to
manage keys and secrets.

Prerequisites:
1. Azure subscription with Azure Key Vault connection
2. Key Vault connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:KEYVAULT_CONNECTION_URL = "https://[region].azure-apihub.net/apim/keyvault/[connection-id]"

    python sample_connector_usage_keyvault.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.keyvault import (
    KeyvaultClient,
    KeyEncryptInput,
    KeyDecryptInput,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/keyvault/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "KEYVAULT_CONNECTION_URL",
    ""
)

# Sample key and secret names (replace with your own)
KEY_NAME = os.environ.get("KEYVAULT_KEY_NAME", "my-encryption-key")
SECRET_NAME = os.environ.get("KEYVAULT_SECRET_NAME", "my-secret")


async def example_1_list_keys():
    """Example 1: List all keys in the vault."""
    print("\n=== Example 1: List Keys ===")

    credential = DefaultAzureCredential()

    async with KeyvaultClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_keys_async()

            if result and result.get("value"):
                keys = result["value"]
                print(f"Found {len(keys)} keys:")
                for key in keys:
                    print(f"  - {key.get('name')} (enabled: {key.get('is_enabled')})")
            else:
                print("No keys found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_2_get_key_metadata():
    """Example 2: Get metadata for a specific key."""
    print("\n=== Example 2: Get Key Metadata ===")

    credential = DefaultAzureCredential()

    async with KeyvaultClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_key_metadata_async(key_name=KEY_NAME)

            if result:
                print(f"Key Name: {result.get('name')}")
                print(f"Version: {result.get('version')}")
                print(f"Key Type: {result.get('key_type')}")
                print(f"Enabled: {result.get('is_enabled')}")
                print(f"Created: {result.get('created_time')}")
                if result.get('allowed_operations'):
                    print(f"Allowed Operations: {', '.join(result['allowed_operations'])}")
            else:
                print(f"Key '{KEY_NAME}' not found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_3_encrypt_decrypt():
    """Example 3: Encrypt and decrypt data using a key."""
    print("\n=== Example 3: Encrypt and Decrypt Data ===")

    credential = DefaultAzureCredential()

    async with KeyvaultClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Encrypt data
            plaintext = "Hello, Azure Key Vault!"
            print(f"Original text: {plaintext}")

            encrypt_input = KeyEncryptInput(
                algorithm="RSA-OAEP",
                raw_data=plaintext
            )
            encrypt_result = await client.encrypt_data_async(
                input=encrypt_input,
                key_name=KEY_NAME
            )

            if encrypt_result:
                encrypted = encrypt_result.get("encrypted_data")
                print(f"Encrypted: {encrypted[:50]}..." if encrypted else "No result")

                # Decrypt data
                decrypt_input = KeyDecryptInput(
                    algorithm="RSA-OAEP",
                    encrypted_data=encrypted
                )
                decrypt_result = await client.decrypt_data_async(
                    input=decrypt_input,
                    key_name=KEY_NAME
                )

                if decrypt_result:
                    decrypted = decrypt_result.get("raw_data")
                    print(f"Decrypted: {decrypted}")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_list_secrets():
    """Example 4: List all secrets in the vault."""
    print("\n=== Example 4: List Secrets ===")

    credential = DefaultAzureCredential()

    async with KeyvaultClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.list_secrets_async()

            if result and result.get("value"):
                secrets = result["value"]
                print(f"Found {len(secrets)} secrets:")
                for _ in secrets:
                    print("  - [REDACTED]")
            else:
                print("No secrets found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_get_secret():
    """Example 5: Get a secret value."""
    print("\n=== Example 5: Get Secret ===")

    credential = DefaultAzureCredential()

    async with KeyvaultClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_secret_async(secret_name=SECRET_NAME)

            if result:
                print(f"Secret Name: {result.get('name')}")
                print(f"Content Type: {result.get('content_type')}")
                # Note: Be careful with secret values in logs
                value = result.get("value", "")
                masked = value[:3] + "***" if len(value) > 3 else "***"
                print(f"Value (masked): {masked}")
            else:
                print("Secret not found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_6_get_secret_metadata():
    """Example 6: Get secret metadata without the value."""
    print("\n=== Example 6: Get Secret Metadata ===")

    credential = DefaultAzureCredential()

    async with KeyvaultClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            result = await client.get_secret_metadata_async(
                secret_name=SECRET_NAME
            )

            if result:
                print(f"Secret Name: {result.get('name')}")
                print(f"Version: {result.get('version')}")
                print(f"Content Type: {result.get('content_type')}")
                print(f"Enabled: {result.get('is_enabled')}")
                print(f"Created: {result.get('created_time')}")
                print(f"Updated: {result.get('last_updated_time')}")
            else:
                print("Secret not found")

        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    if not CONNECTION_RUNTIME_URL:
        print("Error: KEYVAULT_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL from Azure Portal.")
        return

    print(f"Using connection URL: {CONNECTION_RUNTIME_URL[:50]}...")

    # Run read-only examples by default
    await example_1_list_keys()
    await example_2_get_key_metadata()
    await example_4_list_secrets()
    await example_5_get_secret()
    await example_6_get_secret_metadata()

    # Uncomment to run encryption/decryption example:
    # await example_3_encrypt_decrypt()

    print("\n=== All examples completed ===")


if __name__ == "__main__":
    asyncio.run(main())
