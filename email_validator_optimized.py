import re
import os
import csv
import dns.resolver
import dns.exception
import logging
import time
import smtplib
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import openpyxl
import xlrd
import argparse
from email.utils import parseaddr
from functools import lru_cache
from ratelimit import limits, sleep_and_retry
from cachetools import cached, TTLCache
from idna import encode as idna_encode
from docx import Document
from tqdm import tqdm
import sys
import signal
import json
from pathlib import Path

# Cache configurations with increased capacity for large datasets
dns_cache = TTLCache(maxsize=50000, ttl=3600)  # 1 hour TTL, increased cache size
smtp_cache = TTLCache(maxsize=50000, ttl=1800)  # 30 minutes TTL, increased cache size

# Rate limiting configurations
MAX_CALLS_PER_SECOND = 10  # Increased for better throughput
SMTP_CALLS_PER_MINUTE = 60  # Increased for better throughput

# Constants
MAX_WORKERS = 50  # Increased concurrent validation threads
DNS_TIMEOUT = 5   # Seconds for DNS timeout
SMTP_TIMEOUT = 10  # Seconds for SMTP timeout
BATCH_SIZE = 1000  # Process emails in batches
CHECKPOINT_INTERVAL = 5000  # Save progress every 5000 emails

# File paths
LOG_FILE = "email_validation.log"
VALID_EMAIL_FILE = "valid_emails.txt"
CHECKPOINT_FILE = "validation_checkpoint.json"
PROGRESS_FILE = "validation_progress.json"

# More comprehensive regex for email validation
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Common constants (disposable domains and role-based prefixes)
DISPOSABLE_DOMAINS = [
    'mailinator.com', 'yopmail.com', 'tempmail.com', 'temp-mail.org', 
    'guerrillamail.com', '10minutemail.com', 'trashmail.com', 'sharklasers.com',
    'throwawaymail.com', 'getairmail.com', 'mailnesia.com', 'tempinbox.com',
    'dispostable.com', 'mailcatch.com', 'anonbox.net', 'getnada.com'
]

ROLE_BASED_PREFIXES = [
    'admin', 'info', 'support', 'sales', 'contact', 'help', 'webmaster',
    'postmaster', 'hostmaster', 'abuse', 'noreply', 'no-reply', 'mail',
    'office', 'marketing', 'team', 'billing', 'jobs', 'career', 'hr'
]

# Configure logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)

class ValidationProgress:
    def __init__(self):
        self.total_processed = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.start_time = time.time()
        self.checkpoint = {}
    
    def save_progress(self):
        progress = {
            'total_processed': self.total_processed,
            'valid_count': self.valid_count,
            'invalid_count': self.invalid_count,
            'elapsed_time': time.time() - self.start_time
        }
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f)
    
    def save_checkpoint(self, last_processed_index):
        self.checkpoint['last_processed_index'] = last_processed_index
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(self.checkpoint, f)
    
    def load_checkpoint(self):
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                self.checkpoint = json.load(f)
            return self.checkpoint.get('last_processed_index', 0)
        return 0

def signal_handler(signum, frame):
    logging.info("Received interrupt signal. Saving progress...")
    progress.save_progress()
    sys.exit(0)

def is_syntactically_valid(email):
    """Checks if the email has a valid basic format."""
    _, addr = parseaddr(email)
    if not addr or addr != email:
        return False
    
    if not re.match(EMAIL_REGEX, email):
        return False
    
    if '..' in email:
        return False
    
    try:
        username, domain = email.split('@')
        if not username or not domain:
            return False
        if domain.startswith('.') or domain.endswith('.'):
            return False
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
            return False
    except ValueError:
        return False
    
    return True

@cached(cache=dns_cache)
def check_mx_record(domain):
    """Checks if the domain has a valid MX record with caching."""
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout,
            dns.exception.DNSException) as e:
        logging.debug(f"MX check failed for {domain}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during MX check for {domain}: {e}")
        return False

def is_disposable_email(domain):
    """Check if the email domain is a known disposable email service."""
    return domain.lower() in DISPOSABLE_DOMAINS

def is_role_based_email(username):
    """Check if the email is a role-based address."""
    return username.lower() in ROLE_BASED_PREFIXES

@sleep_and_retry
@limits(calls=SMTP_CALLS_PER_MINUTE, period=60)
@cached(cache=smtp_cache)
def verify_smtp_connection(email, domain):
    """Attempt to verify email by connecting to the SMTP server with rate limiting and caching."""
    try:
        mx_records = sorted([(pref, str(exch)) for pref, exch in dns.resolver.resolve(domain, 'MX')])
        if not mx_records:
            return False
        
        for _, mail_server in mx_records:
            try:
                smtp = smtplib.SMTP(timeout=SMTP_TIMEOUT)
                smtp.connect(mail_server)
                smtp.helo(socket.getfqdn())
                
                smtp.mail('')
                code, _ = smtp.rcpt(email)
                
                smtp.quit()
                
                if code == 250:
                    return True
                if code in [421, 450, 451, 452]:
                    return True
            except Exception:
                continue
        
        return False
    except Exception as e:
        logging.debug(f"SMTP verification failed for {email}: {e}")
        return True

def validate_email(email):
    """Performs comprehensive email validation with IDN support."""
    if not isinstance(email, str) or not email.strip():
        return None

    email = email.strip()
    
    try:
        if '@' in email:
            local_part, domain = email.split('@')
            if any(ord(c) > 127 for c in domain):
                domain = idna_encode(domain).decode('ascii')
                email = f"{local_part}@{domain}"
    except Exception as e:
        logging.debug(f"IDN conversion failed for {email}: {e}")
        return None

    if not is_syntactically_valid(email):
        return None

    try:
        username, domain = email.split('@')
    except ValueError:
        return None

    if is_disposable_email(domain) or is_role_based_email(username):
        return None

    if not check_mx_record(domain):
        return None

    if verify_smtp_connection(email, domain):
        return email

    return None

def process_batch(emails):
    """Process a batch of emails with parallel validation."""
    valid_emails = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_email = {executor.submit(validate_email, email): email for email in emails}
        for future in as_completed(future_to_email):
            try:
                result = future.result()
                if result:
                    valid_emails.append(result)
            except Exception as e:
                logging.error(f"Error processing email {future_to_email[future]}: {e}")
    return valid_emails

def read_emails_in_batches(file_path):
    """Generator to read emails in batches from various file formats."""
    ext = Path(file_path).suffix.lower()
    batch = []
    
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                batch.append(line.strip())
                if len(batch) >= BATCH_SIZE:
                    yield batch
                    batch = []
    elif ext == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():  # Assuming email is in first column
                    batch.append(row[0].strip())
                    if len(batch) >= BATCH_SIZE:
                        yield batch
                        batch = []
    elif ext in ['.xlsx', '.xls']:
        if ext == '.xlsx':
            wb = openpyxl.load_workbook(file_path, read_only=True)
        else:
            wb = xlrd.open_workbook(file_path)
        sheet = wb.active if ext == '.xlsx' else wb.sheet_by_index(0)
        
        for row in sheet.rows if ext == '.xlsx' else range(sheet.nrows):
            email = row[0].value if ext == '.xlsx' else sheet.cell_value(row, 0)
            if email and isinstance(email, str):
                batch.append(email.strip())
                if len(batch) >= BATCH_SIZE:
                    yield batch
                    batch = []
    elif ext == '.docx':
        doc = Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                batch.append(para.text.strip())
                if len(batch) >= BATCH_SIZE:
                    yield batch
                    batch = []
    
    if batch:  # Yield remaining emails
        yield batch

def main():
    parser = argparse.ArgumentParser(description='Validate email addresses from various file formats')
    parser.add_argument('input_file', help='Path to the input file containing email addresses')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        logging.error(f"Input file not found: {args.input_file}")
        return

    global progress
    progress = ValidationProgress()
    start_index = progress.load_checkpoint() if args.resume else 0

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    valid_emails = set()
    if os.path.exists(VALID_EMAIL_FILE) and args.resume:
        with open(VALID_EMAIL_FILE, 'r') as f:
            valid_emails.update(f.read().splitlines())

    try:
        total_emails = sum(1 for _ in read_emails_in_batches(args.input_file))
        with tqdm(total=total_emails, initial=start_index) as pbar:
            for i, batch in enumerate(read_emails_in_batches(args.input_file)):
                if i * BATCH_SIZE < start_index:
                    continue

                batch_valid_emails = process_batch(batch)
                valid_emails.update(batch_valid_emails)

                progress.total_processed += len(batch)
                progress.valid_count = len(valid_emails)
                progress.invalid_count = progress.total_processed - progress.valid_count

                if progress.total_processed % CHECKPOINT_INTERVAL == 0:
                    progress.save_checkpoint(progress.total_processed)
                    progress.save_progress()
                    with open(VALID_EMAIL_FILE, 'w') as f:
                        f.write('\n'.join(sorted(valid_emails)))

                pbar.update(len(batch))
                pbar.set_postfix({'valid': progress.valid_count, 
                                'invalid': progress.invalid_count})

    except Exception as e:
        logging.error(f"Error processing file: {e}")
        progress.save_checkpoint(progress.total_processed)
        progress.save_progress()
    finally:
        with open(VALID_EMAIL_FILE, 'w') as f:
            f.write('\n'.join(sorted(valid_emails)))
        
        logging.info(f"Validation complete. Results:")
        logging.info(f"Total processed: {progress.total_processed}")
        logging.info(f"Valid emails: {progress.valid_count}")
        logging.info(f"Invalid emails: {progress.invalid_count}")
        logging.info(f"Results saved to: {VALID_EMAIL_FILE}")

if __name__ == '__main__':
    main()