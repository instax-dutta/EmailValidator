# Email Validator

A robust Python script for validating email addresses from various file formats with comprehensive validation rules and detailed logging.

## Features

- Supports multiple input file formats (TXT, CSV, Excel, Word)
- Validates email syntax and domain existence
- Checks for disposable email domains
- Identifies role-based email addresses
- Handles IDN (International Domain Names)
- Concurrent processing for better performance
- Detailed logging and progress tracking

## Requirements

```bash
python3
dns.resolver
openpyxl
xlrd
python-docx
idna
ratelimit
cachetools
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/EmailValidator.git
cd EmailValidator
```

2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install dnspython openpyxl xlrd python-docx idna ratelimit cachetools
```

## Usage

```bash
python email_validator.py input_file
```

Replace `input_file` with the path to your file containing email addresses.

### Supported Input File Formats

- Text files (.txt)
- CSV files (.csv)
- Excel files (.xlsx, .xls)
- Word documents (.doc, .docx)

### Output

The script generates two files:
- `valid_emails.txt`: Contains all valid email addresses
- `email_validation.log`: Detailed log of the validation process

## Configuration

The script includes several configurable parameters in the source code:

- `MAX_WORKERS`: Number of concurrent validation threads (default: 20)
- `DNS_TIMEOUT`: Timeout for DNS queries in seconds (default: 5)
- `SMTP_TIMEOUT`: Timeout for SMTP connections in seconds (default: 10)
- `MAX_CALLS_PER_SECOND`: Rate limit for API calls (default: 5)

## Validation Rules

Emails are checked against:
1. Basic syntax validation
2. Domain existence (MX records)
3. Disposable email domains
4. Role-based email addresses
5. IDN (International Domain Names) support

## Error Handling

The script includes comprehensive error handling:
- Invalid file formats
- Network connectivity issues
- Rate limiting
- Invalid email formats
- File access permissions

## Logging

Detailed logs are written to `email_validation.log`, including:
- Progress updates
- Validation results
- Error messages
- Performance metrics

## Troubleshooting

### Common Issues

1. **File Not Found**
   - Ensure the input file path is correct
   - Check file permissions

2. **DNS Timeout**
   - Check internet connectivity
   - Increase `DNS_TIMEOUT` value

3. **Memory Issues**
   - Reduce `MAX_WORKERS` for large files
   - Process files in smaller batches

4. **Slow Processing**
   - Adjust `MAX_WORKERS` based on your system
   - Consider disabling SMTP verification

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool performs email validation based on standard rules and DNS checks. However, the only way to be 100% certain an email address is valid is to send an email and get a response.