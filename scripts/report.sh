"=== SYNOLOGY NAS STATUS REPORT ==="
"Generated: Wed Oct 15 07:49:23 PM CDT 2025"
""
"— SYSTEM INFO —"
Linux nas 4.4.302+ #69057 SMP Fri Jan 12 17:02:28 CST 2024 x86_64 GNU/Linux synology_geminilake_224+
""
"— STORAGE POOLS —"
""
"— VOLUMES —"
""
"— RAID STATUS —"
Personalities : [raid1] 
md2 : active raid1 sata1p5[0] sata2p5[1]
      5849795584 blocks super 1.2 [2/2] [UU]
      
md1 : active raid1 sata2p2[0] sata1p2[1]
      2097088 blocks [2/2] [UU]
      
md0 : active raid1 sata2p1[0] sata1p1[1]
      8388544 blocks [2/2] [UU]
      
unused devices: <none>
""
"— DISK HEALTH —"
Copyright (c) 2003-2023 Synology Inc. All rights reserved.

Usage: synodisk
--partition	-d DEV_PATH Partition disk -t (s)ystem/(d)ata/(a)ll 
--write_cache_set 
--help     Show the usage
--enum -t internal/ebox/cache/usb/sys Enumerate disks in internal or expansion box
--info PATH         Query the disk information. Note [PATH] is omitted for single-disk plateform
--detect_fs PATH    Detect the file system of a device
--isssd DEV_PATH    Check the disk is ssd or not
--standby DEV_PATH  Set [DEV_PATH] disk to standby 
--usbstandby DEV_PATH  Set [DEV_PATH] usb disk to standby 
--get_idle DEV_PATH Get [DEV_PATH] disk idle time 
--read_temp DEV_PATH Get [DEV_PATH] disk temperature 
--write_cache_get DEV_PATH Get [DEV_PATH] disk write cache status 
--is_secure_erasing Check is any disk secure erasing 
--get_location_form DEV_PATH get device location form(containerID-diskOrder) . e.g. 0-1
--smart_info_get DEV_PATH get the smart information
--m2-card-model-get DEV_PATH 	 get m.2 adapter card model
--is-perf-testing DEV_PATH_LIST 	 Check is any disk in DEV_PATH_LIST doing performance test or not,
                                	 the device is split by ','. e.g. /dev/sda,/dev/sdb.
									 the result is 0: not or 1:testing.
--check-valid DEV_PATH 	 check whether the disk is valid
--is-all-interal-drives-free-to-use 	 check whether the all internal drives are free to use
--readonly-get DEV_PATH 	 get read-only mode of disk
--readonly-set DEV_PATH RO 	 set the disk to enable/disable read-only
--check -p PATH1,PATH2,... [-u] [-m mode] [-c] [-s size] [-r LOWERBOUND,UPPERBOUND]]
       -u  Show details of correct block. (Default is disable)
       -p  Set the location(s) of the target devices.
       -m  Set the operation mode of the checking. The argument can be: 
             'seq': Sequential writing mode. 
             'jump' Jump writing mode. 
       -c  Do checksum after writing. (Default is disable)
       -s  Set the data block size in bytes based on the format [digital][unit]
           where [digitial] is a integer and [unit] can be 'K','M' or 'G' 
           representing kilo, meter and giga bytes. 
           If the unit of the value is not assigned, 
           the default unit is 'k'.
       -r  Set the check range. The arguments LOWERBOUND and UPPERBOUND 
           are also represented as [digital][unit]. (Default unit is 'k')
           The default values of LOWERBOUND and UPPERBOUND are 0 and maximum disk size.
           Note that LOWERBOUND must always smaller than UPPERBOUND.
--enum-path LOC1,LOC2,... 	Enumerate disks' path 
           LOC can be internal, ebox, cache, usb or sys 
""
"— SHARED FOLDERS —"
total 0
drwxrwxrwx+ 1 admin     users   0 Feb 24  2024 admin
drwxrwxrwx+ 1 root      root   68 Oct 14 11:35 @eaDir
drwxrwxrwx+ 1 goldman   users 206 Jun  4  2024 goldman
drwxrwxrwx+ 1 nas-admin users  12 Feb 26  2024 nas-admin
"Share info unavailable"
""
"— KEY SERVICES —"
""
"— USER ACCOUNTS —"
""
"— NETWORK —"
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: sit0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN group default qlen 1
    link/sit 0.0.0.0 brd 0.0.0.0
3: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 90:09:d0:56:61:97 brd ff:ff:ff:ff:ff:ff
    inet 10.42.100.100/24 brd 10.42.100.255 scope global eth0
       valid_lft forever preferred_lft forever
4: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 90:09:d0:56:61:98 brd ff:ff:ff:ff:ff:ff
    inet 10.42.150.100/24 brd 10.42.150.255 scope global eth1
       valid_lft forever preferred_lft forever
5: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default qlen 1000
    link/ether 02:42:23:08:d2:93 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
""
default via 10.42.100.1 dev eth0  src 10.42.100.100 
10.42.100.0/24 dev eth0  proto kernel  scope link  src 10.42.100.100 
10.42.150.0/24 dev eth1  proto kernel  scope link  src 10.42.150.100 
172.17.0.0/16 dev docker0  proto kernel  scope link  src 172.17.0.1 linkdown 
""
"— DOCKER STATUS —"
""
"— DOCKER COMPOSE —"
""
"=== END REPORT ==="
