#__Program Function      : Connect to device, get interface information, print errors to file
#__Date                  : 19-02-2019
#__Author                : Jonatan Lauenstein

import paramiko
import datetime
import csv
import time
import getpass 
import sys, os
NETWORK_DEVICES = [""]


########################################################################################################################################################
#FUNCTIONS DESCRIPTIONS:                                                                                                                               #  
#get_username_and_password:             Promts user for username and password and saves it                                                             #
#get_hostname:                          Connects to device and returns a string of the hostname                                                        #
#get_correct_interface_name_and_type:   Connects to device and get all interfaces with T P I enabled                                                   #
#get_interface_ap_info:                 Connects to device and gets a long string of interface information, does some string manipulation              #                                                          #
#get_time:                              Checks the local time and date, strips the date                                                                #    
#deploy_to_file:                        Stores correct information in a .csv file                                                                      #
#connect_to_device:                     Establishes a connection to a device                                                                           #
#                                                                                                                                                      #
#FUNCTION INPUT:                                                                                                                                       #
#get_username_and_password:             String(IP of device), and uses getpass function to hide password                                               #
#get_hostname:                          String(IP of device) + String(Username) and String(Password)                                                   #
#get_correct_interface_name_and_type:   String(IP of device) + String(Username) and String(Password)                                                   #
#get_interface_ap_info:                 String(IP of device) + String(Username) and String(Password) + Dictunary{Interface NUMBER: Interface TYPE}     #
#get_time:                              No input (Uses datetime to get current date)                                                                   #
#deploy_to_file:                        Dictunary{Interface Name + Number:{Input Packets:xxx, Input Errors:xxx, Output Packets:xxx, Output Errors:xxx}}#
#                                       + String(Device Name), String(Date)                                                                            #
#connect_to_device:                     String(IP of device) + String(Username) and String(Password)                                                   #                          #
########################################################################################################################################################


####################################################################################################################
####################################################################################################################
def main():
    #Take list of IP addresses and connect to them one at a time (SHOULD BE A FILE OF DEVICES!)

    for ip_of_device in NETWORK_DEVICES:
        username_and_password = get_username_and_password(ip_of_device)
        device_name = get_hostname(ip_of_device, username_and_password)
        print("Connecting to device:", device_name)
        
        interfaces_dict = get_correct_interface_name_and_type(ip_of_device, username_and_password)

        information_from_device = get_interface_ap_info(interfaces_dict, ip_of_device, username_and_password)

        date = get_time()
        
        errors_found = deploy_to_file(information_from_device, date, device_name)

    input("Press any key to exit")

####################################################################################################################
####################################################################################################################

def get_username_and_password(ip_of_device):
    print("IP of device:", ip_of_device)
    input_username = input("Username: ")
    try:
        input_password = getpass.getpass()
    
    except Exception as error:
        print(error)
        input("")
    list_of_loggin_details = []
    list_of_loggin_details.append(input_username)
    list_of_loggin_details.append(input_password)
    return list_of_loggin_details

####################################################################################################################
####################################################################################################################

def get_hostname(ip_of_device, username_and_password):
    ssh_connection = connect_to_device(ip_of_device, username_and_password)
    cisco_hostname_command = "show running-config view | include hostname"
    (stdin, stdout, stderr) = ssh_connection.exec_command(cisco_hostname_command)
    hostname_initial_string = stdout.readlines()
    hostname = hostname_initial_string[0].replace('hostname ', '').replace('\r\n', '')
    return hostname

####################################################################################################################
####################################################################################################################

def get_correct_interface_name_and_type(ip_of_device, username_and_password):
    try:
        cisco_command = ("show cdp neighbors | include T B I")
        ssh_connection = connect_to_device(ip_of_device, username_and_password)
        (stdin, stdout, stderr) = ssh_connection.exec_command(cisco_command)
        correct_output = stdout.readlines()
        list_of_needed_interfaces_unfilted = []
        list_of_unsorted_interfaces_filtered = []
        dict_interfacetype_interfacenumber = {}
        for unfiltered_output in correct_output:
            if "Gig" in unfiltered_output:
                list_of_needed_interfaces_unfilted.append(unfiltered_output)
        for new_items in list_of_needed_interfaces_unfilted:
            split_strings_into_smaller_strings = new_items.split(" ")
            list_without_nothing = [x for x in split_strings_into_smaller_strings if x]
            list_of_unsorted_interfaces_filtered.append(list_without_nothing)

        for lists in list_of_unsorted_interfaces_filtered:
            if lists[0] == "Gig":
                dict_interfacetype_interfacenumber.update({lists[1]:lists[0]})
            else:
                dict_interfacetype_interfacenumber.update({lists[2]:lists[1]})
            
    except Exception as error:
        print(error)
        input("")
    return dict_interfacetype_interfacenumber 

####################################################################################################################
####################################################################################################################

def connect_to_device(ip_of_device, username_and_password):    
    input_username = username_and_password[0]
    input_password = username_and_password[1]
    try:
        connection_device = paramiko.SSHClient()
        connection_device.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connection_device.connect(ip_of_device, port=22, username=input_username, password=input_password)

    except Exception as error:
        print(error)
        input("")

    return connection_device

####################################################################################################################
####################################################################################################################

def get_interface_ap_info(interfaces_dict, ip_of_device, username_and_password):
    print("Gathering Information")
    interfaces_after_strip = []
    for key,value in interfaces_dict.items():
        if value == "Gig":
            cisco_string = "gigabitethernet {}".format(key)
            interfaces_after_strip.append(cisco_string)
        elif value == "Fas":
            cisco_string = "fastethernet {}".format(key)
            interfaces_after_strip.append(cisco_string)
        else:
            print("unknown interface type")
            input("Press any key to continue: ")

    actual_final_list = []
    final_dict_interface_and_info = {}
    try:
        for interfaces in interfaces_after_strip:
            interface_name = "show interface {}".format(interfaces)
            ssh_connection = connect_to_device(ip_of_device, username_and_password)
            (stdin, stdout, stderr) = ssh_connection.exec_command(interface_name)
            time.sleep(1)
            data_from_device_wrong = stdout.readlines()
            if data_from_device_wrong[0] == '\r\n':
                wrong_one = data_from_device_wrong.pop(0)
                data_from_device = data_from_device_wrong
            else:
                data_from_device = data_from_device_wrong
            
            #This is defently not the best option, will look into a change later on.
            list_changed = [data_from_device[17],data_from_device[20],data_from_device[23],data_from_device[24]]
        
            final_list = []
            for new_items in list_changed:
                list_split = new_items.split(", ")
                final_list.append(list_split[0])
            interface_info_dict = {}
            for final_items in final_list:
                new_list = final_items.split()
                dic_names = (new_list[1],new_list[2])
                interface_info_dict[" ".join(dic_names)] = new_list[0]
            
            final_dict_interface_and_info[interfaces] = interface_info_dict
    except Exception as error:
        print(error)       
    return final_dict_interface_and_info

####################################################################################################################
####################################################################################################################

def get_time():
    init_datetime = datetime.datetime.now()
    current_datetime = init_datetime.strftime("%d-%m-%Y")
    return current_datetime

####################################################################################################################
####################################################################################################################

def deploy_to_file(get_interface_ap_info, current_date, device_name):
    directory_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    csv_file = (r'''{}\{}.csv''').format(directory_path, current_date)
    try:
        with open(csv_file, mode='a') as error_file:
            csv_writer = csv.writer(error_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow([" "])
            csv_writer.writerow([device_name])
            csv_writer.writerow(["Interface Name","Packet Input", "Input Errors", "Packet Output", "Output Errors"])
            for keys,values in get_interface_ap_info.items():
                packets_input = values.get("packets input")
                packets_output = values.get("packets output")
                input_errors = values.get("input errors")
                output_errors = values.get("output errors")
                csv_list = []
                csv_list.append(keys)
                csv_list.append(packets_input)
                csv_list.append(input_errors)
                csv_list.append(packets_output)
                csv_list.append(output_errors)
                csv_writer.writerow(csv_list)

            print("Exporting to file complete!")
    except Exception as error:
        print(error)
        input("")

####################################################################################################################
####################################################################################################################        
main()
