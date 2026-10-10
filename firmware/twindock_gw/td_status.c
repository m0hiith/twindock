/*******************************************************************************
 * Step B: twin/gateway/status every 5 s with values read from the SDK.
 *
 * Every optional field is included only when the SDK returned it successfully;
 * nothing is defaulted or estimated (CLAUDE.md, "The board is never faked").
 *
 * SDK calls used (confirmed in WiSeConnect 4.1.1 headers):
 *   sl_wifi_get_signal_strength, sl_wifi_is_interface_up   (protocol/wifi/inc/sl_wifi.h)
 *   sl_net_get_ip_address                                  (service/network_manager/inc/sl_net.h)
 *   osKernelGetTickCount, osKernelGetTickFreq              (cmsis_os2.h)
 *
 * Not sent yet: "buffered" and "replay" (Step F, offline buffer).
 ******************************************************************************/
#include "td_app.h"

#if TD_ENABLE_STEP_B_STATUS

#include <inttypes.h>
#include <stdarg.h>
#include <stdio.h>

#include "cmsis_os2.h"
#include "sl_net.h"
#include "sl_wifi.h"

// sl_net_get_ip_address() is synchronous only; 1 s is plenty for a local query
// to the network processor and keeps the status period accurate.
#define TD_IP_QUERY_TIMEOUT_MS 1000

// Status payload: longest realistic message is ~190 bytes.
#define TD_STATUS_BUF 256

/* Append printf-style text to buf at *len, never past cap. Returns false when the
 * result would be truncated, so a cut-off JSON message is never published. */
__attribute__((format(printf, 4, 5))) static bool td_append(char *buf, size_t cap, size_t *len, const char *fmt, ...)
{
  va_list ap;
  va_start(ap, fmt);
  int n = vsnprintf(buf + *len, cap - *len, fmt, ap);
  va_end(ap);
  if (n < 0 || (size_t)n >= cap - *len) {
    return false;
  }
  *len += (size_t)n;
  return true;
}

void td_status_publish(void)
{
  static char buf[TD_STATUS_BUF]; // app thread only; static keeps it off the stack
  size_t len     = 0;
  bool ok        = true;
  uint32_t ts_ms = td_now_ms();

  // Uptime from the RTOS tick, the same clock as ts_ms.
  uint32_t uptime_s = osKernelGetTickCount() / osKernelGetTickFreq();

  ok = ok && td_append(buf, sizeof(buf), &len, "{\"ts_ms\":%" PRIu32 ",\"uptime_s\":%" PRIu32, ts_ms, uptime_s);

  // RSSI: average of the last four beacons from the associated AP, in dBm
  // (negative). The call fails when the client interface is down; then omit it.
  int32_t rssi = 0;
  if (sl_wifi_get_signal_strength(SL_WIFI_CLIENT_INTERFACE, &rssi) == SL_STATUS_OK && rssi >= -127 && rssi <= 0) {
    ok = ok && td_append(buf, sizeof(buf), &len, ",\"wifi_rssi_dbm\":%" PRId32, rssi);
  }

  // The SDK's own record of whether the station interface is up (associated).
  bool wifi_up = sl_wifi_is_interface_up(SL_WIFI_CLIENT_INTERFACE);
  ok           = ok && td_append(buf, sizeof(buf), &len, ",\"wifi_connected\":%s", wifi_up ? "true" : "false");

  // IPv4 address leased by DHCP.
  sl_net_ip_address_t ip = { 0 };
  if (wifi_up && sl_net_get_ip_address(SL_NET_WIFI_CLIENT_INTERFACE, &ip, TD_IP_QUERY_TIMEOUT_MS) == SL_STATUS_OK
      && ip.type == SL_IPV4 && ip.v4.ip_address.value != 0) {
    const uint8_t *b = ip.v4.ip_address.bytes;
    ok = ok && td_append(buf, sizeof(buf), &len, ",\"ip\":\"%u.%u.%u.%u\"", b[0], b[1], b[2], b[3]);
  }

  // msgs_sent counts publishes accepted before this one; reconnects is 0 until
  // Step F adds reconnecting after a drop.
  ok = ok
       && td_append(buf,
                    sizeof(buf),
                    &len,
                    ",\"fw_version\":\"%s\",\"msgs_sent\":%" PRIu32 ",\"reconnects\":%" PRIu32 "}",
                    TD_FW_VERSION,
                    td_net_msgs_sent(),
                    td_net_reconnects());

  if (!ok) {
    printf("[td] status: payload too long, not sent\r\n");
    return;
  }
  // QoS 0: a lost status is replaced by the next one 5 s later.
  (void)td_net_publish(TD_TOPIC_STATUS, buf, 0, false);
}

#endif // TD_ENABLE_STEP_B_STATUS
