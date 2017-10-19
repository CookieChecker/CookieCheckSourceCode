# CookieCheck

Here you find the source code of the CookieCheck tool.
It is a simple Python script that instruments a test using Google Chrome,
and matches the resulting cookies against a list of well-known trackers.

## Prerequisites
You must have installed an updated version Google Chrome and Python3.
We tested this software on Ubuntu.
Few Python3 packages are needed: `requests` and `websocket-client`.
You can install them using the `pip3` command-line tool.

## Usage
To test if a Web site installs cookies, run the tool specifying the target Web site as argument, like in the following example:
```
./test_site_native.py www.google.com
```

The tool provides a JSON object on the standard output, with the results of the test.
It is a dictionary containing three entries:
* `trackers_cookies` contains the cookies set by the list of trackers contained in the file `trackers_ghostery_disconnect`
* `other_cookies` contains the cookies set by other third parties
* `trackers_no_cookies` contains the trackers contacted without a cookie exchange.

