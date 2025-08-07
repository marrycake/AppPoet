import logging

# logging.getLogger("androguard").setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)
Logger = logging.getLogger('main.stdout')
# Set the logger to debug level for detailed output
Logger.setLevel(logging.DEBUG)
