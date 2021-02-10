from google.cloud import storage
from colorama import init, Fore

# Initialize the color ouput with colorama
init()

### Utility Functions
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             List GCP Buckets                    *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "*  List GCP Buckets Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border='-'):
    line = border * len(message)
    print(line)
    print(message)
    print(line)

# List buckets function
def list_buckets():
    """Lists all buckets."""

    storage_client = storage.Client()
    buckets = storage_client.list_buckets()

    for bucket in buckets:
        print(bucket.name)

# Main function
if __name__ == "__main__":
    welcomebanner()
    list_buckets()
    endbanner()