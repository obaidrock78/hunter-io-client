# Hunter.io Python Client

A lightweight Python client for interacting with the Hunter.io API v2.

This client allows you to:

- Search for emails associated with a domain or company (`domain_search`)
- Find the most likely email address for a person (`find_email`)
- Verify the deliverability of an email address (`verify_email`)

---






## Installation

pip install -e .[dev]

# After Deployment

pip install hunter-io-client



## Code Usage


from hunter_client import HunterClient

client = HunterClient("YOUR_API_KEY")

# Domain search
result = client.domain_search(domain="example.com")
print(result)

# Find email
email = client.find_email(domain="example.com", first_name="John", last_name="Doe")
print(email)

# Verify email
verification = client.verify_email("test@example.com")
print(verification)
Project Status
All tests, type checks, and linting pass successfully:

Pytest results

$ pytest tests/
================================================================================================== test session starts ===================================================================================================
collected 12 items

tests/test_hunter_client.py ............                                                                                                                  [100%]

=================================================================================================== 12 passed in 0.05s ===================================================================================================
Mypy type checking



$ mypy hunter_client/
Success: no issues found in 2 source files
Flake8 linting

$ flake8 hunter_client/
# No warnings/errors
This means the project is:

Fully type-checked with mypy

Linter-clean (flake8 with wemake-python-styleguide)

Tested with full coverage of all main functions
