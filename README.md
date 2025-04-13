# Email Validator

This repository contains two versions of the email validator:

1. **Standard Version** (`email_validator.py`)
   - Suitable for small to medium datasets
   - Lower resource consumption
   - Ideal for regular usage

2. **Optimized Version** (`email_validator_optimized.py`)
   - Designed for large datasets
   - Enhanced performance with larger cache sizes
   - Higher throughput with increased concurrent processing
   - Progress tracking and checkpoint features
   - Recommended when processing large email lists or if the standard version causes system lag

## Requirements

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

Core dependencies:
```bash
python3
dns.resolver
openpyxl
xlrd
python-docx
idna
ratelimit
cachetools
tqdm (for progress tracking)
```

## Installation

### Prerequisites

#### Windows
1. Install Python 3.x from [python.org](https://www.python.org/downloads/windows/)
   - During installation, check "Add Python to PATH"
   - Verify installation: `python --version` in Command Prompt

2. Install Git from [git-scm.com](https://git-scm.com/download/windows)
   - Use default installation options
   - Verify installation: `git --version`

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv git
```

### Setup Instructions

1. Clone the repository:
```bash
# Windows (Command Prompt)
git clone https://github.com/instax-dutta/EmailValidator.git
cd EmailValidator

# Linux
git clone https://github.com/instax-dutta/EmailValidator.git
cd EmailValidator
```

2. Create and activate a virtual environment:

```bash
# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate

# Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
# Windows/Linux
pip install -r requirements.txt

# If requirements.txt is missing, install packages directly:
pip install dnspython openpyxl xlrd python-docx idna ratelimit cachetools
```

## Usage

### Running the Validator

```bash
# Windows
python email_validator.py input_file

# Linux
python3 email_validator.py input_file
```

Replace `input_file` with the path to your file containing email addresses.

### Example Commands

```bash
# Windows
python email_validator.py emails.txt
python email_validator.py "C:\Users\YourName\Documents\emails.csv"

# Linux
python3 email_validator.py emails.txt
python3 email_validator.py /home/username/documents/emails.csv
```

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
   - Windows: Use forward slashes (/) or escaped backslashes (\\) in file paths
   - Linux: Check file ownership with `ls -l`

2. **DNS Timeout**
   - Check internet connectivity
   - Increase `DNS_TIMEOUT` value
   - Windows: Try `ipconfig /flushdns`
   - Linux: Try `sudo systemd-resolve --flush-caches`

3. **Memory Issues**
   - Reduce `MAX_WORKERS` for large files
   - Process files in smaller batches
   - Windows: Close unnecessary applications
   - Linux: Check available memory with `free -h`

4. **Slow Processing**
   - Adjust `MAX_WORKERS` based on your system
   - Consider disabling SMTP verification
   - Windows: Check Task Manager for CPU/Memory usage
   - Linux: Use `top` or `htop` to monitor system resources

5. **Python/Package Issues**
   Windows:
   - Ensure Python is in PATH
   - Try running as administrator
   - Check pip installation: `python -m pip --version`
   
   Linux:
   - Check Python version: `python3 --version`
   - Verify pip installation: `pip3 --version`
   - Try: `sudo apt install python3-dev` (Ubuntu/Debian)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool performs email validation based on standard rules and DNS checks. However, the only way to be 100% certain an email address is valid is to send an email and get a response.