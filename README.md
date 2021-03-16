# Cathy-python
Cross-platform python implementation of Robert Vasicek's Win-only popular Cathy disk catalog tool. Mainly intended on providing osx and linux support, since the original already works for Windows, but Windows is also supported. No GUI, mainly intended for simple cli search of existing .caf files and also automatic scanning of (backup) disks. The code should work for python 2 as well as 3.

The cathy.py file has to be in the directory where the .caf files are located. Generated .caf files are put in the same directory as the python file.

Usage:

<b>python cathy.py search <i>keyword(s)</i></b>
  
  to search for a specific term in all caf files. Keyword(s) can be different keywords separated by spaces, but then quotes are necessary
  (i.e. python cathy.py search "my photos")
  
<b>python cathy.py scan <i>path</i></b>
  
  scans the directory tree from #path# and generates a Cathy compatible file with the volume label name in the cathy.py dir. For windows <i>path</i> should be the drive letter (i.e. 'f:'), for linux and osx it is best to use the full mounted path (i.e. /Volumes/NewDisk). Warning: Existing caf files are silently overwritten!
  
<b>python cathy.py scanarchive <i>path</i></b>
  
  same as scan, but sets the archive bit. I'm not sure what the original Cathy implementation for the archive bit is,
  but in this python version archive disks are skipped by search

<b>python cathy.py usage</b>

  provides a list of all cataloged disks (caf files) with free/used/total space.
