---
title: TwinDock
emoji: 🏭
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
short_description: Warehouse and factory digital twin (simulated plant)
---

# TwinDock: hosted demo

A browser-based digital twin of the Riverside campus (a warehouse and a two-line factory), built around a
Silicon Labs SiWx917 board. **On this hosted demo every value is simulated (SIM)**: a cause-and-effect model of the
plant runs inside the container (machines draw air and power because they run, the compressor loads because the
pressure fell, the generator starts because the grid failed). The real SiWx917 board appears only in the live demo,
where it connects over MQTT.

- `/twin`: the 3D twin. `/control`: Control Room (moves, maintenance decisions, logistics, demo beats).
- `/monitor`, `/energy`, `/fleet`, `/rules`: monitoring. `/model`: every model, equation, parameter and its source.
- The container fast-forwards 45 simulated minutes when it starts (or wakes), so the factory is already running.

Source, design notes and the decisions behind the model: see the project repository.
