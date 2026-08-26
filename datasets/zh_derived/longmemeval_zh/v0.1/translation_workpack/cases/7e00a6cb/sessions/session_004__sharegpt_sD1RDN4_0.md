---
question_id: "7e00a6cb"
session_index: 4
session_id: "sharegpt_sD1RDN4_0"
timestamp: "2023/05/20 (Sat) 18:25"
is_evidence_session: false
turn_count: 4
translation_status: TODO
---
# Session 004 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
how are the usb ports enumerated on a raspberry pi running an android os?
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
在运行安卓系统的树莓派上，USB端口是如何枚举的？
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
On a Raspberry Pi running Android, the USB ports are enumerated in the same way as they are on any other computer running Android. When a device is connected to a USB port, the operating system assigns it a unique device number and assigns it a device class based on the type of device. The device number and class are used to determine how the device should be treated by the operating system and which drivers should be used to communicate with the device.

To view information about the USB devices connected to a Raspberry Pi running Android, you can use the `lsusb` command in a terminal window. This command will list the device number, device class, and manufacturer for each USB device connected to the system.

You can also use the Android Device Manager tool to view information about the USB devices connected to the Raspberry Pi. To access the Device Manager, go to the Settings app and select "About phone" or "About tablet" from the menu. Then, select the "Hardware information" or "Device information" option to view details about the USB devices connected to the system.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
在运行安卓系统的树莓派上，USB端口的枚举方式与任何其他运行安卓系统的计算机相同。当设备连接到USB端口时，操作系统会为其分配一个唯一的设备编号，并根据设备类型分配一个设备类别。设备编号和类别用于确定操作系统应如何处理该设备，以及应使用哪些驱动程序与该设备通信。

要查看连接到运行安卓系统的树莓派上的USB设备信息，您可以在终端窗口中使用`lsusb`命令。此命令将列出连接到系统的每个USB设备的设备编号、设备类别和制造商。

您还可以使用安卓设备管理器工具查看连接到树莓派的USB设备信息。要访问设备管理器，请转到“设置”应用，并从菜单中选择“关于手机”或“关于平板电脑”。然后，选择“硬件信息”或“设备信息”选项以查看连接到系统的USB设备的详细信息。
<!-- ZH_TURN_001_END -->

## Turn 002 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
I want to power off one of the ports, but how do I know which one is which?
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
我想关闭其中一个端口，但我怎么知道哪个是哪个？
<!-- ZH_TURN_002_END -->

## Turn 003 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
To determine which USB port corresponds to a particular device on a Raspberry Pi running Android, you can use the `lsusb` command in a terminal window. This command will list the device number, device class, and manufacturer for each USB device connected to the system.

You can also use the Android Device Manager tool to view information about the USB devices connected to the Raspberry Pi. To access the Device Manager, go to the Settings app and select "About phone" or "About tablet" from the menu. Then, select the "Hardware information" or "Device information" option to view details about the USB devices connected to the system.

To power off a particular USB port, you can use the `echo` command to write the value "0" to the appropriate sysfs file for that port. For example, to power off the USB port associated with device number 3, you could use the following command:
```
echo 0 > /sys/devices/platform/soc/3c980000.usb/buspower
```
Keep in mind that this will only power off the USB port and will not physically disconnect the device from the port. To physically disconnect the device, you will need to unplug it from the port.

It's also worth noting that not all Raspberry Pi models and configurations support the ability to power off individual USB ports. If you are unable to power off a particular port using the method described above, it may not be supported on your system.
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
要确定运行安卓系统的树莓派上哪个USB端口对应特定设备，您可以在终端窗口中使用`lsusb`命令。此命令将列出连接到系统的每个USB设备的设备编号、设备类别和制造商。

您还可以使用安卓设备管理器工具查看连接到树莓派的USB设备信息。要访问设备管理器，请转到“设置”应用，并从菜单中选择“关于手机”或“关于平板电脑”。然后，选择“硬件信息”或“设备信息”选项以查看连接到系统的USB设备的详细信息。

要关闭特定USB端口，您可以使用`echo`命令将值“0”写入该端口对应的sysfs文件。例如，要关闭与设备编号3关联的USB端口，您可以使用以下命令：
```
echo 0 > /sys/devices/platform/soc/3c980000.usb/buspower
```
请注意，这只会关闭USB端口，不会物理断开设备与端口的连接。要物理断开设备，您需要将其从端口拔出。

还值得注意的是，并非所有树莓派型号和配置都支持关闭单个USB端口的功能。如果您使用上述方法无法关闭特定端口，则您的系统可能不支持此功能。
<!-- ZH_TURN_003_END -->
