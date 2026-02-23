from colorama import init, Fore

# Initialize the color ouput with colorama
init()

def welcomebanner():
    # Print the welcome banner
    print(Fore.CYAN)
    message = "*             Create AWS EC2 Instances                     *"
    banner(message, "*")
    print(Fore.RESET)

def endbanner():
    print(Fore.CYAN)
    message = "* Create AWS Instance Operations Are Complete   *"
    banner(message, "*")
    print(Fore.RESET)

def banner(message, border="*"):
    line = border * (len(message) + 4)
    print(line)
    print(f"{border} {message} {border}")
    print(line)