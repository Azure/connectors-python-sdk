# Copyright (c) Microsoft Corporation. All rights reserved.

"""
Sample program demonstrating how to use the Connector SDK with generated connector clients.

This sample shows the usage pattern. For actual usage, you need to:
1. Generate connector code using LogicAppsCompiler CLI (see GENERATION.md)
2. Install the SDK: pip install <TBD>
3. Use the generated typed client classes
"""

import asyncio
import os
from typing import Optional


async def main():
    """Entry point for the sample application."""
    print("Azure Logic Apps Connector SDK - Sample Usage (Python)")
    print("======================================================")
    print()

    # Example 1: SDK Runtime Components
    print("Example 1: SDK Runtime Components")
    print("----------------------------------")
    print("The SDK provides runtime infrastructure for generated connector clients:")
    print()
    print("  Authentication:")
    print("    - ManagedIdentityTokenProvider: For Azure-hosted apps")
    print("    - ConnectionStringTokenProvider: For local development")
    print()
    print("  HTTP:")
    print("    - ConnectorHttpClient: Async HTTP client with aiohttp")
    print("    - Automatic retry and error handling")
    print()
    print("  Base Classes:")
    print("    - ConnectorClientBase: Base class for all generated clients")
    print("    - ConnectorClientOptions: Configuration options")
    print()

    # Example 2: Token Provider Usage
    print("Example 2: Token Provider Usage")
    print("-------------------------------")

    try:
        # Import the SDK (demonstrates that it's installed)
        from azure_workflows_connectors_sdk import (
            ManagedIdentityTokenProvider,
            ConnectionStringTokenProvider,
        )

        # Managed Identity for Azure-hosted scenarios
        print("  Managed Identity (for Azure-hosted apps):")
        print("    from azure_workflows_connectors_sdk import ManagedIdentityTokenProvider")
        print("    token_provider = ManagedIdentityTokenProvider()")
        print("    token = await token_provider.get_access_token_async(scopes)")
        print()

        # Connection String for local development
        api_key = os.environ.get("CONNECTOR_API_KEY", "demo-key")
        connection_token_provider = ConnectionStringTokenProvider(api_key)
        print("  Connection String (for local development):")
        print("    token_provider = ConnectionStringTokenProvider(api_key)")
        print(f"    Created with key: {api_key[:min(4, len(api_key))]}...")
    except ImportError:
        print("  Note: <TBD> not installed")
        print("  Run: pip install <TBD>")
    except Exception as ex:
        print(f"  Error: {ex}")

    print()

    # Example 3: Generated Client Usage Pattern
    print("Example 3: Generated Client Usage Pattern")
    print("------------------------------------------")
    print("After generating connector code with LogicAppsCompiler CLI:")
    print()
    print("  # Using generated Office365Client (from office365_client.py)")
    print("  from azure_workflows_connectors_sdk.generated.office365_client import (")
    print("      Office365Client, ClientSendHtmlMessage")
    print("  )")
    print("  from azure_workflows_connectors_sdk import ManagedIdentityTokenProvider")
    print()
    print("  # Create the client with connection runtime URL")
    print("  connection_runtime_url = 'https://...'  # From Azure Portal")
    print("  token_provider = ManagedIdentityTokenProvider()")
    print()
    print("  async with Office365Client(connection_runtime_url, token_provider) as client:")
    print("      # Call typed operations with request dataclasses")
    print("      email = ClientSendHtmlMessage(")
    print("          to='recipient@example.com',")
    print("          subject='Hello from SDK',")
    print("          body='<p>Email body</p>',")
    print("      )")
    print("      await client.send_email_v2_async(email)")
    print()
    print("      categories = await client.get_outlook_category_names_async()")
    print()

    # Example 4: Generation Instructions
    print("Example 4: How to Generate Connector Code")
    print("------------------------------------------")
    print("Use the LogicAppsCompiler CLI from the BPM repository:")
    print()
    print("  # Build the generator")
    print("  dotnet build .\\src\\tools\\CodefulSdkGenerator\\LogicAppsCompiler.Cli -c Release")
    print()
    print("  # Generate Office365 connector (Python)")
    print("  cd src\\tools\\CodefulSdkGenerator\\LogicAppsCompiler.Cli\\bin\\Release")
    print('  .\\LogicAppsCompiler.exe "..\\..\\..\\..\\..\\..\\PythonSDK\\src\\azure_workflows_connectors_sdk\\generated" --pythonDirectClient --connectors=office365')
    print()
    print("See PythonSDK/GENERATION.md for complete documentation.")
    print()

    # Example 5: Integration with Azure Functions
    print("Example 5: Azure Functions Integration (Python)")
    print("------------------------------------------------")
    print("The generated clients work well with Azure Functions:")
    print()
    print("  import azure.functions as func")
    print("  from azure_workflows_connectors_sdk.generated.office365_client import Office365Client")
    print("  from azure_workflows_connectors_sdk import ManagedIdentityTokenProvider")
    print()
    print("  app = func.FunctionApp()")
    print()
    print("  @app.route(route='send-email', auth_level=func.AuthLevel.FUNCTION)")
    print("  async def send_email(req: func.HttpRequest) -> func.HttpResponse:")
    print("      connection_url = os.environ['CONNECTION_RUNTIME_URL']")
    print("      token_provider = ManagedIdentityTokenProvider()")
    print()
    print("      async with Office365Client(connection_url, token_provider) as client:")
    print("          email = ClientSendHtmlMessage(")
    print("              to=req.params.get('to'),")
    print("              subject='Hello from Azure Function',")
    print("              body='<p>Sent from Python!</p>',")
    print("          )")
    print("          await client.send_email_v2_async(email)")
    print()
    print("      return func.HttpResponse('Email sent!', status_code=200)")
    print()

    # Example 6: Async Context Manager Pattern
    print("Example 6: Async Context Manager Pattern")
    print("-----------------------------------------")
    print("All generated clients support async context managers:")
    print()
    print("  # Automatic cleanup with context manager")
    print("  async with Office365Client(url, token_provider) as client:")
    print("      email = ClientSendHtmlMessage(to='...', subject='...', body='...')")
    print("      await client.send_email_v2_async(email)")
    print("  # Client automatically closed after exiting context")
    print()
    print("  # Manual lifecycle management")
    print("  client = Office365Client(url, token_provider)")
    print("  try:")
    print("      email = ClientSendHtmlMessage(to='...', subject='...', body='...')")
    print("      await client.send_email_v2_async(email)")
    print("  finally:")
    print("      await client.close()")
    print()

    # Example 7: Error Handling
    print("Example 7: Error Handling")
    print("-------------------------")
    print("The SDK provides structured error handling:")
    print()
    print("  from azure_workflows_connectors_sdk import ConnectorException")
    print("  from azure_workflows_connectors_sdk.generated.office365_client import (")
    print("      Office365Client, ClientSendHtmlMessage")
    print("  )")
    print()
    print("  try:")
    print("      async with Office365Client(url, token_provider) as client:")
    print("          email = ClientSendHtmlMessage(to='...', subject='...', body='...')")
    print("          await client.send_email_v2_async(email)")
    print("  except ConnectorException as ex:")
    print("      print(f'Connector error: {ex.message}')")
    print("      print(f'Status code: {ex.status_code}')")
    print("      print(f'Error body: {ex.error_body}')")
    print()

    print("Sample completed successfully!")
    print()
    print("Next steps:")
    print("  1. Run LogicAppsCompiler CLI to generate connector code")
    print("  2. Install the SDK: pip install <TBD>")
    print("  3. Use typed clients with the connection runtime URL from Azure Portal")
    print("  4. Deploy to Azure Functions or run locally")


if __name__ == "__main__":
    asyncio.run(main())