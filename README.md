# graylog-alerts-to-icinga
Monitor graylog alerts with icinga2

This python script checks the Graylog event stream for entries. If an Altert has been triggered, a Critical message is sent to Icinga2. 
The monitoring of icinga2 is thus connected to Graylog.

Graylog is a log monitoring tool.
Icinga is a tool for machine monitoring. 


# features
- debugging
- customizations can be done via Graylog
- query search to not show alerts that should not trigger anything
- customize search time or restrict to specific machines/hosts
- fully compatible with Graylog 4
- Session authentication
- works with self-signed certificates

# How it works
- Graylog Eventstream is queried via the API (<address>:9000/api/events/search)
- In the Graylog eventstream there are usually only events that are worth watching
- By default, an alarm is triggered in icinga2 when an event is in the eventstream
- how well this plugin works depends very much on which alarms&events are configured in the Graylog


# More
[Dev-Site](https://okxo.de/show-graylog-alerts-in-icinga2/)
