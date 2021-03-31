import cathy
from flask import Flask, render_template, request, redirect
import os
from sys import argv

cafpath = ""
app = Flask(__name__)

disklist = None
lastreverse = True
currentcat = None
lastlabel = None

def mySort(list,keyname,tdict):
	# mysort takes the url sort parameter in keyname and uses tdict to get the key number
	global lastreverse
	if keyname == None:
		lastreverse = True
		return sorted(list,key=lambda x: x[0], reverse=False)
	keyno = tdict[keyname]
	lastreverse = not lastreverse
	return sorted(list,key=lambda x: x[keyno], reverse=lastreverse)

@app.route("/")
def index():
	global disklist
	global lastreverse
	sort = request.args.get('sort')
	#url = request.base_url
	#print(sort, url)
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


@app.route("/browse/<path>/<dir_id>")
def browse(path="",dir_id="0"):	
	global currentcat, lastlabel
	sort = request.args.get('sort')
	cid = int(dir_id)
	if path != lastlabel:
		print("reading file..")
		caffile = os.path.join(cafpath,path+".caf")
		currentcat = cathy.CathyCat.from_file(caffile)
		lastlabel = path
	if cid > 0:
		dirname = currentcat.volume + ' - ' + currentcat.elm[currentcat.lookup_dir_id(cid)][3]
	else:
		dirname = currentcat.volume
	if cid != 0:
		pdir = str(currentcat.elm[currentcat.lookup_dir_id(cid)][2])
	else:
		pdir = "root"

	childs = mySort(currentcat.getChildren(cid) ,sort,{ 'name':0, 'size':1})

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

