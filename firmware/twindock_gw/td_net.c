/*******************************************************************************
 * Step A: Wi-Fi join, MQTT connection and the retained twin/gateway/hello.
 *
 * SDK calls used (all confirmed in WiSeConnect 4.1.1 headers):
 *   sl_net_init / sl_net_get_profile / sl_net_set_profile / sl_net_set_credential /
 *   sl_net_up                                 (service/network_manager/inc/sl_net.h)
 *   sl_net_inet_addr                          (service/network_manager/inc/sl_net.h)
 *   sl_mqtt_client_init / _connect_v2 / _disconnect / _publish / _subscribe
 *                                             (service/mqtt/inc/sl_mqtt_client.h)
 ******************************************************************************/
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "cmsis_os2.h"
#include "sl_mqtt_client.h"
#include "sl_net.h"
#include "sl_net_wifi_types.h"
#include "sl_wifi.h"

#include "td_app.h"

_Static_assert(sizeof(TD_WIFI_SSID) - 1 <= SL_WIFI_MAX_SSID_IE_OCTETS, "TD_WIFI_SSID is longer than 32 bytes");
_Static_assert(sizeof(TD_WIFI_PASSPHRASE) - 1 >= 8 && sizeof(TD_WIFI_PASSPHRASE) - 1 <= 63,
               "WPA2 passphrase must be 8-63 characters");

/* NWP boot configuration, unchanged from the WiSeConnect embedded MQTT client
 * example: station mode, Wi-Fi only (BLE comes with Step E), DHCP client, and
 * SL_SI91X_EXT_EMB_MQTT_ENABLE so the network processor runs the MQTT client. */
static const sl_wifi_device_configuration_t td_wifi_config = {
  .boot_option = LOAD_NWP_FW,
  .mac_address = NULL,
  .band        = SL_SI91X_WIFI_BAND_2_4GHZ,
  .boot_config = { .oper_mode              = SL_SI91X_CLIENT_MODE,
                   .coex_mode              = SL_SI91X_WLAN_ONLY_MODE,
                   .feature_bit_map        = (SL_WIFI_FEAT_SECURITY_PSK | SL_WIFI_FEAT_AGGREGATION),
                   .tcp_ip_feature_bit_map = (SL_SI91X_TCP_IP_FEAT_DHCPV4_CLIENT | SL_SI91X_TCP_IP_FEAT_DNS_CLIENT
                                              | SL_SI91X_TCP_IP_FEAT_SSL | SL_SI91X_TCP_IP_FEAT_EXTENSION_VALID),
                   .custom_feature_bit_map     = (SL_WIFI_SYSTEM_CUSTOM_FEAT_EXTENSION_VALID),
                   .ext_custom_feature_bit_map = (SL_SI91X_EXT_FEAT_SSL_VERSIONS_SUPPORT | SL_SI91X_EXT_FEAT_XTAL_CLK
                                                  | SL_SI91X_EXT_FEAT_UART_SEL_FOR_DEBUG_PRINTS | MEMORY_CONFIG
#ifdef SLI_SI917
                                                  | SL_SI91X_EXT_FEAT_FRONT_END_SWITCH_PINS_ULP_GPIO_4_5_0
#endif
                                                  ),
                   .bt_feature_bit_map = 0,
                   .ext_tcp_ip_feature_bit_map =
                     (SL_SI91X_EXT_TCP_IP_WINDOW_SCALING | SL_SI91X_EXT_TCP_IP_TOTAL_SELECTS(10)
                      | SL_SI91X_EXT_TCP_IP_FEAT_SSL_THREE_SOCKETS | SL_SI91X_EXT_TCP_IP_FEAT_SSL_MEMORY_CLOUD
                      | SL_SI91X_EXT_EMB_MQTT_ENABLE),
                   .ble_feature_bit_map     = 0,
                   .ble_ext_feature_bit_map = 0,
                   .config_feature_bit_map  = 0 },
  .ta_pool         = { .tx_ratio_in_buffer_pool = 0, .rx_ratio_in_buffer_pool = 0, .global_ratio_in_buffer_pool = 0 },
  .efuse_data_type = SL_SI91X_EFUSE_MFG_SW_VERSION,
  .nwp_fw_image_number = SL_SI91X_NWP_FW_IMAGE_NUMBER_0
};

static sl_mqtt_client_t td_client;
static volatile bool td_mqtt_up;
static uint32_t td_msgs_sent; // app thread only
static uint32_t td_reconnects; // stays 0 until Step F adds reconnecting

/* Plain MQTT, no TLS and no credentials: the demo broker is Mosquitto on the
 * laptop with allow_anonymous (broker/mosquitto.conf). */
static sl_mqtt_broker_v2_t td_broker = {
  .port                    = TD_BROKER_PORT,
  .is_connection_encrypted = 0,
  .connect_timeout         = TD_MQTT_CONNECT_TIMEOUT_MS,
  .keep_alive_interval     = TD_MQTT_KEEPALIVE_S,
  .keep_alive_retries      = 0,
  .host_name               = NULL,
  .enable_sni              = 0,
  .sni_host_name           = NULL,
};

static sl_mqtt_client_configuration_t td_mqtt_config = {
  .is_clean_session = 1, // no state to resume; the board re-subscribes on every connect
  .client_id        = (uint8_t *)TD_MQTT_CLIENT_ID,
  .client_id_length = sizeof(TD_MQTT_CLIENT_ID) - 1,
  .client_port      = 1, // as in the SDK example
};

/* Write our SSID and passphrase into the default client profile/credential that
 * sl_net_up() uses. sl_net_init() has just filled them with the SDK placeholders
 * from config/sl_net_default_values.h, so this keeps all other defaults (WPA2,
 * DHCP, auto channel) and only replaces what is ours. */
static sl_status_t td_apply_wifi_credentials(void)
{
  sl_net_wifi_client_profile_t profile = { 0 };
  sl_status_t status = sl_net_get_profile(SL_NET_WIFI_CLIENT_INTERFACE, SL_NET_DEFAULT_WIFI_CLIENT_PROFILE_ID, &profile);
  if (status != SL_STATUS_OK) {
    return status;
  }
  memset(profile.config.ssid.value, 0, sizeof(profile.config.ssid.value));
  memcpy(profile.config.ssid.value, TD_WIFI_SSID, sizeof(TD_WIFI_SSID) - 1);
  profile.config.ssid.length = (uint8_t)(sizeof(TD_WIFI_SSID) - 1);
  status = sl_net_set_profile(SL_NET_WIFI_CLIENT_INTERFACE, SL_NET_DEFAULT_WIFI_CLIENT_PROFILE_ID, &profile);
  if (status != SL_STATUS_OK) {
    return status;
  }
  return sl_net_set_credential(SL_NET_DEFAULT_WIFI_CLIENT_CREDENTIAL_ID,
                               SL_NET_WIFI_PSK,
                               TD_WIFI_PASSPHRASE,
                               sizeof(TD_WIFI_PASSPHRASE) - 1);
}

void td_net_wifi_up(void)
{
  sl_status_t status;

  // Boots the network processor firmware. Only fails if the NWP does not start,
  // so retrying is the only useful reaction.
  while ((status = sl_net_init(SL_NET_WIFI_CLIENT_INTERFACE, &td_wifi_config, NULL, NULL)) != SL_STATUS_OK
         && status != SL_STATUS_ALREADY_INITIALIZED) {
    printf("[td] wifi: init failed 0x%" PRIx32 ", retrying\r\n", (uint32_t)status);
    osDelay(TD_BOOT_RETRY_MS);
  }

  status = td_apply_wifi_credentials();
  if (status != SL_STATUS_OK) {
    printf("[td] wifi: could not store SSID/passphrase 0x%" PRIx32 "\r\n", (uint32_t)status);
  }

  printf("[td] wifi: joining \"%s\"\r\n", TD_WIFI_SSID);
  // Associates, runs WPA2 and DHCP. Fails when the AP is out of range or the
  // passphrase is wrong; keep trying so the board comes up once the AP does.
  while ((status = sl_net_up(SL_NET_WIFI_CLIENT_INTERFACE, SL_NET_DEFAULT_WIFI_CLIENT_PROFILE_ID)) != SL_STATUS_OK) {
    printf("[td] wifi: join failed 0x%" PRIx32 ", retrying in %d s\r\n", (uint32_t)status, TD_BOOT_RETRY_MS / 1000);
    osDelay(TD_BOOT_RETRY_MS);
  }
  printf("[td] wifi: connected\r\n");
}

/* Called by the SDK on its event thread. Never publishes; only reports the
 * connection loss to the app thread. */
static void td_mqtt_event_handler(void *client, sl_mqtt_client_event_t event, void *event_data, void *context)
{
  (void)client;
  (void)context;
  switch (event) {
    case SL_MQTT_CLIENT_DISCONNECTED_EVENT: {
      td_event_t ev = { .type = TD_EV_MQTT_DOWN };
      (void)td_post_event(&ev);
      break;
    }
    case SL_MQTT_CLIENT_ERROR_EVENT:
      // Receive-side errors (payload too large, reassembly failure). The SDK reports
      // a real connection loss with SL_MQTT_CLIENT_DISCONNECTED_EVENT.
      printf("[td] mqtt: error event %d\r\n", (event_data != NULL) ? (int)*(sl_mqtt_client_error_status_t *)event_data : -1);
      break;
    default:
      break;
  }
}

void td_net_mqtt_connect(void)
{
  static bool initialised = false;
  sl_status_t status;

  if (!initialised) {
    // Registers the event handler; no network traffic yet.
    status = sl_mqtt_client_init(&td_client, td_mqtt_event_handler);
    if (status != SL_STATUS_OK) {
      printf("[td] mqtt: init failed 0x%" PRIx32 "\r\n", (uint32_t)status);
      return;
    }
    // Parses the dotted IPv4 string into the broker struct.
    status = sl_net_inet_addr(TD_BROKER_IP, &td_broker.ip.ip.v4.value);
    if (status != SL_STATUS_OK) {
      printf("[td] mqtt: TD_BROKER_IP \"%s\" is not a valid IPv4 address\r\n", TD_BROKER_IP);
      return;
    }
    td_broker.ip.type = SL_IPV4;
    initialised       = true;
  }

  for (;;) {
    printf("[td] mqtt: connecting to %s:%d as %s\r\n", TD_BROKER_IP, TD_BROKER_PORT, TD_MQTT_CLIENT_ID);
    // Synchronous connect (non-zero timeout): returns SL_STATUS_OK once CONNACK
    // arrives. No last will: the contract has no will topic; the backend detects
    // a dead board from missing status messages instead.
    status = sl_mqtt_client_connect_v2(&td_client, &td_broker, NULL, &td_mqtt_config, TD_MQTT_CONNECT_TIMEOUT_MS);
    if (status == SL_STATUS_OK) {
      td_mqtt_up = true;
      printf("[td] mqtt: connected\r\n");
      return;
    }
    printf("[td] mqtt: connect failed 0x%" PRIx32 ", retrying in %d s\r\n", (uint32_t)status, TD_BOOT_RETRY_MS / 1000);
    // A failed connect normally leaves the client DISCONNECTED; if the SDK could not
    // clean up, disconnect explicitly so the next connect is accepted.
    if (td_client.state == SL_MQTT_CLIENT_CONNECTION_FAILED) {
      (void)sl_mqtt_client_disconnect(&td_client, TD_MQTT_CONNECT_TIMEOUT_MS);
    }
    osDelay(TD_BOOT_RETRY_MS);
  }
}

bool td_net_mqtt_connected(void)
{
  return td_mqtt_up;
}

void td_net_mqtt_mark_down(void)
{
  td_mqtt_up = false;
}

sl_status_t td_net_publish(const char *topic, const char *payload, uint8_t qos, bool retained)
{
  if (!td_mqtt_up) {
    return SL_STATUS_NOT_READY;
  }
  sl_mqtt_client_message_t msg = {
    .qos_level            = (sl_mqtt_qos_t)qos,
    .packet_identifier    = 0,
    .is_retained          = retained,
    .is_duplicate_message = false,
    .topic                = (uint8_t *)topic,
    .topic_length         = (uint16_t)strlen(topic),
    .content              = (uint8_t *)payload,
    .content_length       = (uint32_t)strlen(payload),
  };
  // Synchronous publish: the SDK copies topic and payload into its own request,
  // and SL_STATUS_OK means the network processor accepted the message.
  sl_status_t status = sl_mqtt_client_publish(&td_client, &msg, TD_MQTT_PUBLISH_TIMEOUT_MS, NULL);
  if (status == SL_STATUS_OK) {
    td_msgs_sent++;
    printf("[td] pub %s %s\r\n", topic, payload);
  } else {
    printf("[td] pub FAILED 0x%" PRIx32 " %s\r\n", (uint32_t)status, topic);
  }
  return status;
}

sl_status_t td_net_subscribe(const char *topic, uint8_t qos, sl_mqtt_client_message_received_t handler)
{
  if (!td_mqtt_up) {
    return SL_STATUS_NOT_READY;
  }
  // Synchronous subscribe; handler runs on the SDK event thread for every
  // message on this topic.
  sl_status_t status = sl_mqtt_client_subscribe(&td_client,
                                                (const uint8_t *)topic,
                                                (uint16_t)strlen(topic),
                                                (sl_mqtt_qos_t)qos,
                                                TD_MQTT_SUBSCRIBE_TIMEOUT_MS,
                                                handler,
                                                NULL);
  printf("[td] sub %s -> 0x%" PRIx32 "\r\n", topic, (uint32_t)status);
  return status;
}

sl_status_t td_net_publish_hello(void)
{
  // Lists only the hardware this build handles (HARDWARE.md, "Exposed in TwinDock").
  // sensors stays empty until a sensor step exists and its part is verified.
  static const char hello[] = "{\"board\":\"" TD_BOARD "\",\"radio_board\":\"" TD_RADIO_BOARD
                              "\",\"fw_version\":\"" TD_FW_VERSION "\""
#if TD_ENABLE_STEP_D_LEDS
                              ",\"leds\":[\"LED0\",\"LED1\"]"
#else
                              ",\"leds\":[]"
#endif
#if TD_ENABLE_STEP_C_BUTTONS
                              ",\"buttons\":[\"BTN0\",\"BTN1\"]"
#else
                              ",\"buttons\":[]"
#endif
                              ",\"sensors\":[]}";
  // Retained + QoS 1: any client that subscribes later (backend restart, new
  // browser) gets the board identity immediately, and it is not lost in transit.
  return td_net_publish(TD_TOPIC_HELLO, hello, 1, true);
}

uint32_t td_net_msgs_sent(void)
{
  return td_msgs_sent;
}

uint32_t td_net_reconnects(void)
{
  return td_reconnects;
}
