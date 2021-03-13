#!python3
'''
attempt to build a python class to read cathy's .caf file
2017/05/31  got entrydat.cpp from Robert Vasicek rvas01@gmx.net :)
2017/06/02  first reading/struct. conversion from entrydat.cpp
2017/06/03  first complete read of a .caf
            first query functions
			
USAGE

type a full path to your catalog .cat file like :
	from os import getcwd
	pth = getcwd()
	catname = '-Downloads.caf'
	pathcatname = os.path.join(pth,catname)

create a python instance from the catalog :
	from cathy import CathyCat
	cat = CathyCat(pathcatname)

cat.pathcat		# catalogfilename in the cathy's ui
cat.date
cat.device
cat.volume 		# name in 'volume' column
cat.alias   	# name in first Cathy column
cat.volumename
cat.serial
cat.comment
cat.freesize
cat.archive
		
cat.elm will contain every element (folder name ot filename)
cat.elm[69] returns a tuple with (date, size, parent folder id, filename)
cat.info[folder id] returns a tuple with folder informations

#example
import os
from cathy import CathyCat
pth = os.getcwd()
catname = '-Downloads.caf'
pathcatname = os.path.join(pth,catname)
cat = CathyCat(pathcatname)

cat.pathcat		# catalogfilename in the cathy's ui
cat.date
cat.device
cat.volume
cat.alias
cat.volumename
cat.serial
cat.comment
cat.freesize
cat.archive


2021/03/09	All unpack formats fixed for endianness so the Python code will run on mac and linux systems
2021/03/10	removed some modifications to the original code that I didn't worked correctly (at least not for me):
			- 2 to 4 byte change in m_sPathName
			- [2:-1] truncation in catpath
			Added search functions
'''

#from __future__ import (print_function, unicode_literals, division)
#__metaclass__ = type

from __future__ import (print_function, division)
__metaclass__ = type


import time,datetime
import subprocess
import os
from os import path as ospath
from struct import calcsize, unpack, pack
from time import ctime
from binascii import b2a_hex
import shutil

from sys import platform,version_info,argv

class CathyCat() :

	ulCurrentMagic = 3500410407
	ulMagicBase =     500410407
	#ulMagicBase =     251327015
	ulModus =        1000000000
	saveVersion = 7
	sVersion = 8 # got a 7 in the .cpp file you share with me, but got an 8 in my .cat testfile genrated in cathy v2.31.3
	
	delim = b'\x00'
	
	def __init__(self, pathcatname, m_timeDate, m_strDevice, m_strVolume, m_strAlias, m_szVolumeName, m_dwSerialNumber, m_strComment, m_fFreeSize, m_sArchive, info, elm) :
		'''
		read a cathy .caf file
		and import it into a python instance
		'''

		self.pathcat = pathcatname		# catalogfilename in the cathy's ui
		self.date = m_timeDate
		self.device = m_strDevice
		self.volume = m_strVolume
		self.alias = m_strAlias
		self.volumename = m_szVolumeName
		self.serial = m_dwSerialNumber
		self.comment = m_strComment
		self.freesize = m_fFreeSize
		self.archive = m_sArchive
		self.totaldirs = 0
		
		#self.ptr_path = ptrpath # pointer from which to parse folder info
		self.info = info
		#self.ptr_files = ptr_files
		self.elm = elm

	@classmethod
	def from_file(cls, pathcatname):
		
		try : cls.buffer = open(pathcatname,'rb')
		except : return
		
		# m_sVersion - Check the magic
		ul = cls.readbuf('<L')
		#print(ul%CathyCat.ulModus)
		if ul > 0 and ul%CathyCat.ulModus == CathyCat.ulMagicBase : 
			m_sVersion= int(ul/CathyCat.ulModus)
		else :
			cls.buffer.close()
			return
		
		if m_sVersion > 2 :
			m_sVersion = cls.readbuf('h')
		
		if m_sVersion > CathyCat.sVersion :
			return
		#print("m_sVersion:",m_sVersion)
		
		# m_timeDate
		m_timeDate = ctime(cls.readbuf('<L'))
		
		# m_strDevice - Starting version 2 the device is saved
		if m_sVersion >= 2 : 
			m_strDevice = cls.readstring()
	
		# m_strVolume, m_strAlias > m_szVolumeName
		m_strVolume = cls.readstring()
		m_strAlias = cls.readstring()
	
		if len(m_strAlias) == 0 :
			m_szVolumeName = m_strVolume
		else :
			m_szVolumeName = m_strAlias
	
		# m_dwSerialNumber well, odd..
		bytesn = cls.buffer.read(4)
		rawsn = b2a_hex(bytesn).decode().upper()
		sn = ''
		while rawsn :
			chunk = rawsn[-2:]
			rawsn = rawsn[:-2]
			sn += chunk
		m_dwSerialNumber = '%s-%s'%(sn[:4],sn[4:])
	
		# m_strComment
		if m_sVersion >= 4  :
			m_strComment = cls.readstring()
		
		# m_fFreeSize - Starting version 1 the free size was saved
		if m_sVersion >= 1 : 
			m_fFreeSize = cls.readbuf('<f') # as megabytes
		else :
			m_fFreeSize = -1 # unknow
			
		# m_sArchive
		if m_sVersion >= 6 :
			m_sArchive = cls.readbuf('h')
			if m_sArchive == -1 :
				m_sArchive = 0
				
		'''
		self.pathcat = pathcatname		# catalogfilename in the cathy's ui
		self.date = m_timeDate
		self.device = m_strDevice
		self.volume = m_strVolume
		self.alias = m_strAlias
		self.volumename = m_szVolumeName
		self.serial = m_dwSerialNumber
		self.comment = m_strComment
		self.freesize = m_fFreeSize
		self.archive = m_sArchive
		
		self.ptr_path = cls.buffer.tell() # pointer from which to parse folder info
		ptrpath = cls.buffer.tell()
		'''

		# folder information : file count, total size
		m_paPaths = []
		lLen = cls.readbuf('<l')
		#print(lLen)
		tcnt = 0
		for l in range(lLen) :
			if l==0 or m_sVersion<=3 :
				m_pszName = cls.readstring()
				#print("m_pszName:",m_pszName)
			if m_sVersion >= 3 :
				m_lFiles = cls.readbuf('<l')
				m_dTotalSize = cls.readbuf('<d')
			#print(m_lFiles,m_dTotalSize)
			m_paPaths.append( (tcnt, m_lFiles,m_dTotalSize) )
			tcnt = tcnt + 1
			
		info = m_paPaths
		
		#ptr_files = cls.buffer.tell() # pointer from which to parse elements (file or folders)
		
		
		# files : date, size, parentfolderid, filename
		# if it's a folder :  date, -thisfolderid, parentfolderid, filename
		m_paFileList = []
		lLen = cls.readbuf('<l')
		#print(lLen)
		for l in range(lLen) :
			#elmdate = ctime(cls.readbuf('<L'))
			elmdate = cls.readbuf('<L')
			if m_sVersion<=6 :
				# later, won't test for now
				m_lLength = 0
			else :
				# m_lLength = cls.buffer.read(8)
				m_lLength = cls.readbuf('<q') 
			#m_sPathName = cls.readbuf('<l')  # in the .cpp I think m_sPathName wants 2 bytes but 4 works for me
			m_sPathName = cls.readbuf('H')
			m_pszName = cls.readstring()
			m_paFileList.append((elmdate,m_lLength,m_sPathName,m_pszName))
		
		elm = m_paFileList

		cls.buffer.close()

		return cls(pathcatname, m_timeDate, m_strDevice, m_strVolume, m_strAlias, m_szVolumeName, m_dwSerialNumber, m_strComment, m_fFreeSize, m_sArchive, info, elm)
		
	def write(self, pathcatname):
		
		try : self.buffer = open(pathcatname,'wb')
		except : return
		
		# m_sVersion - Check the magic
		ul = 3*CathyCat.ulModus+CathyCat.ulMagicBase
		#print(ul)

		if ul > 0 and ul%CathyCat.ulModus == CathyCat.ulMagicBase : 
			m_sVersion= int(ul/CathyCat.ulModus)
			#print(m_sVersion)


		self.writebuf('<L',ul)
		self.writebuf('h',CathyCat.saveVersion)
		self.writebuf('<L',int(time.time()))

		self.writestring(self.device)
		self.writestring(self.volume)
		self.writestring(self.alias)
	
		# m_strVolume, m_strAlias > m_szVolumeName
		#m_strVolume = cls.readstring()
		#m_strAlias = cls.readstring()
	
		#if len(m_strAlias) == 0 :
		#	m_szVolumeName = m_strVolume
		#else :
		#	m_szVolumeName = m_strAlias
	
		# m_dwSerialNumber well, odd..

		t_serial = self.serial.replace('-','')
		serial_long = int(t_serial,16)
		self.writebuf('<L',serial_long) # not sure if little endian is ok

		#bytesn = cls.buffer.read(4)
		#rawsn = b2a_hex(bytesn).decode().upper()
		#sn = ''
		#while rawsn :
		#	chunk = rawsn[-2:]
		#	rawsn = rawsn[:-2]
		#	sn += chunk
		#m_dwSerialNumber = '%s-%s'%(sn[:4],sn[4:])

	
		# m_strComment
		self.writestring(self.comment)

		#if m_sVersion >= 4  :
		#	m_strComment = cls.readstring()
		
		# m_fFreeSize - Starting version 1 the free size was saved
		self.writebuf('<f',self.freesize)
		#if m_sVersion >= 1 : 
		#	m_fFreeSize = cls.readbuf('<f') # as megabytes
		#else :
		#	m_fFreeSize = -1 # unknow
			
		# m_sArchive
		self.writebuf('h',self.archive)
		#if m_sVersion >= 6 :
		#	m_sArchive = cls.readbuf('h')
		#	if m_sArchive == -1 :
		#		m_sArchive = 0
				
		'''
		self.pathcat = pathcatname		# catalogfilename in the cathy's ui
		self.date = m_timeDate
		self.device = m_strDevice
		self.volume = m_strVolume
		self.alias = m_strAlias
		self.volumename = m_szVolumeName
		self.serial = m_dwSerialNumber
		self.comment = m_strComment
		self.freesize = m_fFreeSize
		self.archive = m_sArchive
		
		self.ptr_path = cls.buffer.tell() # pointer from which to parse folder info
		'''
		#ptrpath = self.buffer.tell()

		# folder information : file count, total size
		self.writebuf('<l',len(self.info))
		for i in range(len(self.info)):
			if i ==0:
				self.writestring("")
			#print(i,self.info[i][0],self.info[i][1])
			self.writebuf('<l',self.info[i][1])
			self.writebuf('<d',self.info[i][2])

		#m_paPaths = []
		#lLen = cls.readbuf('<l')
		#for l in range(lLen) :
		#	if l==0 or m_sVersion<=3 :
		#		m_pszName = cls.readstring()
		#		#print("m_pszName:",m_pszName,pathcatname)
		#	if m_sVersion >= 3 :
		#		m_lFiles = cls.readbuf('<l')
		#		m_dTotalSize = cls.readbuf('<d')
		#	m_paPaths.append( (m_lFiles,m_dTotalSize) )	
		#info = m_paPaths
		
		#ptr_files = cls.buffer.tell() # pointer from which to parse elements (file or folders)
		
		
		# files : date, size, parentfolderid, filename
		# if it's a folder :  date, -thisfolderid, parentfolderid, filename

		self.writebuf('<l',len(self.elm))
		for el in self.elm:
			self.writebuf('<L',el[0]) #date
			#print(el[1])
			self.writebuf('<q',el[1]) #size or folderid
			self.writebuf('H',el[2]) #parentfolderid
			self.writestring(el[3]) #filename
		'''
		m_paFileList = []
		lLen = cls.readbuf('<l')
		for l in range(lLen) :
			elmdate = ctime(cls.readbuf('<L'))
			if m_sVersion<=6 :
				# later, won't test for now
				m_lLength = 0
			else :
				# m_lLength = cls.buffer.read(8)
				m_lLength = cls.readbuf('<q') 
			#m_sPathName = cls.readbuf('<l')  # in the .cpp I think m_sPathName wants 2 bytes but 4 works for me
			m_sPathName = cls.readbuf('H')
			m_pszName = cls.readstring()
			m_paFileList.append((elmdate,m_lLength,m_sPathName,m_pszName))
		
		elm = m_paFileList
		'''

		self.buffer.close()

		#return cls(pathcatname, m_timeDate, m_strDevice, m_strVolume, m_strAlias, m_szVolumeName, m_dwSerialNumber, m_strComment, m_fFreeSize, m_sArchive, info, elm)



	def catpath(self) :
		'''
		returns an absolute path to the main directory
		handled by this .cat file
		'''
		return self.device + self.volume #[2:-1] # don't know why 

	def path(self,elmid) :
		'''
		returns the absolute path of an element
		from its id or its name
		'''
		elmid = self._checkelmid(elmid)
		if type(elmid) == list :
			print('got several answers : %s\nselected the first id.'%elmid)
			elmid = elmid[0]
		
		pths = []
		while True :
			dt,lg,pn,nm = self.elm[elmid]
			pths.append(nm)
			# print(lg,pn,nm) # -368 302 cursors
			if pn == 0 :
				pths.append(self.catpath())
				break
			else :
				for elmid,elm in enumerate(self.elm) :
					if elm[1] == -pn :
						# print('>',elm)
						nm = elm[3]
						break
				else :
					print('error in parenting..')
		pths.reverse()
		return ospath.sep.join(pths)

	def parentof(self,elmid) :
		'''
		returns the parent folder of an element,
		from its id or its name
		'''
		
		elmid = self._checkelmid(elmid)
		if type(elmid) == list :
			print('got several answers : %s\nselected the first id.'%elmid)
			elmid = elmid[0]
		
		dt,lg,pn,nm = self.elm[elmid]
		
		# a 0 parentid means it's the catalog 'root'
		if pn == 0 :
			return self.catpath()
		# parent is a folder, it's id is in the size field, negated
		for i,elm in enumerate(self.elm) :
			if elm[1] == -pn : return elm[3]

	def lookup(self,elmname) :
		'''	
		get an internal id from a file or folder name
		several answers are possible
		'''
		ids = []
		for i,elm in enumerate(self.elm) :
			if elm[3] == elmname : ids.append(i)
		return ids[0] if len(ids) == 1 else ids

	# private
	def _checkelmid(self,elmid) :
		if type(elmid) == str : elmid = self.lookup(elmid)
		return elmid
		
	# private. parser struct. fixed lengths
	@classmethod
	def readbuf(cls,fmt,nb=False) :
		if not(nb) : nb = calcsize(fmt)
		return unpack(fmt, cls.buffer.read(nb))[0]

	# private. parser struct. fixed lengths
	def writebuf(self,fmt, inp) :
		#if not(nb) : nb = calcsize(fmt)
		self.buffer.write(pack(fmt,inp))
	
	# private. parser string. arbitrary length. delimited by a 0 at its end
	@classmethod
	def readstring(cls) :
		chain = ''
		while 1 :
			chr = cls.readbuf('s')
			if chr == CathyCat.delim : break
			else : 
				try : chain += chr.decode()
				except : pass
		return chain

	def writestring(self,inp) :
		if version_info[0] == 2:
			# some hack to allow the code to run on python2
			inp = inp.decode(errors='replace')
		#print(inp.encode('utf-8',errors='replace'))
		self.buffer.write(inp.encode('utf-8',errors='replace'))
		self.buffer.write(CathyCat.delim)

	@classmethod
	def get_device(cls,start_path):
		output=subprocess.check_output(['df',start_path]).decode().split('\n')
		for line in output:
			if start_path in line:
				end = line.find(' ')
				device = line[:end]
		return device

	@classmethod
	def get_serial(cls,start_path):
		if platform == "linux" or platform == "linux2":
			device = cls.get_device(start_path)
			output=subprocess.check_output(['sudo','blkid','-o','value','-s','UUID',device]).decode().strip()
			ser = output[-8:-4]+"-"+output[-4:]
			#print("Serial:",ser+"##")
		elif platform == "darwin":
			output=subprocess.check_output(['diskutil','info',start_path]).decode()
			#print(type(output))
			start = output.find("UUID:")+7
			end = output.find('\n',start)
			ser = output[end-8:end-4]+"-"+output[end-4:end]
			#print(ser)
		elif platform == "win32":
		    pass
		return ser

	@classmethod
	def get_label(cls,start_path):
		if platform == "linux" or platform == "linux2":
			device = cls.get_device(start_path)
			output=subprocess.check_output(['sudo','blkid','-o','value','-s','LABEL',device]).decode().strip()
			ser = output
			#print("Label:",ser)
		elif platform == "darwin":
			output=subprocess.check_output(['diskutil','info',start_path]).decode()
			#print(type(output))
			start = output.find("Volume Name:")+12
			end = output.find('\n',start)
			ser = output[start:end].strip()
			#print(ser)
		elif platform == "win32":
		    pass
		return ser

	@classmethod
	def get_free_space(cls,start_path):
		if platform == "linux" or platform == "linux2":
			output=subprocess.check_output(['df']).decode().split('\n')
			for line in output:
				if start_path in line:
					#print(line)
					items = [x for x in line.split(' ') if x]
					#print(len(items))
					ser = float(items[3])
			#print(ser)
		elif platform == "darwin":
			output=subprocess.check_output(['diskutil','info',start_path]).decode()
			#print(type(output))
			start = output.find("Free Space:")
			start = output.find('(',start)+1
			end = output.find('Bytes',start)
			ser = float(output[start:end].strip())/1024
			#print(ser)
		elif platform == "win32":
			import ctypes
			free_bytes = ctypes.c_ulonglong(0)
			ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(u'c:\\'), None, None, ctypes.pointer(free_bytes))
			ser = float(free_bytes.value)/1024

		return ser/1024

	def scandir(self, dir_id,start_path):
		# the recursive function for scanning a disk
		# it is better to do the recursion yourself instead of using os.walk, 
		# because then you can build the Cathy tree more easily (filecount and dirsize)
		tsize = 0
		filecnt = 0
		for el in os.listdir(start_path):
			elem = os.path.join(start_path,el)
			if os.path.isfile(elem):
				#print("File:",elem)
				filecnt = filecnt + 1
				cursize = os.path.getsize(elem)
				tsize = tsize + cursize
				dat = os.path.getmtime(elem)
				self.elm.append((int(dat),cursize,dir_id,el))
			if os.path.isdir(elem):
				#print("Dir:",elem)
				self.totaldirs = self.totaldirs + 1
				keepdir = self.totaldirs
				dat = os.path.getmtime(elem)
				self.elm.append((int(dat),-keepdir,dir_id,el))
				(did, fcnt, tsiz) = self.scandir(keepdir,elem)
				self.info.append((keepdir,fcnt,tsiz))
				filecnt = filecnt + fcnt
				tsize = tsize + tsiz
				'''
				try:
					print(keepdir,dir_id,elem,fcnt,tsiz)
				except:
					pass
				'''
		return (dir_id,filecnt,tsize)

	@classmethod
	def scan(cls,start_path):
		# the scan function initializes the global caf parameters then calls the recursive scandir function
		pathcat = start_path		# catalogfilename in the cathy's ui
		date = int(time.time())		# caf creation date
		device = start_path			# for device now the start_path is used, for win this is prob drive letter, but for linux this will be the root dir
		volume = cls.get_label(start_path)
		alias = volume
		volumename = volume
		serial = cls.get_serial(start_path)
		comment = ""
		freesize = cls.get_free_space(start_path)
		archive = 0

		t_cat = cls(pathcat, date, device, volume, alias, volumename, serial, comment, freesize, archive, [], [])
		t_cat.info.append(t_cat.scandir(0,start_path))
		t_cat.info.sort()

		return t_cat

# functions that use CathyCat

def makeCafList(path):
	# returns list of all .caf files in path using os.walk
	lst = []
	for root,dirs,files in os.walk(path):
		for fil in files:
			if ".caf" in fil[-4:]:
				lst.append(fil)
	return(lst)

def searchFor(patt, searchterm):
	searchlist = searchterm.lower().split(' ')
	# checks all .caf files in patt for a match with alls terms in searchlist
	cafList = makeCafList(pth)
	for catname in cafList:
		pathcatname = os.path.join(pth,catname)
		cat = CathyCat.from_file(pathcatname)
		if cat.archive:
			print("Skipping",catname,"for search because of archive bit")
		else:
			print(catname)
			for i in range(len(cat.elm)):
				FOUND = True
				for term in searchlist:
					if not term in cat.elm[i][3].lower():
						FOUND = False
						break;
				if FOUND:
					print("Match:",cat.path(i)[3:])

	
if __name__ == '__main__':

	pth = os.getcwd() #path to .caf files
	if len(argv) >2:
		if "search" in argv[1]:
			searchFor(pth,argv[2])
		
		if "scan" in argv[1]:
			scanpath =argv[2]
			if scanpath[-1] == '/':
				scanpath = scanpath[:-1]
			print("Scanning...")
			cat = CathyCat.scan(scanpath)
			if "archive" in argv[1]:
				print("Setting archive bit!")
				cat.archive = 1
			savename = os.path.join(os.getcwd(),cat.volume+".caf")
			print("Saving to:",savename)
			cat.write(savename)

		if "setarchive" in argv[1]:
			setpath = os.path.join(pth,argv[2])
			cat = CathyCat.from_file(setpath)
			cat.archive = 1
			cat.write(setpath)
	else:
		print("Not enough arguments.\nUse cathy search <term> to search and 'cathy scan <path>' to scan a device.")

	#print(cat.info[0],cat2.info[0])
	
	#cat = CathyCat.from_file(os.path.join(pth,"NieuwVolume.caf"))
	#print(cat.serial)

