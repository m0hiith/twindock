# LinkedIn post: TwinDock

Everything for the post is in this folder:

- `twindock-platform-30s.mp4`: a plain 30 s screen recording of the running platform, with no editing. It shows the
  3D warehouse twin, the Control Room, the FL-01 wiring (breadboard, then schematic), the device kits, the monitoring
  centre and the energy page. 1920×1080, H.264.
- `forklift-route-13s.mp4`: an optional short clip of a forklift driving its route in the twin.
- `images/01…12`: screenshots of the platform and the wiring, numbered in posting order.

**How to post:** LinkedIn won't put a video and images in the same post. Pick one of these options:
1. **Video post (recommended):** upload `twindock-platform-30s.mp4` with the text below, then add the best 3–4
   images in the first comment, or
2. **Image post (carousel):** upload `images/01` to `images/12` in order, with the same text.

Before you post, check the `[ ]` placeholders: names, the @mentions and the link.

---

## Post text

Proud to share **TwinDock**, a live digital twin of a warehouse and factory that I built on the **Silicon Labs SiWx917** 🏭📡

This project came out of a collaboration between **GITAM University** and **Silicon Labs**. Silicon Labs gave our college SiWx917 development kits, and GITAM gave us the space and guidance to build something real with them. Thank you both for trusting students with real industrial hardware. 🙏

**What is TwinDock?**
On a typical site, the yard, the forklifts, the machines, the compressor and the energy meters each run on separate systems, and each one tells only part of the story. TwinDock brings all of it into one live 3D view that every screen shares.

🔹 **3D warehouse twin:** an isometric world with docks, racks, forklifts, trucks and pallets. Units follow a waypoint graph at realistic speeds and reserve lanes so they don't collide.
🔹 **Control Room:** works on a phone. An operator moves a forklift or a truck, the server checks the move, and every open screen updates in real time.
🔹 **The Silicon Labs board as the gateway:** the SiWx917 (BRD2605A) talks to the twin over Wi-Fi and MQTT. Its buttons drive the forklifts, and its RGB LED is controlled from the twin. The LED turns on in the UI only after the board confirms it.
🔹 **Factory and campus:** production lines with OEE, worker safety alerts, energy and generator failover, 32 plain-language rules and a monitoring centre.
🔹 **Device kits and wiring:** 18 sensor kits designed around Silicon Labs radios (SiWx917 for Wi-Fi, EFR32BG for BLE, EFR32MG24 for Thread), each with breadboard and schematic views. The forklift kit adds a VL53L1X time-of-flight sensor and a load cell to the board over Qwiic. Its boot sequence also fixes the I2C address clash between the VL53L1X and the on-board light sensor.

**The rule I built everything around: the board is never faked.** Every value from the real board is shown with a violet LIVE badge and its age. Everything simulated is labelled SIM. If no data has arrived, the screen says "Waiting for device". It never guesses.

**Tech stack:** C firmware on the WiSeConnect SDK · MQTT (Mosquitto) · Python FastAPI backend · React + TypeScript + Three.js frontend

**What's next:** bringing the firmware up on the physical board and adding BLE tag tracking.

Special thanks to **[@Silicon Labs]** and **[@GITAM University]**, and to **[mentor / faculty names]** for the guidance. ❤️

🔗 Code: [GitHub link]

#SiliconLabs #GITAM #IoT #DigitalTwin #SiWx917 #EmbeddedSystems #Industry40 #MQTT #WiFi6 #BluetoothLE #StudentProjects

---

## Notes on accuracy

- According to the README, firmware steps A–D build with 0 errors but **have not been run on a board yet**. That's
  why the post calls it "what's next" and doesn't claim the board has been demonstrated live. If you have since run it
  on the board, change the "What's next" line to say so.
- The video and screenshots were taken with no board connected, so the gateway shows "Waiting for device". That's
  the honest state, and the post explains it.
- The design credit to Dilum Sanjaya's "WareTrack" concept is in the README. You can add "UI inspired by Dilum
  Sanjaya's WareTrack concept" to the post if you like.
