# Copyright (c) Microsoft Corporation. All rights reserved.

"""
SMTP sample for the Azure Connectors Python SDK

This sample demonstrates how to use the SMTP client from the Azure Connectors Python SDK.

Prerequisites:
1. Azure subscription with SMTP connection
2. SMTP connection in Connector Namespaces (with credentials configured)
3. Connection runtime URL from Azure Portal

Installation:
    pip install azure-connectors

Usage:
    Set environment variable:
    $env:SMTP_CONNECTION_URL = "https://[region].azure-apihub.net/apim/smtp/[connection-id]"

    python sample_connector_usage_smtp.py
"""
import base64
import os
from azure.identity import DefaultAzureCredential
from azure.connectors import ConnectorException
from azure.connectors.smtp import (
    SmtpClient,
    Email,
    Attachment,
)

# Connection runtime URL format:
# https://[region].azure-apihub.net/apim/smtp/[connection-id]
CONNECTION_RUNTIME_URL = os.environ.get(
    "SMTP_CONNECTION_URL",
    ""
)


def example_1_send_basic_email():
    """Example 1: Send a basic email."""
    print("\n=== Example 1: Send Basic Email ===")

    sender = os.environ.get("TEST_SMTP_FROM", "")
    recipient = os.environ.get("TEST_SMTP_TO", "")

    if not sender or not recipient:
        print("Set environment variables to send an email:")
        print("  $env:TEST_SMTP_FROM = 'sender@yourdomain.com'")
        print("  $env:TEST_SMTP_TO = 'recipient@example.com'")
        return

    with DefaultAzureCredential() as credential:

        with SmtpClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                email = Email(
                    from_=sender,
                    to=recipient,
                    subject="Test Email from Azure Connectors SDK",
                    body="Hello! This is a test email sent via the Azure Connectors SDK for Python.",
                )

                client.send_email(input=email)

                print("Email sent successfully:")
                print(f"  From: {sender}")
                print(f"  To: {recipient}")
                print(f"  Subject: {email.subject}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_2_send_email_with_cc_bcc():
    """Example 2: Send an email with CC and BCC recipients."""
    print("\n=== Example 2: Send Email with CC/BCC ===")

    sender = os.environ.get("TEST_SMTP_FROM", "")
    recipient = os.environ.get("TEST_SMTP_TO", "")
    cc_recipient = os.environ.get("TEST_SMTP_CC", "")
    bcc_recipient = os.environ.get("TEST_SMTP_BCC", "")

    if not sender or not recipient:
        print("Set environment variables to send an email:")
        print("  $env:TEST_SMTP_FROM = 'sender@yourdomain.com'")
        print("  $env:TEST_SMTP_TO = 'recipient@example.com'")
        print("  $env:TEST_SMTP_CC = 'cc@example.com'  (optional)")
        print("  $env:TEST_SMTP_BCC = 'bcc@example.com'  (optional)")
        return

    with DefaultAzureCredential() as credential:

        with SmtpClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                email = Email(
                    from_=sender,
                    to=recipient,
                    c_c=cc_recipient if cc_recipient else None,
                    bcc=bcc_recipient if bcc_recipient else None,
                    subject="Test Email with CC/BCC",
                    body="This email demonstrates CC and BCC functionality.",
                )

                client.send_email(input=email)

                print("Email sent successfully:")
                print(f"  From: {sender}")
                print(f"  To: {recipient}")
                if cc_recipient:
                    print(f"  CC: {cc_recipient}")
                if bcc_recipient:
                    print(f"  BCC: {bcc_recipient}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_3_send_html_email():
    """Example 3: Send an HTML-formatted email."""
    print("\n=== Example 3: Send HTML Email ===")

    sender = os.environ.get("TEST_SMTP_FROM", "")
    recipient = os.environ.get("TEST_SMTP_TO", "")

    if not sender or not recipient:
        print("Set environment variables to send an email:")
        print("  $env:TEST_SMTP_FROM = 'sender@yourdomain.com'")
        print("  $env:TEST_SMTP_TO = 'recipient@example.com'")
        return

    with DefaultAzureCredential() as credential:

        with SmtpClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                html_body = """
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .header { color: #0078d4; }
                        .content { margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <h1 class="header">Azure Connectors SDK</h1>
                    <div class="content">
                        <p>This is an <strong>HTML-formatted</strong> email.</p>
                        <ul>
                            <li>Feature 1: Easy to use</li>
                            <li>Feature 2: Async support</li>
                            <li>Feature 3: Type safety</li>
                        </ul>
                    </div>
                </body>
                </html>
                """

                email = Email(
                    from_=sender,
                    to=recipient,
                    subject="HTML Email from Azure Connectors SDK",
                    body=html_body.strip(),
                )

                client.send_email(input=email)

                print("HTML email sent successfully:")
                print(f"  From: {sender}")
                print(f"  To: {recipient}")
                print(f"  Subject: {email.subject}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_4_send_email_with_attachment():
    """Example 4: Send an email with an attachment."""
    print("\n=== Example 4: Send Email with Attachment ===")

    sender = os.environ.get("TEST_SMTP_FROM", "")
    recipient = os.environ.get("TEST_SMTP_TO", "")

    if not sender or not recipient:
        print("Set environment variables to send an email:")
        print("  $env:TEST_SMTP_FROM = 'sender@yourdomain.com'")
        print("  $env:TEST_SMTP_TO = 'recipient@example.com'")
        return

    with DefaultAzureCredential() as credential:

        with SmtpClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                # Create a sample text file content
                file_content = "This is a sample attachment created by Azure Connectors SDK."
                encoded_content = base64.b64encode(file_content.encode()).decode()

                attachment = Attachment(
                    file_name="sample.txt",
                    content_data=encoded_content,
                    content_type="text/plain",
                )

                email = Email(
                    from_=sender,
                    to=recipient,
                    subject="Email with Attachment",
                    body="Please find the attached file.",
                    attachments=[attachment],
                )

                client.send_email(input=email)

                print("Email with attachment sent successfully:")
                print(f"  From: {sender}")
                print(f"  To: {recipient}")
                print(f"  Attachment: {attachment.file_name}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def example_5_send_email_with_options():
    """Example 5: Send an email with importance and receipts."""
    print("\n=== Example 5: Send Email with Options ===")

    sender = os.environ.get("TEST_SMTP_FROM", "")
    recipient = os.environ.get("TEST_SMTP_TO", "")

    if not sender or not recipient:
        print("Set environment variables to send an email:")
        print("  $env:TEST_SMTP_FROM = 'sender@yourdomain.com'")
        print("  $env:TEST_SMTP_TO = 'recipient@example.com'")
        return

    with DefaultAzureCredential() as credential:

        with SmtpClient(CONNECTION_RUNTIME_URL, credential) as client:
            try:
                email = Email(
                    from_=sender,
                    to=recipient,
                    subject="High Importance Email",
                    body="This is a high-importance email with read receipt requested.",
                    importance="High",
                    read_receipt=sender,
                    delivery_receipt=sender,
                )

                client.send_email(input=email)

                print("Email with options sent successfully:")
                print(f"  From: {sender}")
                print(f"  To: {recipient}")
                print(f"  Importance: {email.importance}")
                print(f"  Read Receipt: {email.read_receipt}")
                print(f"  Delivery Receipt: {email.delivery_receipt}")

            except ConnectorException as ex:
                print(f"Connector error: {ex}")
            except Exception as ex:
                print(f"Error: {ex}")


def main():
    """Run all examples."""
    print("SMTP sample usage for the Azure Connectors Python SDK")
    print("=" * 60)

    if not CONNECTION_RUNTIME_URL:
        print("\nWARNING: SMTP_CONNECTION_URL environment variable not set.")
        print("Set it to your connection runtime URL to run actual API calls.")
        print("Format: https://[region].azure-apihub.net/apim/smtp/[connection-id]")
        return

    example_1_send_basic_email()
    example_2_send_email_with_cc_bcc()
    example_3_send_html_email()
    example_4_send_email_with_attachment()
    example_5_send_email_with_options()

    print("\n" + "=" * 60)
    print("Sample completed!")


if __name__ == "__main__":
    main()
