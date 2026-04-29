"""
Microsoft Graph API Mail Service for PropScope.

This service provides email sending functionality using the Microsoft Graph API
with client credentials authentication. Configuration is read exclusively from
environment variables via Django settings.
"""

import logging
import requests
from typing import Optional
from django.conf import settings


logger = logging.getLogger(__name__)


# Custom Exceptions
class GraphMailConfigurationError(Exception):
    """Raised when Graph API configuration is missing or invalid."""
    pass


class GraphMailAuthenticationError(Exception):
    """Raised when Graph API authentication fails."""
    pass


class GraphMailSendError(Exception):
    """Raised when sending mail via Graph API fails."""
    pass


class GraphMailService:
    """
    Service for sending emails via Microsoft Graph API.

    This service uses the client credentials flow for authentication
    and sends emails on behalf of a configured sender address.

    Configuration is read from Django settings (which load from environment variables):
    - GRAPH_TENANT_ID: Azure AD tenant ID
    - GRAPH_CLIENT_ID: Application (client) ID
    - GRAPH_CLIENT_SECRET: Client secret
    - GRAPH_SENDER_ADDRESS: Email address to send from

    Example usage:
        service = GraphMailService()
        service.send_mail(
            to=['recipient@example.com'],
            subject='Test Email',
            body='This is a test message',
            is_html=False
        )
    """

    # Microsoft Graph API endpoints
    TOKEN_ENDPOINT = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    SEND_MAIL_ENDPOINT = "https://graph.microsoft.com/v1.0/users/{sender_address}/sendMail"
    TOKEN_SCOPE = "https://graph.microsoft.com/.default"

    def __init__(self):
        """Initialize the service and validate configuration."""
        self._validate_configuration()
        self._access_token: Optional[str] = None

    def _validate_configuration(self) -> None:
        """
        Validate that all required configuration values are present.

        Raises:
            GraphMailConfigurationError: If any required configuration is missing
        """
        required_settings = {
            'GRAPH_TENANT_ID': settings.GRAPH_TENANT_ID,
            'GRAPH_CLIENT_ID': settings.GRAPH_CLIENT_ID,
            'GRAPH_CLIENT_SECRET': settings.GRAPH_CLIENT_SECRET,
            'GRAPH_SENDER_ADDRESS': settings.GRAPH_SENDER_ADDRESS,
        }

        missing = [key for key, value in required_settings.items() if not value]

        if missing:
            error_msg = f"Missing required Graph API configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise GraphMailConfigurationError(error_msg)

        logger.debug("Graph API configuration validated successfully")

    def _get_access_token(self) -> str:
        """
        Obtain an access token using client credentials flow.

        Returns:
            str: Access token for Microsoft Graph API

        Raises:
            GraphMailAuthenticationError: If token request fails
        """
        token_url = self.TOKEN_ENDPOINT.format(tenant_id=settings.GRAPH_TENANT_ID)

        payload = {
            'client_id': settings.GRAPH_CLIENT_ID,
            'client_secret': settings.GRAPH_CLIENT_SECRET,
            'scope': self.TOKEN_SCOPE,
            'grant_type': 'client_credentials'
        }

        try:
            logger.debug("Requesting access token from Microsoft Graph")
            response = requests.post(token_url, data=payload, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get('access_token')

            if not access_token:
                raise GraphMailAuthenticationError("No access token in response")

            logger.info("Successfully obtained access token from Microsoft Graph")
            return access_token

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to obtain access token: {str(e)}"
            logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Graph API error details: {error_details}")
                except:
                    logger.error(f"Graph API response: {e.response.text}")
            raise GraphMailAuthenticationError(error_msg) from e

    def _build_message_payload(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        is_html: bool = False,
    ) -> dict:
        """
        Build the message payload for Microsoft Graph API.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            is_html: Whether body is HTML (default: False for plain text)

        Returns:
            dict: Message payload for Graph API
        """
        # Build recipient lists
        to_recipients = [{"emailAddress": {"address": addr}} for addr in to]

        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": body
                },
                "toRecipients": to_recipients
            },
            "saveToSentItems": True
        }

        # Add CC recipients if provided
        if cc:
            message["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]

        # Add BCC recipients if provided
        if bcc:
            message["message"]["bccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in bcc
            ]

        return message

    def send_mail(
        self,
        to: list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        is_html: bool = False,
    ) -> None:
        """
        Send an email via Microsoft Graph API.

        Args:
            to: List of recipient email addresses (required)
            subject: Email subject (required)
            body: Email body content (required)
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            is_html: Whether body is HTML (default: False for plain text)

        Raises:
            GraphMailConfigurationError: If configuration is invalid
            GraphMailAuthenticationError: If authentication fails
            GraphMailSendError: If sending the email fails
            ValueError: If required parameters are invalid
        """
        # Validate inputs
        if not to:
            raise ValueError("At least one recipient is required")
        if not subject:
            raise ValueError("Subject is required")
        if not body:
            raise ValueError("Body is required")

        # Get access token
        try:
            access_token = self._get_access_token()
        except GraphMailAuthenticationError:
            # Re-raise authentication errors
            raise

        # Build message payload
        payload = self._build_message_payload(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            is_html=is_html
        )

        # Send email
        send_url = self.SEND_MAIL_ENDPOINT.format(
            sender_address=settings.GRAPH_SENDER_ADDRESS
        )

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        try:
            logger.info(f"Sending email to {', '.join(to)} with subject '{subject}'")
            logger.debug(f"Send mail endpoint: {send_url}")

            response = requests.post(
                send_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            logger.info(f"Email sent successfully to {', '.join(to)}")

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)

            # Log detailed error response if available
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    logger.error(f"Graph API error details: {error_details}")
                except:
                    logger.error(f"Graph API response: {e.response.text}")

            raise GraphMailSendError(error_msg) from e
