---
layout: single
permalink: /machines/besca/
title: "Besca"
excerpt: "BSC & Bee"
header:
  overlay_image: /assets/images/besca2.jpg
  image: /assets/images/BescaRoast.jpg
  teaser: assets/images/BescaRoast-supporter.jpg
---

<img class="tab-image" src="{{ site.baseurl }}/assets/images/supporter-badge.png" width="150px">

* __Producer:__ [Besca](https://www.bescaroasters.com){:target="_blank"}, Turkey
* __Machine:__ all Shop and Industrial BSC Roasters as well as the Bee sample roasters
* __Connection:__ MODBUS TCP via the network (BSC automatic); MODBUS RTU via USB (BSC manual & Bee)
* __Features:__ 
  - logging of environmental temperature (ET), bean temperature (BT) and related rate-of-rise curves
  - slider control of fan speed, burner level and drum speed (only BSC automatic)
  - control buttons to operate the drum, cooler, and mixer (only BSC automatic)

 
**Watch out!** 
for manual machines produced after 15.09.2019, those with the touch screen, the Artisan machine setup _"Besca BSC manual v2"_ included in Artisan v2.1 and later should be used. For all other manual machines the _"Besca BSC manual v1"_ (or _"Besca BSC manual"_ in Artisan v2.0 and earlier)
{: .notice--primary}


**Watch out!**
The communication via MODBUS RTU requires to install a [serial driver](/modbus_serial/).
{: .notice--primary}