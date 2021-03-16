# Cathy-python
Cross-platform python implementation of Robert Vasicek's Win-only popular Cathy disk catalog tool. Mainly focussed on providing osx and linux support, since the original already works for Windows. No GUI, mainly intended for simple cli search of existing .caf files and also automatic scanning of (backup) disks. It works for python 2 and 3.

The cathy.py file has to be in the directory where the .caf files are located. Generated .caf files are put in the same directory as the python file.

Usage:
python cathy.py search <keyword>
  to search for a specific term in all caf files. Searchterm can be different keywords separated by spaces, but then quotes are necessary
  i.e. python cathy.py search "my photos"
  
python cathy.py scan <path>
  scans the directory tree from <path> and generates a Cathy compatible file with the volume label name in the cathy.py dir
  
python cathy.py scanarchive <path>
  same as scan, but sets the archive bit. I'm not sure what the original Cathy implementation for the archive bit is,
  but in this python version archive disks are not included in the search, since

python cathy.py usage
  provides a list of all cataloged disks (caf files) with free/used/total space.
