# Cathy-python
Cross-platform python implementation of Robert Vasicek's Win-only popular Cathy disk catalog tool (http://rva.mtg.sk/). Mainly intended for providing osx and linux support, since the original already works for Windows, but Windows is also supported. No GUI, mainly intended for simple cli search of existing .caf files and also automatic scanning of (backup) disks. The code should work for python 2 as well as 3.

For CLI operation only the cathy.py file is needed. The other stuff is for the Flask browser GUI version.
The cathy.py file has to be in the directory where the .caf files are located. Generated .caf files are put in the same directory as the python file. To avoid a lot of troublesome dependencies some infoz are gathered via shell commands. In some configurations this might not work at all and it might stop working with new os updates.

Usage:

<b>python cathy.py search <i>keyword(s)</i></b>
  
  to search for a specific term in all caf files. Keyword(s) can be multiple keywords separated by spaces, but then quotes are necessary
  (i.e. python cathy.py search "my photos"). Search only shows match if a filename contains all the keywords (logical AND).
  
<b>python cathy.py scan <i>path</i></b>
  
  scans the directory tree from <i>path</i> and generates a Cathy compatible file with the volume label name in the cathy.py dir (not sure what happens if the disk has no label). For windows <i>path</i> should be the drive letter (i.e. 'f:'), for linux and osx it is best to use the full mounted path (i.e. /Volumes/NewDisk or /media/usb). Warning: Existing caf files are silently overwritten!
  
<b>python cathy.py scanarchive <i>path</i></b>
  
  same as scan, but sets the archive flag. I'm not sure what the original Cathy implementation for the archive flag is,
  but in this python version archive disks are skipped by search

<b>python cathy.py usage</b>

  provides a list of all cataloged disks (caf files) with their free/used/total space.

<b>Browser GUI based on Flask</b>

A first Python Flask browser implementation is now also provided. You'll need flask. Do 'pip install flask'

Then run the server with 'python3 app.py <i>path-to-caf-files</i>'

With your browser go to 'localhost:5000' and browse through your offline disks (caf files) and directories and perform a search.
Scan is not implemented in the browser version, you'll have to scan disks using CLI.
