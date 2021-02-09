from google.cloud import storage

### Utility Functions
def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             List AWS EC2 Instances                     *"
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
    list_buckets()