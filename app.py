import cathy
from flask import Flask, render_template, request, redirect
import os, re
from sys import argv

cafpath = ""
app = Flask(__name__)

disklist = None
lastreverse = True
currentcat = None
lastlabel = None
watch_ids = {}
lastwatch = {}
childs = []
wcdfile = ""

def findPngs(elm,fil):
	print("findpNGS")
	if not os.path.isfile(os.path.join(cafpath,fil)):
		return []
	with open(os.path.join(cafpath,fil),"r") as fp:
		watched = [x for x in set(fp.read().split('\n')) if len(x)>0]
	pngs = {}
	for el in elm:
		if '.png' in el[3]:
			#print(el[3])
			mtch = re.match("(\d+)\.png",el[3])
			watch_id = ""
			try:
				watch_id = mtch.group(1)
			except Exception:
				pass
			if watch_id != "":
				key = int(el[2])
				if watch_id in watched:
					pngs.update({key:(1,watch_id)})
				else:
					pngs.update({key:(0,watch_id)})
		elif '.jpg' in el[3]:
			jpgname = el[3].replace('.jpg','')
			watch_id = currentcat.parentof(el[3])
			#print("wid:",watch_id,jpgname)
			if watch_id == el[3].replace('.jpg',''):
				print("JPG Match:",watch_id)
				key = int(el[2])
				if watch_id in watched:
					pngs.update({key:(1,watch_id)})
				else:
					pngs.update({key:(0,watch_id)})

	return pngs

def myZip(inchilds,ids):
	childs = []
	for child in inchilds:
		value=(-1,"")
		if child[2] != "": # is a dir, check if it contains a malid png
			key = int(child[2])
			value = ids.get(key,(-1,""))
		childs.append((child[0],child[1],child[2],value[0]))
	return childs

def saveWatchIDs(fil):
	# protect from writing empty list after restart
	if len(watch_ids) < 1:
		return

	if not os.path.isfile(fil):
		return []
	ids = []
	for key in watch_ids:
		val = watch_ids[key]
		if val[0]:
			ids.append(val[1])
	ids.sort()
	print('\n'.join([str(x) for x in ids]))
	with open(fil,"w") as fp:
		fp.write('\n'.join([str(x) for x in ids]))

def mySort(list,keyname,tdict):
	# mysort takes the url sort parameter in keyname and uses tdict to get the key number
	global lastreverse
	if keyname == None:
		lastreverse = True
		return sorted(list,key=lambda x: x[0], reverse=False)
	keyno = tdict[keyname]
	lastreverse = not lastreverse
	return sorted(list,key=lambda x: x[keyno], reverse=lastreverse)

def update_watch_ids(childs,watchboxes):
	for child in childs:
		if child[2] != "":
			tid = int(child[2])
			try:
				malid = watch_ids[tid][1]
				if str(tid) in watchboxes:
					watch_ids.update({tid:(1,malid)})
					print("Add:",tid)
				else:
					watch_ids.update({tid:(0,malid)})
					print("Remove:",tid)
			except Exception:
				pass #apparently this child doesn't have a checkbox


@app.route("/",methods=["GET","POST"])
def index():
	global disklist,lastreverse,wcdfile, watch_ids, childs
	
	if request.method == "POST":
		watchboxes  =  request.form.getlist('watch')
		update_watch_ids(childs,watchboxes)

	referrer = request.referrer
	#print(referrer)
	if referrer and wcdfile.replace(".wch","") in referrer and len(watch_ids) > 0:
		print("Savin watch IDs")
		saveWatchIDs(os.path.join(cafpath,wcdfile))
		watch_ids = []
	

	sort = request.args.get('sort')
	if disklist == None:
		disklist = []
		cafList = [x.replace(".caf","") for x in cathy.makeCafList(cafpath)]
		for fil in cafList:
			cat = cathy.CathyCat.fast_from_file(os.path.join(cafpath,fil+'.caf'))
			free = int(cat.freesize/1000)
			used = int(int(cat.info[0][2])/1000/1000/1000)
			total = round(float(free+used)/500)*.5
			disklist.append((fil,used,free,total,cat.archive))
		disklist = mySort(disklist,'name',{ 'name':0, 'used':1, 'free':2, 'total':3 })
	else:
		disklist = mySort(disklist,sort,{ 'name':0, 'used':1, 'free':2, 'total':3 })

	return render_template('index.html', title='DISKS', files=[(x[0],'{0:,}'.format(x[1]),'{0:,}'.format(x[2]),'{0:,.1f}'.format(x[3]), x[4]) for x in disklist])


@app.route("/browse/<path>/<dir_id>",methods=["GET","POST"])
def browse(path="",dir_id="0"):	
	global currentcat, lastlabel, watch_ids, childs, wcdfile

	if request.method == "POST":
		watchboxes  =  request.form.getlist('watch')
		update_watch_ids(childs,watchboxes)
		#print(watchboxes)

	sort = request.args.get('sort')
	cid = int(dir_id)
	if path != lastlabel:
		print("reading file..")
		caffile = os.path.join(cafpath,path+".caf")
		currentcat = cathy.CathyCat.from_file(caffile)
		lastlabel = path
		watch_ids = {}
	if cid > 0:
		dirname = currentcat.volume + ' - ' + currentcat.elm[currentcat.lookup_dir_id(cid)][3]
	else:
		dirname = currentcat.volume
	if cid != 0:
		pdir = str(currentcat.elm[currentcat.lookup_dir_id(cid)][2])
	else:
		pdir = "root"

	childs = mySort(currentcat.getChildren(cid) ,sort,{ 'name':0, 'size':1})

	wcdfile = path+".wch"
	if os.path.isfile(os.path.join(cafpath,wcdfile)):
		if len(watch_ids) ==  0:
			watch_ids = findPngs(currentcat.elm,wcdfile)
		childs = myZip(childs,watch_ids)
		return render_template('wbrowse.html', title=path, dirname=dirname, pdir=pdir, files=[(x[0],'{0:,.0f}'.format(int(x[1])/1000),x[2],x[3]) for x in childs])

	else:
		wcdfile = ""
		return render_template('browse.html', title=path, dirname=dirname, pdir=pdir, files=[(x[0],'{0:,.0f}'.format(int(x[1])/1000),x[2]) for x in childs])


@app.route("/disksearch/<path>", methods=["GET", "POST"])
@app.route("/search", methods=["GET", "POST"])
def search(path=""):
	if path != "":
		tpath = os.path.join(cafpath,path+'.caf')
	else:
		tpath = cafpath
	if request.method == "POST":
		req = request.form
		if request.form.get("archive"):
			archive = True
		else:
			archive = False

		response = cathy.searchFor(tpath,req['search'],archive)
		return render_template('results.html', title="results", search=req['search'], results=[(x[0],'{0:,}'.format(int(x[1]/1000))) for x in response])

	return redirect('/')


def main():
	app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
	if len(argv) != 2:
		exit("Missing path to caf files!")
	cafpath = argv[1]
	main()

