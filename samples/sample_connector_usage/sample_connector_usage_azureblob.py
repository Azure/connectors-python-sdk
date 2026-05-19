# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Azure Blob Storage Connector SDK Sample

This sample demonstrates how to use the Azure Blob Storage connector SDK.

Prerequisites:
1. Azure subscription with Azure Blob Storage connection
2. Azure Blob Storage connection in Connector Namespaces
3. Connection runtime URL from Azure Portal

Note: Azure Blob Storage uses key-based auth (accountName + accessKey), not OAuth.
The connection must be created with parameterValues in a single PUT — no consent link flow.

Installation:
    pip install azure-connectors

Usage:
    Set environment variables:
    $env:AZUREBLOB_CONNECTION_URL = "https://[region].azure-apihub.net/apim/azureblob/[connection-id]"
    $env:TEST_STORAGE_ACCOUNT = "mystorageaccount"
    
    python sample_connector_usage_azureblob.py
"""

import asyncio
import os
from azure.identity.aio import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.azureblob import AzureblobClient, CreateFileInput

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/azureblob/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "AZUREBLOB_CONNECTION_URL",
    ""
)

# Storage account name (dataset parameter in API calls)
STORAGE_ACCOUNT = os.environ.get(
    "TEST_STORAGE_ACCOUNT",
    ""
)


async def example_1_get_blob_metadata():
    """Example 1: Get blob metadata by path."""
    print("\n=== Example 1: Get Blob Metadata ===")
    
    blob_path = os.environ.get("TEST_BLOB_PATH", "")
    if not blob_path:
        print("Set TEST_BLOB_PATH environment variable to a blob path.")
        print("Example: $env:TEST_BLOB_PATH = 'container/folder/file.txt'")
        return
    
    credential = DefaultAzureCredential()
    
    async with AzureblobClient(CONNECTION_RUNTIME_URL, credential) as client:

        metadata = await client.get_file_metadata_by_path_async(
            dataset=STORAGE_ACCOUNT,
            path=blob_path,
        )
        
        if metadata:
            print(f"Blob Metadata for '{blob_path}':")
            print(f"  Name: {metadata.get('Name', 'N/A')}")
            print(f"  Path: {metadata.get('Path', 'N/A')}")
            print(f"  Size: {metadata.get('Size', 'N/A')} bytes")
            print(f"  Last Modified: {metadata.get('LastModified', 'N/A')}")
            print(f"  Media Type: {metadata.get('MediaType', 'N/A')}")
            print(f"  ETag: {metadata.get('ETag', 'N/A')}")
        else:
            print(f"No metadata returned for: {blob_path}")
                



async def example_2_download_blob():
    """Example 2: Download blob content."""
    print("\n=== Example 2: Download Blob Content ===")
    
    blob_path = os.environ.get("TEST_BLOB_PATH", "")
    if not blob_path:
        print("Set TEST_BLOB_PATH environment variable to a blob path.")
        print("Example: $env:TEST_BLOB_PATH = 'container/folder/file.txt'")
        return
    
    credential = DefaultAzureCredential()
    
    async with AzureblobClient(CONNECTION_RUNTIME_URL, credential) as client:
        content = await client.get_file_content_by_path_async(
            dataset=STORAGE_ACCOUNT,
            path=blob_path,
        )
        
        if content:
            file_name = os.path.basename(blob_path)
            print(f"Downloaded blob '{file_name}': {len(content)} bytes")
            
            # Show preview for text files
            if len(content) < 1000:
                try:
                    text_preview = content.decode("utf-8")[:200]
                    print(f"  Preview: {text_preview}...")
                except UnicodeDecodeError:
                    print("  (Binary content)")
        else:
            print(f"No content returned for: {blob_path}")
                


async def example_3_upload_blob():
    """Example 3: Upload a blob."""
    print("\n=== Example 3: Upload Blob ===")
    
    folder_path = os.environ.get("TEST_FOLDER_PATH", "")
    if not folder_path:
        print("Set TEST_FOLDER_PATH environment variable to a container/folder path.")
        print("Example: $env:TEST_FOLDER_PATH = 'mycontainer/uploads'")
        return
    
    blob_name = "sample-upload.txt"
    blob_content = "Hello from Azure Connectors SDK for Python!\nUploaded at: " + \
                   asyncio.get_event_loop().time().__str__()
    
    credential = DefaultAzureCredential()
    
    async with AzureblobClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            # Create input with the file content
            input_data = CreateFileInput()
            input_data.additional_properties["$content"] = blob_content
            input_data.additional_properties["$content-type"] = "text/plain"
            
            metadata = await client.create_file_async(
                input=input_data,
                dataset=STORAGE_ACCOUNT,
                folder_path=folder_path,
                name=blob_name,
            )
            
            if metadata:
                print(f"Uploaded blob '{blob_name}' to '{folder_path}':")
                print(f"  ID: {metadata.get('Id', 'N/A')}")
                print(f"  Path: {metadata.get('Path', 'N/A')}")
                print(f"  Size: {len(blob_content)} bytes")
            else:
                print("Blob uploaded (no metadata returned).")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_4_list_blobs():
    """Example 4: List blobs in a container/folder."""
    print("\n=== Example 4: List Blobs ===")
    
    folder_id = os.environ.get("TEST_FOLDER_ID", "")
    if not folder_id:
        print("Set TEST_FOLDER_ID environment variable to a folder identifier.")
        print("Example: $env:TEST_FOLDER_ID = 'JTJmbXljb250YWluZXI='  (base64 encoded path)")
        print("Or use list_root_folder_async to list root container blobs.")
        
        # Try listing root folder instead
        print("\nListing root folder blobs instead...")
        credential = DefaultAzureCredential()
        
        async with AzureblobClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                blobs = await client.list_root_folder_async(
                    dataset=STORAGE_ACCOUNT,
                )
                
                if blobs and "value" in blobs:
                    print(f"Found {len(blobs['value'])} items in root:")
                    for blob in blobs["value"][:10]:  # Show first 10
                        name = blob.get("Name", "N/A")
                        is_folder = blob.get("IsFolder", False)
                        size = blob.get("Size", 0)
                        item_type = "folder" if is_folder else f"{size} bytes"
                        print(f"  - {name} ({item_type})")
                else:
                    print("No blobs found in root folder.")
                    
            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")
        return
    
    credential = DefaultAzureCredential()
    
    async with AzureblobClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            blobs = await client.list_folder_async(
                dataset=STORAGE_ACCOUNT,
                id=folder_id,
            )
            
            if blobs and "value" in blobs:
                print(f"Found {len(blobs['value'])} items:")
                for blob in blobs["value"][:10]:  # Show first 10
                    name = blob.get("Name", "N/A")
                    is_folder = blob.get("IsFolder", False)
                    size = blob.get("Size", 0)
                    item_type = "folder" if is_folder else f"{size} bytes"
                    print(f"  - {name} ({item_type})")
            else:
                print("No blobs found in folder.")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def example_5_delete_blob():
    """Example 5: Delete a blob."""
    print("\n=== Example 5: Delete Blob ===")
    
    blob_id = os.environ.get("TEST_BLOB_ID", "")
    if not blob_id:
        print("Set TEST_BLOB_ID environment variable to a blob identifier.")
        print("Example: $env:TEST_BLOB_ID = 'JTJmbXljb250YWluZXIlMmZmaWxlLnR4dA=='")
        print("You can get blob IDs from the list_folder_async response.")
        return
    
    credential = DefaultAzureCredential()
    
    async with AzureblobClient(CONNECTION_RUNTIME_URL, credential) as client:
        try:
            await client.delete_file_async(
                dataset=STORAGE_ACCOUNT,
                id=blob_id,
            )
            
            print(f"Successfully deleted blob: {blob_id}")
                
        except ConnectorException as ex:
            print(f"Connector error: {ex}")
        except Exception as ex:
            print(f"Error: {ex}")


async def main():
    """Run all examples."""
    print("Azure Blob Storage Connector SDK - Sample Usage")
    print("=" * 60)
    
    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: AZUREBLOB_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/azureblob/[connection-id]")
        return
    
    if not STORAGE_ACCOUNT:
        print("\nWARNING: TEST_STORAGE_ACCOUNT environment variable not set.")
        print("Set it to your storage account name.")
        return
    
    await example_1_get_blob_metadata()
    await example_2_download_blob()
    await example_3_upload_blob()
    await example_4_list_blobs()
    await example_5_delete_blob()
    
    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    asyncio.run(main())
