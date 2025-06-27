# Test environment setup for backend pytest

# Ensure required env vars for all tests
export CONSUMER_KEY=dummy_key

# Run pytest with correct PYTHONPATH
PYTHONPATH=backend pytest backend/tests "$@"
