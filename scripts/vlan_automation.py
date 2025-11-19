from netmiko import ConnectHandler
from getpass import getpass
import json
import os

def vlan_automation():
    # Get credentials securely
    username = input("Enter Your UserName: ")
    password = getpass("Enter Your Password: ")
    secret = getpass("Enter Your Enable Password: ")
    
    # Get VLAN details
    which_vlan = input("Which VLAN do you want to check/create?: ")
    vlan_name = input("VLAN name?: ")
    
    # Validate VLAN input
    try:
        vlan_id = int(which_vlan)
        if vlan_id < 1 or vlan_id > 4094:
            print("Error: VLAN ID must be between 1 and 4094")
            return
    except ValueError:
        print("Error: VLAN ID must be a number")
        return

    # Load switch IPs from JSON file
    try:
        with open('inventories/switches.json', 'r') as json_file:
            ip_list = json.load(json_file)
    except FileNotFoundError:
        print("Error: switches.json file not found. Please create it in the inventories folder.")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in switches.json")
        return

    for switch_name, ip in ip_list.items():
        device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': username,
            'password': password,
            'secret': secret,
            'timeout': 30,  # Increased timeout for Packet Tracer
            'session_timeout': 60,
        }
        
        try:
            print(f"\n{'='*50}")
            print(f"Connecting to {switch_name} ({ip})...")
            
            # Establish connection
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            
            # Check if VLAN exists - using show vlan brief
            print(f"Checking if VLAN {vlan_id} exists...")
            show_vlan_output = net_connect.send_command('show vlan brief')
            
            vlan_exists = False
            vlan_current_name = ""
            
            # Parse the show vlan brief output
            for line in show_vlan_output.split('\n'):
                if line.strip().startswith(str(vlan_id)):
                    # Found the VLAN in output
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == str(vlan_id):
                        vlan_exists = True
                        vlan_current_name = parts[1] if len(parts) > 1 else "Unknown"
                        break
            
            if vlan_exists:
                print(f'VLAN {vlan_id} ({vlan_current_name}) already exists on {switch_name}')
                
                # Check if name needs update
                if vlan_current_name != vlan_name:
                    update_name = input(f"VLAN name differs. Current: '{vlan_current_name}', New: '{vlan_name}'. Update? (y/n): ")
                    if update_name.lower() == 'y':
                        commands = [
                            f'vlan {vlan_id}',
                            f'name {vlan_name}',
                        ]
                        output = net_connect.send_config_set(commands)
                        print(f'Updated VLAN {vlan_id} name to {vlan_name}')
                        print(f"Configuration output: {output}")
            else:
                # Create VLAN if it doesn't exist
                print(f'Creating VLAN {vlan_id} with name {vlan_name}...')
                commands = [
                    f'vlan {vlan_id}',
                    f'name {vlan_name}',
                ]
                output = net_connect.send_config_set(commands)
                print(f'Successfully created VLAN {vlan_id} on {switch_name}')
                print(f"Configuration output: {output}")
                
                # Verify VLAN creation
                verify_output = net_connect.send_command(f'show vlan id {vlan_id}')
                if str(vlan_id) in verify_output and vlan_name in verify_output:
                    print(f"✓ VLAN {vlan_id} verified successfully")
                else:
                    print(f"⚠ Warning: VLAN verification may have failed")
            
            # Show final VLAN status
            final_check = net_connect.send_command(f'show vlan id {vlan_id}')
            print(f"\nFinal VLAN status:")
            print(final_check)
            
            net_connect.disconnect()
            print(f"Disconnected from {switch_name}")
            
        except Exception as e:
            print(f'❌ Failed to configure {switch_name} ({ip}): {str(e)}')
            print(f"Error type: {type(e).__name__}")

def interface_automation():
    """Additional function for interface description updates"""
    username = input("Enter Your UserName: ")
    password = getpass("Enter Your Password: ")
    secret = getpass("Enter Your Enable Password: ")
    
    try:
        with open('inventories/switches.json', 'r') as json_file:
            ip_list = json.load(json_file)
    except FileNotFoundError:
        print("Error: switches.json file not found.")
        return

    for switch_name, ip in ip_list.items():
        device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': username,
            'password': password,
            'secret': secret,
            'timeout': 30,
        }
        
        try:
            print(f"\n{'='*50}")
            print(f"Connecting to {switch_name} ({ip}) for interface audit...")
            
            net_connect = ConnectHandler(**device)
            net_connect.enable()
            
            # Get interface status
            interfaces = net_connect.send_command('show ip interface brief', use_textfsm=True)
            print("\nCurrent Interface Status:")
            print("Interface\tIP Address\tStatus\tProtocol")
            for interface in interfaces:
                print(f"{interface['intf']}\t{interface['ipaddr']}\t{interface['status']}\t{interface['proto']}")
            
            # Update interface descriptions
            interface_name = input("\nEnter interface to update (e.g., FastEthernet0/1): ")
            description = input("Enter new description: ")
            
            commands = [
                f'interface {interface_name}',
                f'description {description}',
            ]
            
            output = net_connect.send_config_set(commands)
            print(f"Updated interface {interface_name}")
            print(f"Configuration output: {output}")
            
            net_connect.disconnect()
            
        except Exception as e:
            print(f'Failed to configure interfaces on {switch_name}: {str(e)}')

if __name__ == "__main__":
    print("Cisco Network Automation Tool")
    print("1. VLAN Automation")
    print("2. Interface Description Automation")
    
    choice = input("Select option (1 or 2): ")
    
    if choice == "1":
        vlan_automation()
    elif choice == "2":
        interface_automation()
    else:
        print("Invalid choice")