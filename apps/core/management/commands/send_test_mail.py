"""
Django management command to send a test email via Microsoft Graph API.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.core.services.graph_mail_service import (
    GraphMailService,
    GraphMailConfigurationError,
    GraphMailAuthenticationError,
    GraphMailSendError,
)


class Command(BaseCommand):
    help = 'Send a test email via Microsoft Graph API'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test mail to'
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='PropScope Test Email',
            help='Email subject (default: "PropScope Test Email")'
        )
        parser.add_argument(
            '--html',
            action='store_true',
            help='Send as HTML email'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        subject = options['subject']
        is_html = options['html']

        self.stdout.write(
            self.style.SUCCESS(f'Preparing to send test email to: {recipient}')
        )

        # Prepare body content
        if is_html:
            body = """
            <html>
            <body>
                <h1>PropScope Test Email</h1>
                <p>This is a test email from PropScope sent via Microsoft Graph API.</p>
                <p>If you receive this, the mail service is configured correctly.</p>
                <hr>
                <p><small>PropScope - WSJT-X Statistics / CQ Analyzer</small></p>
            </body>
            </html>
            """
            self.stdout.write('Content type: HTML')
        else:
            body = """PropScope Test Email

This is a test email from PropScope sent via Microsoft Graph API.

If you receive this, the mail service is configured correctly.

---
PropScope - WSJT-X Statistics / CQ Analyzer
"""
            self.stdout.write('Content type: Plain Text')

        # Initialize service and send email
        try:
            service = GraphMailService()
            self.stdout.write('Graph Mail Service initialized successfully')

            service.send_mail(
                to=[recipient],
                subject=subject,
                body=body,
                is_html=is_html
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Test email sent successfully to {recipient}'
                )
            )

        except GraphMailConfigurationError as e:
            raise CommandError(
                f'Configuration Error: {str(e)}\n\n'
                'Please check that all required environment variables are set:\n'
                '  - GRAPH_TENANT_ID\n'
                '  - GRAPH_CLIENT_ID\n'
                '  - GRAPH_CLIENT_SECRET\n'
                '  - GRAPH_SENDER_ADDRESS'
            )

        except GraphMailAuthenticationError as e:
            raise CommandError(
                f'Authentication Error: {str(e)}\n\n'
                'Please verify that your Microsoft Graph API credentials are correct.'
            )

        except GraphMailSendError as e:
            raise CommandError(
                f'Send Error: {str(e)}\n\n'
                'The email could not be sent. Please check the error details above.'
            )

        except Exception as e:
            raise CommandError(f'Unexpected error: {str(e)}')
