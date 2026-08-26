---
question_id: "gpt4_213fd887"
session_index: 21
session_id: "sharegpt_GW2dJo3_0"
timestamp: "2023/05/24 (Wed) 21:30"
is_evidence_session: false
turn_count: 2
translation_status: TODO
---
# Session 021 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
how to configure a DNS server linux
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
Configuring a DNS server on Linux involves several steps. Here's a general outline of the process:

1. Install the DNS server software: There are several DNS server software available for Linux, such as BIND (Berkeley Internet Name Domain) and dnsmasq. You can install them using the package manager of your Linux distribution. For example, on Ubuntu, you can install BIND with the following command:
```csharp
sudo apt-get install bind9
```
2. Configure the DNS server: The main configuration file for BIND is located at `/etc/bind/named.conf`. You need to edit this file to define the domain name and other configuration settings. For example, you can define the domain name as `example.com` with the following line:
```python
zone "example.com" {
  type master;
  file "/etc/bind/db.example.com";
};
```
3. Create a zone file: The zone file contains the DNS records for the domain name. You need to create a file at the location specified in the `file` directive in the previous step. For example, you can create the file `/etc/bind/db.example.com` with the following content:
```python
$TTL 86400
@ IN SOA ns1.example.com. admin.example.com. (
  2021030901 ; Serial
  3600 ; Refresh
  1800 ; Retry
  604800 ; Expire
  86400 ; Minimum TTL
)
@ IN NS ns1.example.com.
@ IN A 192.168.0.1
```
This creates a DNS record for the domain name `example.com` with an IP address of `192.168.0.1`.

4. Start the DNS server: Once you have configured the DNS server and the zone file, you can start the DNS server. On Ubuntu, you can start BIND with the following command:
```sql
sudo systemctl start bind9
```
You can also enable the DNS server to start automatically at boot time with the following command:
```bash
sudo systemctl enable bind9
```
That's it! Your DNS server should now be up and running. You can test it by querying the DNS server with the `dig` command, like this:
```
dig example.com
```
This should return the IP address you specified in the zone file.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->
