import csv #import the csv file reader module

#open the csv file and read using the csv module
def read_network_devicefile():
    filename = 'network_devices.csv'
    with open(filename, 'r') as file:
        content = csv.DictReader(file)
        return list(content)        #return the contents of file as a list
 
def main():
    devices = read_network_devicefile()

    i=0
    for device in devices:          #print out each device under the column named 'Device Name'
        name = device['Device Name']     
        i = i+1
        print(f"Device {i:< 3}: {name}")


#call the main function 
if __name__ == '__main__':
    main()