# Core Service: Microsoft Graph API Mail Service

## Overview

This core service provides email sending functionality for PropScope using the Microsoft Graph API. The service is designed to be reusable across the application and completely independent from UI, worker, and specific notification rules.

## Features

- ✅ **Client Credentials Authentication**: Uses OAuth 2.0 client credentials flow
- ✅ **Text and HTML Emails**: Supports both plain text and HTML email formats
- ✅ **Multiple Recipients**: Supports To, CC, and BCC recipients
- ✅ **Environment-based Configuration**: All credentials read from environment variables
- ✅ **Comprehensive Error Handling**: Custom exceptions for different failure scenarios
- ✅ **Detailed Logging**: Logs authentication and send operations
- ✅ **Fully Tested**: 20+ test cases covering all functionality
- ✅ **Management Command**: Includes `send_test_mail` command for testing

## Configuration

### Environment Variables

Add the following variables to your `.env` file:

```env
# Microsoft Graph API Configuration
# These credentials should NEVER be stored in the database
GRAPH_TENANT_ID=your-tenant-id
GRAPH_CLIENT_ID=your-client-id
GRAPH_CLIENT_SECRET=your-client-secret
GRAPH_SENDER_ADDRESS=sender@yourdomain.com
```

These values are automatically loaded into Django settings and used by the service.

### Azure AD Application Setup

1. Register an application in Azure AD
2. Grant the application the `Mail.Send` permission (Application permission, not Delegated)
3. Admin consent required for the permission
4. Create a client secret
5. Note the Tenant ID, Client ID, and Client Secret

## Usage

### Basic Usage

```python
from apps.core.services.graph_mail_service import GraphMailService

# Initialize the service
service = GraphMailService()

# Send a simple text email
service.send_mail(
    to=['recipient@example.com'],
    subject='PropScope Notification',
    body='This is a notification from PropScope'
)
```

### HTML Email

```python
service.send_mail(
    to=['recipient@example.com'],
    subject='PropScope Report',
    body='<h1>Daily Report</h1><p>Your statistics are ready.</p>',
    is_html=True
)
```

### Multiple Recipients with CC and BCC

```python
service.send_mail(
    to=['user1@example.com', 'user2@example.com'],
    cc=['manager@example.com'],
    bcc=['archive@example.com'],
    subject='PropScope Alert',
    body='Important alert message'
)
```

## Exception Handling

The service provides three custom exceptions for different error scenarios:

### GraphMailConfigurationError

Raised when required configuration is missing or invalid.

```python
from apps.core.services.graph_mail_service import GraphMailConfigurationError

try:
    service = GraphMailService()
except GraphMailConfigurationError as e:
    print(f"Configuration error: {e}")
```

### GraphMailAuthenticationError

Raised when authentication with Microsoft Graph fails.

```python
from apps.core.services.graph_mail_service import GraphMailAuthenticationError

try:
    service.send_mail(...)
except GraphMailAuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### GraphMailSendError

Raised when sending the email fails.

```python
from apps.core.services.graph_mail_service import GraphMailSendError

try:
    service.send_mail(...)
except GraphMailSendError as e:
    print(f"Failed to send email: {e}")
```

## Testing the Service

### Using the Management Command

Send a test email to verify configuration:

```bash
# Send plain text test email
python manage.py send_test_mail recipient@example.com

# Send HTML test email
python manage.py send_test_mail recipient@example.com --html

# Custom subject
python manage.py send_test_mail recipient@example.com --subject "Custom Test"
```

### Running Unit Tests

```bash
# Run all core app tests
python manage.py test apps.core

# Run with verbose output
python manage.py test apps.core -v 2
```

## Architecture

### Service Structure

```
apps/core/
├── __init__.py
├── apps.py
├── services/
│   ├── __init__.py
│   └── graph_mail_service.py    # Main service implementation
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── send_test_mail.py    # Test command
└── tests.py                      # Comprehensive test suite
```

### Authentication Flow

1. Service reads configuration from Django settings (loaded from environment variables)
2. On first send, service requests an access token using client credentials
3. Access token is used to authenticate the send mail request
4. Token is obtained fresh for each send operation (future enhancement: token caching)

### API Endpoints Used

- **Token Endpoint**: `https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token`
- **Send Mail Endpoint**: `https://graph.microsoft.com/v1.0/users/{sender_address}/sendMail`

## Logging

The service logs the following events:

- Configuration validation (debug level)
- Access token requests (debug level)
- Successful token acquisition (info level)
- Email send attempts (info level)
- Successful email sends (info level)
- All errors (error level with details)

Example log output:

```
INFO: Successfully obtained access token from Microsoft Graph
INFO: Sending email to recipient@example.com with subject 'Test Email'
INFO: Email sent successfully to recipient@example.com
```

## Future Enhancements

The following features are NOT part of this initial implementation but could be added:

- Token caching to reduce authentication requests
- Email templates
- Attachment support
- Batch sending
- Retry logic with exponential backoff
- Notification rules and automation
- UI for viewing sent emails
- Database logging of sent emails (without storing credentials)

## Security Notes

- ✅ All credentials are read from environment variables
- ✅ No credentials are stored in the database
- ✅ No credentials are logged
- ✅ Access tokens are not cached (obtained per request)
- ✅ HTTPS used for all API communication

## Integration Examples

### Import Error Notification

```python
from apps.core.services.graph_mail_service import GraphMailService

def notify_import_error(file_path, error_message, admin_email):
    service = GraphMailService()
    service.send_mail(
        to=[admin_email],
        subject=f'PropScope Import Error: {file_path}',
        body=f'Import failed for {file_path}\n\nError: {error_message}'
    )
```

### Daily Summary Report

```python
def send_daily_summary(recipients, stats):
    service = GraphMailService()

    html_body = f'''
    <html>
    <body>
        <h1>PropScope Daily Summary</h1>
        <p>Signals received: {stats['total_signals']}</p>
        <p>Unique callsigns: {stats['unique_callsigns']}</p>
        <p>Average distance: {stats['avg_distance']} km</p>
    </body>
    </html>
    '''

    service.send_mail(
        to=recipients,
        subject='PropScope Daily Summary',
        body=html_body,
        is_html=True
    )
```

## Testing

The service includes 20+ test cases covering:

- Configuration validation
- Missing configuration detection
- Token acquisition success and failure
- Message payload building (text, HTML, with CC/BCC)
- Email sending success and failure
- Input validation
- All exception types

Run tests with:

```bash
python manage.py test apps.core
```

## Support

For issues or questions about this service, please refer to:

- Django settings in `propscope/settings.py`
- Service implementation in `apps/core/services/graph_mail_service.py`
- Test examples in `apps/core/tests.py`
