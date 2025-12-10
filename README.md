# Mercury CLI

A command-line interface for managing and automating Broadworks provisioning operations.

---

## Installation

### Prerequisites

- Python 3.12 or higher  
- Access to a Broadworks provisioning server  

---

## Getting Started

Launch the CLI by running:

```bash
mercury-cli
```

On first launch, you will be prompted to authenticate with your Mercury server credentials:

- Username  
- Password  
- Server URL (e.g., https://mercury.example.com/webservice/services/ProvisioningService)  
- TLS option (defaults to yes)  

---

### Skip Authentication (Development)

For testing purposes, you can skip the login prompt via the --no-login flag:

```bash
mercury-cli --no-login
```

---

## Available Commands

### General Commands

| Command | Description |
|----------|-------------|
| `help [command]` | Display available commands or get help for a specific command |
| `sysver` | Display the current system software version |
| `clear` | Clear the terminal screen |
| `exit` | Exit the CLI |

---

### Bulk Operations

The CLI supports bulk creation and modification operations using CSV files.

#### Bulk Create

| Command | Description |
|----------|-------------|
| `bulk create hunt_group <file_path>` | Create hunt groups from CSV |
| `bulk create call_pickup <file_path>` | Create call pickup groups from CSV |
| `bulk create call_center <file_path>` | Create call centers from CSV |
| `bulk create auto_attendant <file_path>` | Create auto attendants from CSV |

#### Bulk Modify

| Command | Description |
|----------|-------------|
| `bulk modify call_center agent_list <file_path>` | Modify call center agent lists from CSV |

---

## Plugin Commands

Mercury CLI supports a plugin system for extending functionality.

| Command | Description |
|----------|-------------|
| `plugin list` | List all available plugins |

Loaded plugins automatically register their own commands and subcommands.

---

## Features

- Tab completion for commands and file paths  
- Command history with auto-suggest  
- Input validation  
- Progress indicators for long-running operations  
- Detailed error reporting for bulk operations  

---