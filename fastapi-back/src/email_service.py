import os
import resend
from dotenv import load_dotenv
from models import RecurringCharges

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "onboarding@resend.dev")

def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    resend.Emails.send({
        "from": EMAIL_FROM_ADDRESS,
        "to": to_email,
        "subject": subject,
        "text": text_body,
        "html": html_body,
    })

def build_new_charge_email(charge: RecurringCharges) -> tuple[str, str, str]:
    subject = f"New recurring charge detected: {charge.merchant_name}"

    text_body = (
        "We noticed a new recurring charge.\n\n"
        f"Merchant: {charge.merchant_name}\n"
        f"Amount: ${charge.amount:.2f}\n"
        f"Frequency: every ~{charge.interval_days} days\n"
        f"Next expected: {charge.next_expected_date}\n"
    )

    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color:#111;">New recurring charge detected</h2>
      <p style="color:#444;">We noticed a new recurring charge on your account.</p>
      <table style="width:100%; border-collapse: collapse; margin-top: 16px;">
        <tr><td style="padding:8px 0; color:#888;">Merchant</td><td style="padding:8px 0; font-weight:bold;">{charge.merchant_name}</td></tr>
        <tr><td style="padding:8px 0; color:#888;">Amount</td><td style="padding:8px 0; font-weight:bold;">${charge.amount:.2f}</td></tr>
        <tr><td style="padding:8px 0; color:#888;">Frequency</td><td style="padding:8px 0;">Every ~{charge.interval_days} days</td></tr>
        <tr><td style="padding:8px 0; color:#888;">Next expected</td><td style="padding:8px 0;">{charge.next_expected_date}</td></tr>
      </table>
    </div>
    """

    return subject, text_body, html_body

def build_price_change_email(charge: RecurringCharges) -> tuple[str, str, str]:
    subject = f"Price change detected: {charge.merchant_name}"

    text_body = (
        "The amount for a recurring charge changed.\n\n"
        f"Merchant: {charge.merchant_name}\n"
        f"Previous amount: ${charge.previous_amount:.2f}\n"
        f"New amount: ${charge.amount:.2f}\n"
        f"Next expected: {charge.next_expected_date}\n"
    )

    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color:#111;">Price change detected</h2>
      <p style="color:#444;">The amount for one of your recurring charges changed.</p>
      <table style="width:100%; border-collapse: collapse; margin-top: 16px;">
        <tr><td style="padding:8px 0; color:#888;">Merchant</td><td style="padding:8px 0; font-weight:bold;">{charge.merchant_name}</td></tr>
        <tr><td style="padding:8px 0; color:#888;">Previous amount</td><td style="padding:8px 0; text-decoration: line-through;">${charge.previous_amount:.2f}</td></tr>
        <tr><td style="padding:8px 0; color:#888;">New amount</td><td style="padding:8px 0; font-weight:bold; color:#b00020;">${charge.amount:.2f}</td></tr>
        <tr><td style="padding:8px 0; color:#888;">Next expected</td><td style="padding:8px 0;">{charge.next_expected_date}</td></tr>
      </table>
    </div>
    """

    return subject, text_body, html_body
