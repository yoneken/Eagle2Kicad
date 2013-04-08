#!/usr/bin/python
# -*- coding: utf-8 -*-

import cgi
import html.parser
import tempfile,os
import sys,io,locale
import inspect
from xml.etree.ElementTree import ElementTree
import cgitb;cgitb.enable()

scriptDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(scriptDir+r'/Board')
sys.path.append(scriptDir+r'/Library')
sys.path.append(scriptDir+r'/Schematic')
sys.path.append(scriptDir+r'/Common')

from Board import Board
from Library import Library
#from Schematic import Schematic

# for file io encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def readmeParser():
	f = open('readme.md', 'r')
	readme = f.readlines()
	f.close

	title = readme[0][1:-1]
	contributors = ""
	notices = ""
	flag = ""
	for line in readme:
		if line.find("Contributors") >= 0:
			flag = "c"
			continue
		if line.find("NOTICE") >= 0:
			flag = "n"
			continue
		if line.find("---") >= 0:
			continue
		if flag == "c":
			if len(line.strip()) == 0:
				flag = ""
			else:
				contributors = line[2:-1].join([contributors, ', '])
		if flag == "n":
			if len(line.strip()) == 0:
				flag = ""
			else:
				notices = line.join([notices, '<br/>'])
	return title, contributors, notices

def printContentType():
	print("Content-type: text/html; charset=UTF-8\r\n")
	print("\r\n")

def printHeader(lbr='Paste target library HERE!!'):
	title, contributors, notices = readmeParser()
	print("<html>")
	print('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')
	print('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">')
	print("<head>")
	print('	<meta http-equiv="Content-Type" content="text/html charset=UTF-8"/>')
	print("	<title>" + title + "</title>")
	print("</head>")
	print("<body>")
	print("	<h1>" + title + "</h1>")
	print("	<h3>Contributors:</h3>")
	print(	contributors)
	print('	<h2><font color="red">!!!NOTICE:!!!</font></h2>')
	print(	notices)
	print('	<br/>')
	print('	<form action="./index.cgi#result" method="post">')
	print('		<label>Input: Eagle 6.+ library file (.lbr)</label><br/>')
	print('		<textarea name="lbr" cols="80" rows="20">')
	print(			lbr)
	print('		</textarea><br/>')
	print('		<input type="submit" value="Convert"><input type="reset" value="Reset"><br/>')
	print("</form>")

def printResults(libString,modString):
	print('		<label>Converted libraries will be shown at follwing textareas.</label></br>')
	print('		<br/>')
	print('		<a name="result"/>')
	print('		<label>Output: KiCad library file (.lib)</label><br/>')
	print('		<textarea name="lib" cols="80" rows="20">')
	print(			libString)
	print('		</textarea><br/><br/>')
	print('		<label>Output: KiCad module file (.mod)</label><br/>')
	print('		<textarea name="mod" cols="80" rows="20">')
	print(			modString)
	print('		</textarea><br/>')

def printFooter():
	print("</body>")
	print("</html>")

def printJson(lib, mod):
	print('{"lib":"' + lib + '", "mod":"' + mod + '"}')

def checkRefs():
	form = cgi.FieldStorage()
	lbr = form.getvalue('lbr', '')
	json = form.getvalue('json', '0')
	return lbr, json

def getRootNode(fileName):
	node = ElementTree(file=fileName)
	node = node.getroot()
	return node

def convertLbr(lbr):
	lib = ""
	mod = ""
	tmpLbr = tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', delete=False)
	tmpLib = tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', delete=False)
	tmpMod = tempfile.NamedTemporaryFile(mode='w+t', encoding='utf-8', delete=False)
	try:
		#tmpLbr = codecs.lookup(locale.getpreferredencoding())[-1](tmpLbr)
		tmpLbr.write(lbr)
		tmpLbr.close()
	except:
		lib += "Error: cannot write tempolary files."
	else:

		node = ElementTree(file=tmpLbr.name)
		node = node.getroot().find("drawing").find("library")
		
		libr = Library(node,"Eagle2Kicad")
		libr.writeLibrary(tmpLib,tmpMod)

		tmpLib.close()
		tmpMod.close()
		
		try:
			fLib = open(tmpLib.name, 'r', encoding='utf-8')
			lib = fLib.readlines()
			fLib.close()

			fMod = open(tmpMod.name, 'r', encoding='utf-8')
			mod = fMod.readlines()
			fMod.close()

		except:
			lib += "Error: cannot read converted files."

	finally:
		os.remove(tmpLbr.name)
		os.remove(tmpLib.name)
		os.remove(tmpMod.name)
		
	return "".join(lib), "".join(mod)

def main():
	lbr, json = checkRefs()
	if len(lbr)>0:
		lib, mod = convertLbr(lbr)
		if json == 1:
			printContentType()
			printJson(lib, mod)
		else:
			printContentType()
			printHeader(cgi.escape(lbr))
			printResults(cgi.escape(lib), cgi.escape(mod))
			printFooter()
	else:
		printContentType()
		printHeader()
		printFooter()

if __name__ == "__main__":
	main()
