/*******************************************************************************
 * Copy this file to td_secrets.h (gitignored) and fill in your network.
 ******************************************************************************/
#ifndef TD_SECRETS_H
#define TD_SECRETS_H

#define TD_WIFI_SSID       "your-2.4GHz-ssid" // max 32 bytes; the SiWx917 joins 2.4 GHz here
#define TD_WIFI_PASSPHRASE "your-passphrase"  // WPA2-PSK, 8-63 characters
#define TD_BROKER_IP       "192.168.1.50"     // laptop running Mosquitto, IPv4 dotted form

#endif // TD_SECRETS_H
