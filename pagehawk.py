import argparse
import ipaddress
import sys
import os
import json
import base64
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Set Playwright browsers path for bundled executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(sys._MEIPASS, 'playwright_browsers')

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Thread safety lock for JSON file writing
json_write_lock = threading.Lock()

# Delay Configuration (in milliseconds)
DELAY_FROM = 20
DELAY_TO = 800

# Proxy Configuration
USE_PROXY = False
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8080
PROXY_USERNAME = ""  # Leave empty if no authentication required
PROXY_PASSWORD = ""  # Leave empty if no authentication required

# Ports
DEFAULT_PORTS_1 = [
	80,     # HTTP
	443,    # HTTPS
	8000,   # Dev/Test HTTP
	8080,   # Alternate HTTP
	8443    # Alternate HTTPS
]

DEFAULT_PORTS_2 = [
	81,     # Alternate HTTP
	82,     # Alternate HTTP
	591,    # FileMaker HTTP
	631,    # CUPS Web UI
	3000,   # Node.js dev servers
	3001,   # Node.js alternate dev
	3128,   # Proxy
	7000,   # Custom web applications
	7001,   # WebLogic Admin HTTP
	8081,   # Alternate HTTP / dashboards
	8082,   # Secondary web service port
	8085,   # Jenkins / CI web UI
	8090,   # Atlassian services
	8181,   # Lightweight admin panels
	8686,   # JBoss / WildFly management
	8880,   # Alternate admin web UI
	8888,   # Dev/Proxy
	9000,   # SonarQube / Dev HTTP
	9001,   # Supervisor web UI
	9090,   # Prometheus / metrics
	9443,   # Alternate admin HTTPS
	4443    # Alternate HTTPS
]

DEFAULT_PORTS_3 = [
	5000,   # Flask / Python dev server
	5001,   # Flask / API alternate port
	5600,   # Dashboard services
	5601,   # Kibana UI
	5672,   # RabbitMQ AMQP (paired with 15672 UI)
	7180,   # Cloudera Manager
	8008,   # Alternate HTTP / proxy services
	8083,   # Kafka Manager
	8091,   # Atlassian alternate admin
	9091,   # Transmission Web UI
	9200,   # Elasticsearch REST API
	9999,   # Generic admin / debug
	10000,  # Webmin web admin
	10443,  # Alternate admin HTTPS
	15672,  # RabbitMQ management UI
	20000   # Usermin web interface
]

DEFAULT_PORTS_1_2 = DEFAULT_PORTS_1 + DEFAULT_PORTS_2
DEFAULT_PORTS_ALL = DEFAULT_PORTS_1 + DEFAULT_PORTS_2 + DEFAULT_PORTS_3

# Variables used in the script
# Variables used in the script
ips_to_view = []
urls_to_view = []
ports_to_view = []
sockets_to_view = []
visits = {}
html = ""
threads = 10
verbosity_level = 0
subdir_timestamped = False
subdir_screenshots = False
output_path = "."
output_screenshots_pathname = "screenshots"
output_json_filename = "pagehawk_results.json"
output_json_final_filename = "pagehawk_results.json"  # Will be set based on args
output_filename = "pagehawk_results.html"
start_time = None  # Will track when recon starts


def print2(text, color=None, level=0):
    """
    Print text with specified color and verbosity level.
    Verbosity levels:
    -1 = error (red)
     0 = default (white)
     1 = warning (yellow)
     2 = info (cyan)
     3 = debug (light grey)
    """
    global verbosity_level
    
    # Don't print if verbosity level is too low
    if level > verbosity_level:
        return
    
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "orange": "\033[38;5;208m",
        "grey": "\033[90m",
        "reset": "\033[0m"
    }
    
    # Define default colors and prefixes for each level
    level_config = {
        -1: {"prefix": "[ERROR]:  ", "default_color": "red"},
        1: {"prefix": "[WARNING]:", "default_color": "yellow"},
        2: {"prefix": "[INFO]:   ", "default_color": "cyan"},
        3: {"prefix": "[DEBUG]:  ", "default_color": "grey"},
        0: {"prefix": "", "default_color": "white"}
    }
    
    config = level_config.get(level, level_config[0])
    prefix = config["prefix"]
    
    # Use provided color or default color for the level
    if color is None:
        color = config["default_color"]
    
    color_code = colors.get(color.lower(), colors["white"])
    reset_code = colors["reset"]
    print(f"{color_code}{prefix} {text}{reset_code}")

def arguments_parse():
    """
    Parse command-line arguments.
    Returns the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="PageHawk - A reconnaissance tool for penetration testers and administrators"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input (IP address, file, or range)"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output folder for results"
    )
    parser.add_argument(
        "--proxy-ip",
        help="Proxy IP address"
    )
    parser.add_argument(
        "--proxy-port",
        type=int,
        help="Proxy port"
    )
    parser.add_argument(
        "--proxy-username",
        help="Proxy username (if authentication required)"
    )
    parser.add_argument(
        "--proxy-password",
        help="Proxy password (if authentication required)"
    )
    parser.add_argument(
        "--delay-from",
        type=int,
        help="Minimum delay in milliseconds"
    )
    parser.add_argument(
        "--delay-to",
        type=int,
        help="Maximum delay in milliseconds"
    )
    parser.add_argument(
        "--ports",
        help="Ports to check (comma-separated, or use default1/default2/default3/default_all)"
    )
    parser.add_argument(
        "--subdir-screenshots",
        action="store_true",
        help="Create a 'screenshots' subdirectory for all screenshots"
    )
    parser.add_argument(
        "--subdir-timestamped",
        action="store_true",
        help="Create a timestamped subdirectory (pagehawk-yyyy-mm-dd_hh-mm)"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=10,
        help="Number of concurrent threads (default: 10)"
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (-v=warning, -vv=info, -vvv=debug)"
    )
    
    args = parser.parse_args()
    
    # Set global verbosity level and threads
    global verbosity_level, threads
    verbosity_level = args.v
    threads = args.threads
    
    print2("PageHawk - Reconnaissance Tool", level=0)
    print2("=" * 50, level=0)
    print2(f"Input: {args.input}", level=0)
    print2(f"Output: {args.output}", level=0)
    print2(f"Threads: {threads}", level=0)
    print2("=" * 50, level=0)
    print2("", level=0)
    
    return args

def input_ip_split(input_value):
    """
    Split input value by commas if it contains commas.
    Returns a list of input values.
    """
    if ',' in input_value:
        return [item.strip() for item in input_value.split(',')]
    else:
        return [input_value]

def input_ip_parse_input_file(filepath):
    """
    Parse a file containing targets (IPs, URLs, domains, CIDR ranges).
    Supports multiple formats:
    - One entry per line
    - Comma-separated entries
    - Space-separated entries
    - Tab-separated entries
    - Mixed formats
    
    Returns a list of parsed targets.
    """
    targets = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        print2(f"Reading targets from file: {filepath}", level=3)
        
        # Split by newlines first
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Try splitting by different delimiters
            # First try comma
            if ',' in line:
                parts = [p.strip() for p in line.split(',')]
                targets.extend([p for p in parts if p])
            # Then try tab
            elif '\t' in line:
                parts = [p.strip() for p in line.split('\t')]
                targets.extend([p for p in parts if p])
            # Then try space (but be careful with CIDR notation which has no spaces)
            elif ' ' in line:
                parts = [p.strip() for p in line.split(' ')]
                targets.extend([p for p in parts if p])
            # Single entry per line
            else:
                targets.append(line)
        
        print2(f"Parsed {len(targets)} targets from file", level=3)
        return targets
        
    except FileNotFoundError:
        print2(f"File not found: {filepath}", level=-1)
        return None
    except Exception as e:
        print2(f"Error reading file {filepath}: {str(e)}", level=-1)
        return None

def input_ip_parse_nmap_file(filepath):
    """
    Parse an nmap XML file and extract IP:port combinations for HTTP services.
    Looks for ports with HTTP-related services (http, https, http-proxy, etc.) that are open.
    
    Returns a list of "ip:port" strings, or None on error.
    """
    sockets = []
    
    try:
        # First, check if this is an nmap XML file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '<!DOCTYPE nmaprun>' not in content:
            print2(f"File {filepath} is not a valid nmap XML file (missing DOCTYPE nmaprun)", level=-1)
            return None
        
        print2(f"Parsing nmap XML file: {filepath}", level=3)
        
        # Parse the XML
        root = ET.fromstring(content)
        
        # Iterate through all host elements
        for host in root.findall('host'):
            # Get the IP address from the address element
            address_elem = host.find('address[@addrtype="ipv4"]')
            if address_elem is None:
                # Try IPv6 if IPv4 not found
                address_elem = host.find('address[@addrtype="ipv6"]')
            
            if address_elem is None:
                print2(f"No IP address found for host, skipping", level=3)
                continue
            
            ip_addr = address_elem.get('addr')
            
            # Check for user-provided hostname first
            target = ip_addr  # Default to IP address
            hostnames_elem = host.find('hostnames')
            if hostnames_elem is not None:
                # Look for hostname with type="user"
                for hostname_elem in hostnames_elem.findall('hostname'):
                    if hostname_elem.get('type') == 'user':
                        target = hostname_elem.get('name')
                        print2(f"Found host: {target} (user-provided hostname, IP: {ip_addr})", level=3)
                        break
                else:
                    # No user-provided hostname found, use IP
                    print2(f"Found host: {ip_addr} (no user-provided hostname)", level=3)
            else:
                print2(f"Found host: {ip_addr} (no hostnames)", level=3)
            
            # Find the ports element
            ports_elem = host.find('ports')
            if ports_elem is None:
                print2(f"No ports found for {target}, skipping", level=3)
                continue
            
            # Iterate through all port elements
            for port in ports_elem.findall('port'):
                # Get port ID
                port_id = port.get('portid')
                
                # Check if port is open
                state_elem = port.find('state')
                if state_elem is None or state_elem.get('state') != 'open':
                    print2(f"Port {port_id} on {target} is not open, skipping", level=3)
                    continue
                
                # Check if service is HTTP-related
                service_elem = port.find('service')
                if service_elem is not None:
                    service_name = service_elem.get('name', '').lower()
                    
                    # Look for HTTP-related services
                    http_keywords = ['http', 'https', 'web', 'www']
                    is_http_service = any(keyword in service_name for keyword in http_keywords)
                    
                    if is_http_service:
                        socket = f"{target}:{port_id}"
                        sockets.append(socket)
                        print2(f"Found HTTP service: {socket} (service: {service_name})", level=2)
                    else:
                        print2(f"Port {port_id} on {target} has non-HTTP service: {service_name}, skipping", level=3)
                else:
                    print2(f"No service information for port {port_id} on {target}, skipping", level=3)
        
        print2(f"Parsed {len(sockets)} HTTP sockets from nmap file", level=2)
        return sockets
        
    except FileNotFoundError:
        print2(f"File not found: {filepath}", level=-1)
        return None
    except ET.ParseError as e:
        print2(f"Error parsing XML file {filepath}: {str(e)}", level=-1)
        return None
    except Exception as e:
        print2(f"Error reading nmap file {filepath}: {str(e)}", level=-1)
        return None

def input_ip_check_target_validity(target):
    """
    Check if the given target is valid and add it to the appropriate list.
    Supports: URLs (http://..., https://...), single IPs, CIDR notation, IP:port format, and domain names.
    Returns True if valid, False otherwise.
    """
    try:
        target = target.strip()
        
        # Check 1: Is it a URL? (starts with http:// or https://)
        if target.startswith('http://') or target.startswith('https://'):
            print2(f"Found URL: {target}", level=3)
            urls_to_view.append(target)
            return True
        
        # Check 2: Is it an IP with port? (contains : but not /)
        # This check needs to come before CIDR check to avoid confusion
        if ':' in target and '/' not in target:
            # Try to validate if it's IP:port format
            parts = target.split(':')
            if len(parts) == 2:
                ip_part = parts[0]
                port_part = parts[1]
                
                try:
                    # Validate IP part
                    ipaddress.ip_address(ip_part)
                    # Validate port part
                    port_num = int(port_part)
                    if 1 <= port_num <= 65535:
                        print2(f"Found IP:port socket: {target}", level=3)
                        sockets_to_view.append(target)
                        return True
                    else:
                        print2(f"Port out of range in socket: {target}", level=-1)
                        return False
                except (ValueError, ipaddress.AddressValueError):
                    # Not a valid IP:port, might be a domain:port or URL without protocol
                    print2(f"Found domain:port or URL without protocol: {target}", level=3)
                    urls_to_view.append(target)
                    return True
            
        # Check 3: Is it CIDR notation? (contains /)
        # But first, we need to distinguish between CIDR and URL paths
        if '/' in target:
            # Try to parse the part before the slash
            slash_parts = target.split('/', 1)
            base_part = slash_parts[0]
            
            # Try to validate if base_part is an IP address
            try:
                ipaddress.ip_address(base_part)
                # It's an IP, so this might be CIDR notation
                # Now try to parse as CIDR
                try:
                    print2(f"Found CIDR notation: {target}", level=3)
                    network = ipaddress.ip_network(target, strict=False)
                    for host in network.hosts():
                        ips_to_view.append(str(host))
                    # If it's a /32 or /31, hosts() returns empty, so add network address
                    if network.num_addresses <= 2:
                        ips_to_view.append(str(network.network_address))
                    print2(f"Expanded CIDR to {len(list(network.hosts()))} IPs", level=3)
                    return True
                except (ValueError, ipaddress.AddressValueError) as e:
                    # Not valid CIDR, treat as URL with path
                    print2(f"Found URL with path: {target}", level=3)
                    urls_to_view.append(target)
                    return True
            except ValueError:
                # Base part is not an IP, so this is a URL/domain with path
                print2(f"Found URL with path: {target}", level=3)
                urls_to_view.append(target)
                return True
        
        # Check 4: Is it a plain IP address?
        try:
            ipaddress.ip_address(target)
            print2(f"Found IP address: {target}", level=3)
            ips_to_view.append(target)
            return True
        except ValueError:
            # Not a valid IP, might be a domain name
            pass
        
        # Check 5: Treat as domain name or URL without protocol
        if len(target) > 0:
            print2(f"Found domain name or URL: {target}", level=3)
            urls_to_view.append(target)
            return True
        
        # If we got here, target is empty or invalid
        print2(f"Could not parse target: {target}", level=-1)
        return False
        
    except Exception as e:
        print2(f"Error parsing target '{target}': {str(e)}", level=-1)
        return False

def input_ip_parse(input_value):
    """
    Process the input value and validate if it's a valid target (IP, URL, domain, etc.).
    First checks if the input is a file path, and if so, parses the file.
    Supports nmap XML files (.xml extension).
    Returns True if valid, False otherwise.
    """
    input_list = []
    
    # First, check if input_value is a file
    if os.path.isfile(input_value):
        print2(f"Input is a file: {input_value}", level=2)
        
        # Check if it's an XML file (potentially nmap output)
        if input_value.lower().endswith('.xml'):
            print2("Detected XML file, attempting to parse as nmap output", level=2)
            parsed_sockets = input_ip_parse_nmap_file(input_value)
            
            if parsed_sockets is None:
                print2("Failed to parse as nmap XML file, trying as regular file", level=1)
                # Fall back to regular file parsing
                parsed_targets = input_ip_parse_input_file(input_value)
                if parsed_targets is None:
                    print2("Failed to parse input file", level=-1)
                    return False
                input_list = parsed_targets
            else:
                # Successfully parsed nmap file, add sockets directly
                print2(f"Successfully parsed nmap XML file with {len(parsed_sockets)} HTTP sockets", level=2)
                sockets_to_view.extend(parsed_sockets)
                
                # Print summary
                print2(f"Total sockets from nmap: {len(parsed_sockets)}", level=2)
                if len(parsed_sockets) > 0:
                    print2(f"Sockets: {', '.join(parsed_sockets)}", level=3)
                
                # Return early since we already added to sockets_to_view
                return True
        else:
            # Regular text file
            parsed_targets = input_ip_parse_input_file(input_value)
            
            if parsed_targets is None:
                print2("Failed to parse input file", level=-1)
                return False
            
            input_list = parsed_targets
    else:
        # Not a file, treat as direct input (may contain commas)
        input_list = input_ip_split(input_value)
    
    # Now validate each entry
    all_valid = True
    for item in input_list:
        if not input_ip_check_target_validity(item):
            all_valid = False
    
    # Print summary of parsed targets
    print2(f"Total IPs to check: {len(ips_to_view)}", level=2)
    print2(f"Total URLs to check: {len(urls_to_view)}", level=2)
    print2(f"Total sockets to check: {len(sockets_to_view)}", level=2)
    
    if len(ips_to_view) > 0:
        print2(f"IPs: {', '.join(ips_to_view)}", level=3)
    if len(urls_to_view) > 0:
        print2(f"URLs: {', '.join(urls_to_view)}", level=3)
    if len(sockets_to_view) > 0:
        print2(f"Sockets: {', '.join(sockets_to_view)}", level=3)
    
    return all_valid

def input_port_split(port_value):
    """
    Split port value by commas if it contains commas.
    Returns a list of port values.
    """
    if ',' in port_value:
        return [item.strip() for item in port_value.split(',')]
    else:
        return [port_value]

def input_port_check_validity(port):
    """
    Check if the given port is valid and add it to ports_to_view if valid.
    Returns True if valid, False otherwise.
    """
    try:
        port_num = int(port)
        if 1 <= port_num <= 65535:
            ports_to_view.append(port_num)
            return True
        else:
            print2(f"Port out of range (1-65535): {port}", level=-1)
            return False
    except ValueError:
        print2(f"Could not parse port number: {port}", level=-1)
        return False

def input_port_parse(args):
    """
    Process the ports argument and validate ports.
    Returns True if valid, False otherwise.
    """
    global ports_to_view
    
    # If no ports specified, use default
    if not args.ports:
        print2("No ports specified, using DEFAULT_PORTS_ALL", level=2)
        ports_to_view = DEFAULT_PORTS_ALL.copy()
    else:
        # Split by commas
        port_list = input_port_split(args.ports)
        
        all_valid = True
        for item in port_list:
            item_lower = item.lower()
            
            # Check for default keywords
            if item_lower in ["default", "default1"]:
                print2("Adding DEFAULT_PORTS_1", level=3)
                ports_to_view.extend(DEFAULT_PORTS_1)
            elif item_lower == "default2":
                print2("Adding DEFAULT_PORTS_2", level=3)
                ports_to_view.extend(DEFAULT_PORTS_2)
            elif item_lower == "default3":
                print2("Adding DEFAULT_PORTS_3", level=3)
                ports_to_view.extend(DEFAULT_PORTS_3)
            elif item_lower == "default_all":
                print2("Adding DEFAULT_PORTS_ALL", level=3)
                ports_to_view.extend(DEFAULT_PORTS_ALL)
            else:
                # Try to parse as port number
                if not input_port_check_validity(item):
                    all_valid = False
        
        if not all_valid:
            return False
    
    # Remove duplicates while preserving order
    ports_to_view = list(dict.fromkeys(ports_to_view))
    
    # Print port count and list at info level
    print2(f"Total ports to check: {len(ports_to_view)}", level=2)
    print2(f"Ports: {', '.join(map(str, ports_to_view))}", level=3)
    
    return True

def build_sockets():
    """
    Build sockets_to_view from ips_to_view, ports_to_view, and urls_to_view.
    For IPs: Creates IP:port combinations
    For URLs: Creates URL with port combinations (will be converted to http:// or https:// later)
    Returns True if successful.
    """
    global sockets_to_view
    
    # Add IP:port combinations
    for ip in ips_to_view:
        for port in ports_to_view:
            socket = f"{ip}:{port}"
            sockets_to_view.append(socket)
    
    # Add URL:port combinations (same as IPs now)
    for url in urls_to_view:
        for port in ports_to_view:
            socket = f"{url}:{port}"
            sockets_to_view.append(socket)
    
    total_ip_combinations = len(ips_to_view) * len(ports_to_view)
    total_url_combinations = len(urls_to_view) * len(ports_to_view)
    
    print2(f"Total targets to check: {len(sockets_to_view)}", level=2)
    print2(f"  - IP:port combinations: {total_ip_combinations}", level=3)
    print2(f"  - URL:port combinations: {total_url_combinations}", level=3)
    
    return True

def build_visits():
    """
    Build the visits dictionary to track visited targets grouped by IP/URL with ports.
    New structure: {"ips": [{"ip": "", "url": "", "ports": [{port_num: {data}}]}]}
    Loads the structure from visits_template.json and creates entries for each target.
    """
    global visits
    
    # Load template
    try:
        with open(get_resource_path("visits_template.json"), "r") as f:
            template = json.load(f)
        print2("Loaded visits_template.json", level=3)
    except Exception as e:
        print2(f"Error loading visits_template.json: {str(e)}", level=-1)
        return False
    
    # Initialize visits with the new structure
    visits = {"ips": []}
    
    # Dictionary to group ports by IP/URL
    # Key: IP address or URL, Value: list of ports
    target_ports_map = {}
    
    # Process all targets and group by IP/URL
    for target in sockets_to_view:
        ip = ""
        url = ""
        port = ""
        
        # All targets are now in format "target:port"
        if ':' in target:
            parts = target.rsplit(':', 1)  # Split from right to get last colon (port)
            target_base = parts[0]
            port = parts[1]
            
            # Check if target_base is an IP address
            try:
                ipaddress.ip_address(target_base)
                # It's an IP
                ip = target_base
                target_key = ip
                print2(f"Processing IP:port: {ip}:{port}", level=3)
            except ValueError:
                # It's a URL/domain
                url = target_base
                target_key = url
                print2(f"Processing URL:port: {url}:{port}", level=3)
        else:
            # This shouldn't happen anymore, but handle it just in case
            print2(f"Warning: Target without port: {target}", level=1)
            continue
        
        # Add to the mapping
        if target_key not in target_ports_map:
            target_ports_map[target_key] = {
                "ip": ip,
                "url": url,
                "ports": []
            }
        
        # Add port to the list (avoid duplicates)
        if port not in target_ports_map[target_key]["ports"]:
            target_ports_map[target_key]["ports"].append(port)
    
    # Build the final structure
    for target_key, target_data in target_ports_map.items():
        ip_entry = {
            "ip": target_data["ip"],
            "url": target_data["url"],
            "ports": []
        }
        
        # Add each port with empty visit data
        for port in target_data["ports"]:
            port_entry = {
                port: {
                    "response": "",
                    "visited_first": "",
                    "visited_last": "",
                    "user_agent": "",
                    "screenshot_path_full": "",
                    "screenshot_path_relative": "",
                    "screenshot_pathname": "",
                    "screenshot_filename": ""
                }
            }
            ip_entry["ports"].append(port_entry)
        
        visits["ips"].append(ip_entry)
    
    total_targets = sum(len(ip_entry["ports"]) for ip_entry in visits["ips"])
    print2(f"Built visits structure with {len(visits['ips'])} unique IPs/URLs and {total_targets} total port entries", level=3)
    print2(f"Visits structure: {visits}", level=3)
    
    return True

def output_check(output_value, args):
    """
    Check if the output path is valid and we have permissions to write there.
    If output ends with .html, extract the filename.
    Creates subdirectories based on --subdir-screenshots and --subdir-timestamped flags.
    Returns True if valid, False otherwise.
    """
    global output_filename, output_path, subdir_screenshots, subdir_timestamped, output_json_final_filename
    
    print2(f"Checking output: {output_value}", level=3)
    
    try:
        import os
        
        temp_output_path = output_value
        filename_provided = False
        
        # Check if output ends with .html
        if output_value.endswith('.html'):
            print2("Output has .html extension, extracting filename", level=3)
            # Split path and filename
            temp_output_path = os.path.dirname(output_value)
            output_filename = os.path.basename(output_value)
            print2(f"Extracted path: {temp_output_path}", level=3)
            print2(f"Extracted filename: {output_filename}", level=3)
            filename_provided = True
            
            # If path is empty, use current directory
            if not temp_output_path:
                temp_output_path = "."
        
        # Check if path is a valid directory
        if not os.path.isdir(temp_output_path):
            print2(f"Output path does not exist: {temp_output_path}", level=-1)
            return False
        
        # Check if we have write permissions
        test_file = os.path.join(temp_output_path, ".pagehawk_test")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print2(f"Write permissions verified for: {temp_output_path}", level=3)
        except (IOError, OSError) as e:
            print2(f"No write permissions for path: {temp_output_path}", level=-1)
            print2(f"Error: {str(e)}", level=-1)
            return False
        
        # Set global flags
        subdir_screenshots = args.subdir_screenshots
        subdir_timestamped = args.subdir_timestamped
        
        # Determine JSON filename based on provided arguments
        if filename_provided:
            # Use the provided filename but change extension to .json
            output_json_final_filename = output_filename.replace('.html', '.json')
        elif subdir_timestamped:
            # Use timestamped filename
            timestamp = datetime.now().strftime("pagehawk-%Y-%m-%d_%H-%M")
            output_json_final_filename = f"{timestamp}.json"
        else:
            # Use default
            output_json_final_filename = output_json_filename
        
        # Create timestamped subdirectory if requested
        if subdir_timestamped:
            timestamp = datetime.now().strftime("pagehawk-%Y-%m-%d_%H-%M")
            temp_output_path = os.path.join(temp_output_path, timestamp)
            os.makedirs(temp_output_path, exist_ok=True)
            print2(f"Created timestamped directory: {temp_output_path}", level=3)
        
        # Create screenshots subdirectory if requested
        if subdir_screenshots:
            screenshots_path = os.path.join(temp_output_path, "screenshots")
            os.makedirs(screenshots_path, exist_ok=True)
            print2(f"Created screenshots directory: {screenshots_path}", level=3)
        
        # Store the output path globally
        output_path = temp_output_path
        
        # Construct full output path
        full_output_path = os.path.join(output_path, output_filename)
        print2(f"Saving output to {full_output_path}", level=0)
        print2(f"JSON will be saved as: {output_json_final_filename}", level=3)
        
        return True
        
    except Exception as e:
        print2(f"Error checking output path: {str(e)}", level=-1)
        return False

def output_save():
    """
    Save output to the specified output folder.
    Generates HTML report and saves it along with the JSON data.
    """
    print2("\nGenerating HTML report...", level=0)
    
    try:
        # Generate the HTML content
        html_content = generate_html()
        
        if not html_content:
            print2("Failed to generate HTML content", level=-1)
            return False
        
        # Determine HTML filename based on same logic as JSON
        global output_filename
        if not output_filename or output_filename == "pagehawk_results.html":
            # Check if we have a custom JSON filename to derive from
            if output_json_final_filename != "pagehawk_results.json":
                output_filename = output_json_final_filename.replace('.json', '.html')
            else:
                output_filename = "pagehawk_results.html"
        
        # Save HTML file
        html_file_path = os.path.join(output_path, output_filename)
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print2(f"HTML report saved to: {html_file_path}", level=0)
        print2(f"JSON data saved to: {os.path.join(output_path, output_json_final_filename)}", level=0)
        print2("\nReconnaissance complete!", level=0, color="green")
        
        return True
        
    except Exception as e:
        print2(f"Error saving output: {str(e)}", level=-1)
        return False

def generate_html():
    """
    Generate HTML output from the visits data.
    Creates a standalone HTML file with embedded CSS, JS, and data.
    """
    try:
        # Read the HTML template
        with open(get_resource_path("report_template.html"), "r", encoding="utf-8") as f:
            html_template = f.read()
        
        # Read the CSS file
        with open(get_resource_path("report_template.css"), "r", encoding="utf-8") as f:
            css_content = f.read()
        
        # Read the JS file
        with open(get_resource_path("report_template.js"), "r", encoding="utf-8") as f:
            js_content = f.read()
        
        # Read and encode the logo as base64
        logo_base64 = ""
        try:
            with open(get_resource_path("pagehawk_logo.png"), "rb") as f:
                logo_data = f.read()
                logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            print2("Loaded and encoded logo as base64", level=3)
        except FileNotFoundError:
            print2("Warning: pagehawk_logo.png not found, logo will not be embedded", level=1)
        except Exception as e:
            print2(f"Warning: Could not read logo file: {str(e)}", level=1)
        
        print2("Loaded template files", level=3)
        
        # Prepare the JSON data
        json_data = json.dumps(visits, indent=2)
        
        # Create the style tag with CSS
        css_block = f"<style>\n{css_content}\n    </style>"
        
        # Create the data script tag
        data_block = f"<script>\n        let json_data = {json_data};\n    </script>"
        
        # Create the JS script tag
        js_block = f"<script>\n{js_content}\n    </script>"
        
        # Replace placeholders
        html_output = html_template.replace("{{CSS_PLACEHOLDER}}", css_block)
        html_output = html_output.replace("{{DATA_PLACEHOLDER}}", data_block)
        html_output = html_output.replace("{{JS_PLACEHOLDER}}", js_block)
        
        # Replace logo src with base64 data URI if logo was loaded
        if logo_base64:
            html_output = html_output.replace('src="pagehawk_logo.png"', f'src="data:image/png;base64,{logo_base64}"')
        
        print2("Generated standalone HTML with embedded assets", level=3)
        
        return html_output
        
    except FileNotFoundError as e:
        print2(f"Template file not found: {str(e)}", level=-1)
        return None
    except Exception as e:
        print2(f"Error generating HTML: {str(e)}", level=-1)
        return None

def ready_to_start_recon():
    """
    Perform pre-recon checks to ensure everything is set up correctly.
    Returns True if ready, False otherwise.
    """
    # Check if visits dict is populated with new structure
    if not visits or "ips" not in visits or len(visits["ips"]) == 0:
        print2("No targets to process", level=-1)
        return False
    
    # Count total port entries
    total_ports = sum(len(ip_entry["ports"]) for ip_entry in visits["ips"])
    print2(f"Ready to start recon for {len(visits['ips'])} IPs/URLs with {total_ports} total port checks", level=2)
    
    return True

def visit_website(ip_entry, port_key, port_data):
    """
    Visit a website at the given IP:port or URL:port, render JavaScript, and take a screenshot.
    Updates the port_data dictionary with timestamp and response status.
    
    Port 80 uses http:// without :80 suffix, no HTTPS fallback
    Port 443 uses https:// without :443 suffix
    Other ports use http://target:port format with HTTPS fallback
    
    Args:
        ip_entry: The IP/URL entry from visits["ips"]
        port_key: The port number (as string)
        port_data: The data dictionary for this specific port
    """
    ip = ip_entry["ip"]
    url_target = ip_entry["url"]
    
    # Determine if this is a URL or IP target
    is_url_target = bool(url_target)
    target_base = url_target if is_url_target else ip
    
    # Build display target
    display_target = f"{target_base}:{port_key}"
    print2(f"Visiting website {display_target}", level=2)
    
    response_status = "unreachable"
    screenshot_path = None
    
    # Determine protocol and port suffix based on port number
    port_num = int(port_key)
    use_https_fallback = True  # By default, try HTTPS if HTTP fails
    
    if port_num == 80:
        protocol = "http"
        port_suffix = ""  # Don't add :80
        use_https_fallback = False  # Don't try HTTPS for port 80
    elif port_num == 443:
        protocol = "https"
        port_suffix = ""  # Don't add :443
        use_https_fallback = False  # Already HTTPS, no fallback needed
    else:
        protocol = "http"
        port_suffix = f":{port_key}"
        use_https_fallback = True  # Try HTTPS if HTTP fails for other ports
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            
            # Create context with SSL verification disabled
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # Set timeout (increased for slower loading pages)
            page.set_default_timeout(30000)
            
            # Build initial URL
            if is_url_target:
                # Handle URL with potential path
                if '/' in url_target:
                    parts = url_target.split('/', 1)
                    domain = parts[0]
                    path = parts[1]
                    url = f"{protocol}://{domain}{port_suffix}/{path}"
                else:
                    url = f"{protocol}://{url_target}{port_suffix}"
            else:
                # IP address
                url = f"{protocol}://{ip}{port_suffix}"
            
            print2(f"Trying {url}", level=3)
            
            try:
                response = page.goto(url, wait_until="domcontentloaded")
                
                # Wait a bit for any dynamic content to load
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    # If networkidle times out, that's okay, we already have domcontentloaded
                    print2(f"Network didn't become idle, but page loaded", level=3)
                
                # Get HTTP status code
                if response:
                    response_status = str(response.status)
                    print2(f"{protocol.upper()} response: {response_status}", level=3)
                else:
                    response_status = "no_response"
                
                # Generate screenshot filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if is_url_target:
                    # Sanitize URL for filename
                    safe_filename = url_target.replace('://', '_').replace('/', '_').replace(':', '_').replace('.', '_')
                    screenshot_filename = f"{safe_filename}_{port_key}_{timestamp}.png"
                else:
                    screenshot_filename = f"{ip.replace('.', '_')}_{port_key}_{timestamp}.png"
                
                # Determine screenshot save path
                if subdir_screenshots:
                    screenshot_path = os.path.join(output_path, "screenshots", screenshot_filename)
                else:
                    screenshot_path = os.path.join(output_path, screenshot_filename)
                
                # Take screenshot
                page.screenshot(path=screenshot_path, full_page=True)
                
                print2(f"Screenshot saved: {screenshot_filename}", level=3)
                
                browser.close()
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Determine error type
                if "timeout" in error_str or "navigationtimeout" in error_str:
                    response_status = "timeout"
                elif "refused" in error_str or "econnrefused" in error_str:
                    response_status = "refused"
                elif "reset" in error_str:
                    response_status = "reset"
                else:
                    response_status = "error"
                
                # Only try HTTPS fallback if enabled for this port
                if use_https_fallback:
                    print2(f"HTTP failed ({response_status}), trying HTTPS", level=3)
                    
                    # Build HTTPS URL
                    if is_url_target:
                        if '/' in url_target:
                            parts = url_target.split('/', 1)
                            domain = parts[0]
                            path = parts[1]
                            url = f"https://{domain}{port_suffix}/{path}"
                        else:
                            url = f"https://{url_target}{port_suffix}"
                    else:
                        url = f"https://{ip}{port_suffix}"
                    
                    print2(f"Trying {url}", level=3)
                    
                    try:
                        response = page.goto(url, wait_until="domcontentloaded")
                        
                        # Wait a bit for any dynamic content to load
                        try:
                            page.wait_for_load_state("networkidle", timeout=5000)
                        except:
                            # If networkidle times out, that's okay, we already have domcontentloaded
                            print2(f"Network didn't become idle, but page loaded", level=3)
                        
                        # Get HTTP status code
                        if response:
                            response_status = str(response.status)
                            print2(f"HTTPS response: {response_status}", level=3)
                        else:
                            response_status = "no_response"
                        
                        # Generate screenshot filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        if is_url_target:
                            # Sanitize URL for filename
                            safe_filename = url_target.replace('://', '_').replace('/', '_').replace(':', '_').replace('.', '_')
                            screenshot_filename = f"{safe_filename}_{port_key}_{timestamp}.png"
                        else:
                            screenshot_filename = f"{ip.replace('.', '_')}_{port_key}_{timestamp}.png"
                        
                        # Determine screenshot save path
                        if subdir_screenshots:
                            screenshot_path = os.path.join(output_path, "screenshots", screenshot_filename)
                        else:
                            screenshot_path = os.path.join(output_path, screenshot_filename)
                        
                        # Take screenshot
                        page.screenshot(path=screenshot_path, full_page=True)
                        
                        print2(f"Screenshot saved: {screenshot_filename}", level=3)
                        
                        browser.close()
                        
                    except Exception as e2:
                        error_str2 = str(e2).lower()
                        
                        # Determine error type
                        if "timeout" in error_str2 or "navigationtimeout" in error_str2:
                            response_status = "timeout"
                        elif "refused" in error_str2 or "econnrefused" in error_str2:
                            response_status = "refused"
                        elif "reset" in error_str2:
                            response_status = "reset"
                        else:
                            response_status = "unreachable"
                        
                        print2(f"Failed to connect to {url} - {response_status}", level=3)
                        print2(f"Error details: {str(e2)[:200]}", level=3)
                        browser.close()
                else:
                    # No HTTPS fallback, just report the failure
                    print2(f"Failed to connect to {url} - {response_status}", level=3)
                    print2(f"Error details: {str(e)[:200]}", level=3)
                    browser.close()
                
    except Exception as e:
        print2(f"Error visiting {display_target} - {str(e)}", level=-1)
        response_status = "error"
    
    # Update port data
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if this is the first visit
    if port_data["visited_first"] == "":
        port_data["visited_first"] = current_timestamp
        port_data["visited_last"] = current_timestamp
    else:
        # Update only the last visit timestamp
        port_data["visited_last"] = current_timestamp
    
    port_data["response"] = response_status
    
    # Save screenshot paths in three formats
    if screenshot_path:
        port_data["screenshot_path_relative"] = screenshot_path
        port_data["screenshot_path_full"] = os.path.abspath(screenshot_path)
        port_data["screenshot_pathname"] = output_screenshots_pathname
        port_data["screenshot_filename"] = os.path.basename(screenshot_path)
    
    # Save visits to JSON file after each visit (thread-safe)
    try:
        with json_write_lock:  # Acquire lock before writing
            json_file_path = os.path.join(output_path, output_json_final_filename)
            with open(json_file_path, 'w') as f:
                json.dump(visits, f, indent=4)
        print2(f"Saved visits to {output_json_final_filename}", level=3)
    except Exception as e:
        print2(f"Error saving visits JSON: {str(e)}", level=-1)
    
    return True

def main_recon_process():
    """
    Main reconnaissance process using multithreading for concurrent visits.
    New structure: visits["ips"] contains IP/URL entries, each with a "ports" array.
    """
    global start_time
    
    print2("\nStarting the recon process...", level=0)
    print2(f"Using {threads} concurrent threads", level=0, color="cyan")
    print2('(You can interrupt / pause this process by pressing "escape". An additional prompt will be asked to truely abort the process)', color="yellow", level=0)
    print2("", level=0)
    
    # Start the timer
    start_time = time.time()
    
    # Collect all tasks (ip_entry, port_key, port_data tuples)
    tasks = []
    for ip_entry in visits["ips"]:
        for port_entry in ip_entry["ports"]:
            for port_key, port_data in port_entry.items():
                tasks.append((ip_entry, port_key, port_data))
    
    total_tasks = len(tasks)
    completed_tasks = 0
    
    print2(f"Total targets to scan: {total_tasks}", level=2)
    
    # Use ThreadPoolExecutor for concurrent execution
    with ThreadPoolExecutor(max_workers=threads) as executor:
        # Submit all tasks
        future_to_task = {
            executor.submit(visit_website, ip_entry, port_key, port_data): (ip_entry, port_key, port_data)
            for ip_entry, port_key, port_data in tasks
        }
        
        # Process completed tasks
        for future in as_completed(future_to_task):
            completed_tasks += 1
            ip_entry, port_key, port_data = future_to_task[future]
            
            try:
                future.result()  # This will raise any exceptions that occurred
                if verbosity_level < 2:  # Only show progress if not in verbose mode
                    target = ip_entry["url"] if ip_entry["url"] else ip_entry["ip"]
                    print2(f"Progress: {completed_tasks}/{total_tasks} - Completed {target}:{port_key}", level=0)
            except Exception as e:
                target = ip_entry["url"] if ip_entry["url"] else ip_entry["ip"]
                print2(f"Exception in thread for {target}:{port_key} - {str(e)}", level=-1)
    
    # Calculate elapsed time
    end_time = time.time()
    elapsed_seconds = int(end_time - start_time)
    
    # Format time display
    if elapsed_seconds >= 60:
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        time_str = f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
    else:
        time_str = f"{elapsed_seconds} second{'s' if elapsed_seconds != 1 else ''}"
    
    print2(f"\nCompleted all {total_tasks} scans in {time_str}", level=0, color="green")

def main():
    args = arguments_parse()
    
    if not input_ip_parse(args.input):
        print2("Input validation failed.", level=-1)
        sys.exit(1)
    
    if not input_port_parse(args):
        print2("Port validation failed.", level=-1)
        sys.exit(1)

    if not build_sockets():
        print2("Socket building failed.", level=-1)
        sys.exit(1)
    
    if not build_visits():
        print2("Visits building failed.", level=-1)
        sys.exit(1)
    
    if not output_check(args.output, args):
        print2("Output folder validation failed.", level=-1)
        sys.exit(1)
    
    if not ready_to_start_recon():
        print2("Pre-recon checks failed.", level=-1)
        sys.exit(1)
    
    main_recon_process()
    
    output_save()

if __name__ == "__main__":
    main()
