"""
Tests for Microsoft Graph Mail Service.
"""

from django.test import TestCase, override_settings
from unittest.mock import Mock, patch, MagicMock
from apps.core.services.graph_mail_service import (
    GraphMailService,
    GraphMailConfigurationError,
    GraphMailAuthenticationError,
    GraphMailSendError,
)


@override_settings(
    GRAPH_TENANT_ID='test-tenant-id',
    GRAPH_CLIENT_ID='test-client-id',
    GRAPH_CLIENT_SECRET='test-client-secret',
    GRAPH_SENDER_ADDRESS='sender@example.com',
)
class GraphMailServiceTests(TestCase):
    """Tests for GraphMailService."""

    def test_initialization_with_valid_config(self):
        """Test that service initializes successfully with valid configuration."""
        service = GraphMailService()
        self.assertIsNotNone(service)

    @override_settings(GRAPH_TENANT_ID='')
    def test_initialization_missing_tenant_id(self):
        """Test that missing tenant ID raises configuration error."""
        with self.assertRaises(GraphMailConfigurationError) as cm:
            GraphMailService()
        self.assertIn('GRAPH_TENANT_ID', str(cm.exception))

    @override_settings(GRAPH_CLIENT_ID='')
    def test_initialization_missing_client_id(self):
        """Test that missing client ID raises configuration error."""
        with self.assertRaises(GraphMailConfigurationError) as cm:
            GraphMailService()
        self.assertIn('GRAPH_CLIENT_ID', str(cm.exception))

    @override_settings(GRAPH_CLIENT_SECRET='')
    def test_initialization_missing_client_secret(self):
        """Test that missing client secret raises configuration error."""
        with self.assertRaises(GraphMailConfigurationError) as cm:
            GraphMailService()
        self.assertIn('GRAPH_CLIENT_SECRET', str(cm.exception))

    @override_settings(GRAPH_SENDER_ADDRESS='')
    def test_initialization_missing_sender_address(self):
        """Test that missing sender address raises configuration error."""
        with self.assertRaises(GraphMailConfigurationError) as cm:
            GraphMailService()
        self.assertIn('GRAPH_SENDER_ADDRESS', str(cm.exception))

    @override_settings(
        GRAPH_TENANT_ID='',
        GRAPH_CLIENT_ID='',
    )
    def test_initialization_multiple_missing_configs(self):
        """Test that multiple missing configs are reported."""
        with self.assertRaises(GraphMailConfigurationError) as cm:
            GraphMailService()
        error_message = str(cm.exception)
        self.assertIn('GRAPH_TENANT_ID', error_message)
        self.assertIn('GRAPH_CLIENT_ID', error_message)

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful token acquisition."""
        # Mock successful token response
        mock_response = Mock()
        mock_response.json.return_value = {'access_token': 'test-token-123'}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = GraphMailService()
        token = service._get_access_token()

        self.assertEqual(token, 'test-token-123')
        mock_post.assert_called_once()

        # Verify the correct token endpoint was called
        call_args = mock_post.call_args
        self.assertIn('test-tenant-id', call_args[0][0])

        # Verify payload contains correct data
        payload = call_args[1]['data']
        self.assertEqual(payload['client_id'], 'test-client-id')
        self.assertEqual(payload['client_secret'], 'test-client-secret')
        self.assertEqual(payload['scope'], 'https://graph.microsoft.com/.default')
        self.assertEqual(payload['grant_type'], 'client_credentials')

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_get_access_token_missing_in_response(self, mock_post):
        """Test authentication error when token is missing from response."""
        # Mock response without access token
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        service = GraphMailService()

        with self.assertRaises(GraphMailAuthenticationError) as cm:
            service._get_access_token()
        self.assertIn('No access token', str(cm.exception))

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_get_access_token_request_exception(self, mock_post):
        """Test authentication error when request fails."""
        # Mock request exception
        mock_post.side_effect = Exception("Network error")

        service = GraphMailService()

        with self.assertRaises(GraphMailAuthenticationError) as cm:
            service._get_access_token()
        self.assertIn('Failed to obtain access token', str(cm.exception))

    def test_build_message_payload_basic(self):
        """Test building a basic message payload."""
        service = GraphMailService()

        payload = service._build_message_payload(
            to=['recipient@example.com'],
            subject='Test Subject',
            body='Test Body',
            is_html=False
        )

        self.assertEqual(payload['message']['subject'], 'Test Subject')
        self.assertEqual(payload['message']['body']['content'], 'Test Body')
        self.assertEqual(payload['message']['body']['contentType'], 'Text')
        self.assertEqual(len(payload['message']['toRecipients']), 1)
        self.assertEqual(
            payload['message']['toRecipients'][0]['emailAddress']['address'],
            'recipient@example.com'
        )
        self.assertTrue(payload['saveToSentItems'])

    def test_build_message_payload_html(self):
        """Test building an HTML message payload."""
        service = GraphMailService()

        payload = service._build_message_payload(
            to=['recipient@example.com'],
            subject='Test Subject',
            body='<h1>Test Body</h1>',
            is_html=True
        )

        self.assertEqual(payload['message']['body']['contentType'], 'HTML')

    def test_build_message_payload_with_cc_bcc(self):
        """Test building a message payload with CC and BCC."""
        service = GraphMailService()

        payload = service._build_message_payload(
            to=['to@example.com'],
            subject='Test Subject',
            body='Test Body',
            cc=['cc@example.com'],
            bcc=['bcc@example.com'],
            is_html=False
        )

        self.assertEqual(len(payload['message']['ccRecipients']), 1)
        self.assertEqual(
            payload['message']['ccRecipients'][0]['emailAddress']['address'],
            'cc@example.com'
        )
        self.assertEqual(len(payload['message']['bccRecipients']), 1)
        self.assertEqual(
            payload['message']['bccRecipients'][0]['emailAddress']['address'],
            'bcc@example.com'
        )

    def test_build_message_payload_multiple_recipients(self):
        """Test building a message payload with multiple recipients."""
        service = GraphMailService()

        payload = service._build_message_payload(
            to=['to1@example.com', 'to2@example.com'],
            subject='Test Subject',
            body='Test Body',
            cc=['cc1@example.com', 'cc2@example.com'],
        )

        self.assertEqual(len(payload['message']['toRecipients']), 2)
        self.assertEqual(len(payload['message']['ccRecipients']), 2)

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_send_mail_success(self, mock_post):
        """Test successful email sending."""
        # Mock successful token response
        token_response = Mock()
        token_response.json.return_value = {'access_token': 'test-token'}
        token_response.raise_for_status = Mock()

        # Mock successful send response
        send_response = Mock()
        send_response.raise_for_status = Mock()

        mock_post.side_effect = [token_response, send_response]

        service = GraphMailService()
        service.send_mail(
            to=['recipient@example.com'],
            subject='Test Email',
            body='Test Body'
        )

        # Verify two POST requests were made (token + send)
        self.assertEqual(mock_post.call_count, 2)

        # Verify send mail call
        send_call = mock_post.call_args_list[1]
        self.assertIn('sender@example.com', send_call[0][0])
        self.assertIn('Bearer test-token', send_call[1]['headers']['Authorization'])

    def test_send_mail_missing_to(self):
        """Test that missing 'to' raises ValueError."""
        service = GraphMailService()

        with self.assertRaises(ValueError) as cm:
            service.send_mail(
                to=[],
                subject='Test',
                body='Test'
            )
        self.assertIn('recipient', str(cm.exception))

    def test_send_mail_missing_subject(self):
        """Test that missing subject raises ValueError."""
        service = GraphMailService()

        with self.assertRaises(ValueError) as cm:
            service.send_mail(
                to=['test@example.com'],
                subject='',
                body='Test'
            )
        self.assertIn('Subject', str(cm.exception))

    def test_send_mail_missing_body(self):
        """Test that missing body raises ValueError."""
        service = GraphMailService()

        with self.assertRaises(ValueError) as cm:
            service.send_mail(
                to=['test@example.com'],
                subject='Test',
                body=''
            )
        self.assertIn('Body', str(cm.exception))

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_send_mail_authentication_failure(self, mock_post):
        """Test email sending with authentication failure."""
        # Mock failed token request
        mock_post.side_effect = Exception("Auth failed")

        service = GraphMailService()

        with self.assertRaises(GraphMailAuthenticationError):
            service.send_mail(
                to=['recipient@example.com'],
                subject='Test',
                body='Test'
            )

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_send_mail_send_failure(self, mock_post):
        """Test email sending when send request fails."""
        # Mock successful token response
        token_response = Mock()
        token_response.json.return_value = {'access_token': 'test-token'}
        token_response.raise_for_status = Mock()

        # Mock failed send request
        send_response = Mock()
        send_response.raise_for_status.side_effect = Exception("Send failed")

        mock_post.side_effect = [token_response, send_response]

        service = GraphMailService()

        with self.assertRaises(GraphMailSendError) as cm:
            service.send_mail(
                to=['recipient@example.com'],
                subject='Test',
                body='Test'
            )
        self.assertIn('Failed to send email', str(cm.exception))

    @patch('apps.core.services.graph_mail_service.requests.post')
    def test_send_mail_with_all_options(self, mock_post):
        """Test sending email with all available options."""
        # Mock successful token response
        token_response = Mock()
        token_response.json.return_value = {'access_token': 'test-token'}
        token_response.raise_for_status = Mock()

        # Mock successful send response
        send_response = Mock()
        send_response.raise_for_status = Mock()

        mock_post.side_effect = [token_response, send_response]

        service = GraphMailService()
        service.send_mail(
            to=['to@example.com'],
            subject='Test Email',
            body='<p>Test HTML Body</p>',
            cc=['cc@example.com'],
            bcc=['bcc@example.com'],
            is_html=True
        )

        # Verify send mail was called with correct payload
        send_call = mock_post.call_args_list[1]
        payload = send_call[1]['json']

        self.assertEqual(payload['message']['body']['contentType'], 'HTML')
        self.assertIn('ccRecipients', payload['message'])
        self.assertIn('bccRecipients', payload['message'])
