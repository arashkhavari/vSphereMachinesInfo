#!/usr/bin/env python
from __future__ import print_function
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import argparse
import atexit
import getpass
import ssl
import pandas as pd
nameList=[]
stateList=[]
ipList=[]
hostNameList=[]
guestOSList=[]
memorySizeMBList=[]
numCPUList=[]
numEthenetCardsList=[]
numVirtualDisksList=[]
pathList=[]
def GetArgs():
   parser = argparse.ArgumentParser(
       description='Process args for retrieving all the Virtual Machines')
   parser.add_argument('-s', '--host', required=True, action='store',
                       help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store',
                       help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store',
                       help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=False, action='store',
                       help='Password to use when connecting to host')
   parser.add_argument('-d', '--dir', required=False, action='store',
                       help='Directory for output excel')
   args = parser.parse_args()
   return args
def PrintVmInfo(vm, depth=1):
   maxdepth = 10
   if hasattr(vm, 'childEntity'):
      if depth > maxdepth:
         return
      vmList = vm.childEntity
      for c in vmList:
         PrintVmInfo(c, depth+1)
      return
   if isinstance(vm, vim.VirtualApp):
      vmList = vm.vm
      for c in vmList:
         PrintVmInfo(c, depth + 1)
      return
   summary = vm.summary
   nameList.append(summary.config.name)
   if summary.runtime.powerState == 'poweredOn':
       state="ON"
   elif summary.runtime.powerState == 'poweredOff':
       state="OFF"
   stateList.append(state)
   ipList.append(summary.guest.ipAddress)
   hostNameList.append(summary.guest.hostName)
   guestOSList.append(summary.guest.guestFullName)
   memorySizeMBList.append(summary.config.memorySizeMB//1024)
   numCPUList.append(summary.config.numCpu)
   numEthenetCardsList.append(summary.config.numEthernetCards)
   numVirtualDisksList.append(summary.config.numVirtualDisks)
   pathList.append(summary.config.vmPathName)
def main():
   args = GetArgs()
   if args.password:
      password = args.password
   else:
      password = getpass.getpass(prompt='Enter password for host %s and '
                                        'user %s: ' % (args.host,args.user))
   context = None
   if hasattr(ssl, '_create_unverified_context'):
      context = ssl._create_unverified_context()
   si = SmartConnect(host=args.host,
                     user=args.user,
                     pwd=password,
                     port=int(args.port),
                     sslContext=context)
   if not si:
       print("Could not connect to the specified host using specified "
             "username and password")
       return -1
   atexit.register(Disconnect, si)
   content = si.RetrieveContent()
   for child in content.rootFolder.childEntity:
      if hasattr(child, 'vmFolder'):
         datacenter = child
         vmFolder = datacenter.vmFolder
         vmList = vmFolder.childEntity
         for vm in vmList:
            PrintVmInfo(vm)
         info = {'VM Name' : nameList, 'IP Address': ipList, 'Machine State': stateList,
                 'Host Name': hostNameList, 'OS': guestOSList,'Memory': memorySizeMBList,
                 'CPU': numCPUList, 'Ethernet': numEthenetCardsList, 'HDD': numVirtualDisksList,
                 'PATH': pathList}
         df = pd.DataFrame(info, columns = ['VM Name', 'IP Address', 'Machine State',
                                          'Host Name', 'OS', 'Memory', 'CPU',
                                          'Ethernet', 'HDD', 'PATH'])
         df.to_excel(args.dir , index=False, header=True)
   return 0
if __name__ == "__main__":
   main()

