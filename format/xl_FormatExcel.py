# Copyright(c) 2016, David Mans, Konrad Sobon
# @arch_laboratory, http://archi-lab.net, http://neoarchaic.net

import clr
import sys
import System
from System import Array
from System.Collections.Generic import *

clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel
System.Threading.Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo("en-US")
from System.Runtime.InteropServices import Marshal

pyt_path = r'C:\Program Files (x86)\IronPython 2.7\Lib'
sys.path.append(pyt_path)

import os
appDataPath = os.getenv('APPDATA')
dynPath = appDataPath + r"\Dynamo\0.9"
if dynPath not in sys.path:
	sys.path.Add(dynPath)
	
bbPath = appDataPath + r"\Dynamo\0.9\packages\Bumblebee\extra"
if bbPath not in sys.path:
	try:
		sys.path.Add(bbPath)
		import bumblebee as bb
	except:
		import xml.etree.ElementTree as et
		root = et.parse(dynPath + "\DynamoSettings.xml").getroot()
		for child in root:
			if child.tag == "CustomPackageFolders":
				for path in child:
					if path not in sys.path:
						sys.path.Add(path)
		import bumblebee as bb

#The inputs to this node will be stored as a list in the IN variable.
dataEnteringNode = IN

filePath = IN[0]
runMe = IN[1]
styles = IN[2]

def StyleData(ws, gs, cellRange):
	# get range
	if ":" in cellRange:
		origin = ws.Cells(bb.xlRange(cellRange)[1], bb.xlRange(cellRange)[0])
		extent = ws.Cells(bb.xlRange(cellRange)[3], bb.xlRange(cellRange)[2])
		rng = ws.Range[origin, extent]
	else:
		# this is a named cell range
		rng = ws.Range(cellRange)
	# format cell fill style
	if gs.fillStyle != None:
		fs = gs.fillStyle
		if fs.patternType != None:
			rng.Interior.Pattern = fs.PatternType()
		if fs.backgroundColor != None:
			rng.Interior.Color = fs.BackgroundColor()
		if fs.patternColor != None:
			rng.Interior.PatternColor = fs.PatternColor()
	# format cell text style
	if gs.textStyle != None:
		ts = gs.textStyle
		if ts.name != None:
			rng.Font.Name = ts.Name()
		if ts.size != None:
			rng.Font.Size = ts.Size()
		if ts.color != None:
			rng.Font.Color = ts.Color()
		if ts.horizontalAlign != None:
			rng.HorizontalAlignment = ts.HorizontalAlign()
		if ts.verticalAlign != None:
			rng.VerticalAlignment = ts.VerticalAlign()
		if ts.bold != None:
			rng.Font.Bold = ts.Bold()
		if ts.italic != None:
			rng.Font.Italic = ts.Italic()
		if ts.underline != None:
			rng.Font.Underline = ts.Underline()
		if ts.strikethrough != None:
			rng.Font.Strikethrough = ts.Strikethrough()
	# format cell border style
	if gs.borderStyle != None:
		bs = gs.borderStyle
		if bs.lineType != None:
			rng.Borders.LineStyle = bs.LineType()
		if bs.weight != None:
			rng.Borders.Weight = bs.Weight()
		if bs.color != None:
			rng.Borders.Color = bs.Color()

	return ws

def SetUp(xlApp):
	# supress updates and warning pop ups
	xlApp.Visible = False
	xlApp.DisplayAlerts = False
	xlApp.ScreenUpdating = False
	return xlApp

def ExitExcel(filePath, xlApp, wb, ws):
	def CleanUp(_list):
		if isinstance(_list, list):
			for i in _list:
				Marshal.ReleaseComObject(i)
		else:
			Marshal.ReleaseComObject(_list)
		return None
	
	wb.SaveAs(unicode(filePath))
	xlApp.ActiveWorkbook.Close(False)
	xlApp.ScreenUpdating = True
	CleanUp([ws,wb,xlApp])
	return None

def LiveStream():
	try:
		xlApp = Marshal.GetActiveObject("Excel.Application")
		xlApp.Visible = True
		xlApp.DisplayAlerts = False
		return xlApp
	except:
		return None

def Flatten(*args):
    for x in args:
        if hasattr(x, '__iter__'):
            for y in Flatten(*x):
                yield y
        else:
            yield x

# flatten Styles list if its a nested list
if isinstance(styles, list):
	if any(isinstance(x, list) for x in styles):
		styles = list(Flatten(styles))

if runMe:
	try:
		errorReport = None
		if filePath == None:
			# run excel in a live mode
			xlApp = LiveStream()
			# if excel is running and data is being written to single sheet
			if not isinstance(styles, list):
				wb = xlApp.ActiveWorkbook
				try:
					if styles.sheetName == None:
						ws = xlApp.ActiveSheet
					else:
						ws = xlApp.Sheets(styles.SheetName())
				except:
					pass
				StyleData(ws, styles.GraphicStyle(), styles.CellRange())
			# if excel is running and data is being written to multiple sheets
			else:
				wb = xlApp.ActiveWorkbook
				for i in styles:
					ws = xlApp.Sheets(i.SheetName())
					StyleData(ws , i.GraphicStyle(), i.CellRange())
		else:
			try:
				xlApp = SetUp(Excel.ApplicationClass())
				# if excel is closed and data is being written to single sheet
				if not isinstance(styles, list):
					xlApp.Workbooks.open(unicode(filePath))
					wb = xlApp.ActiveWorkbook
					ws = xlApp.Sheets(styles.SheetName())
					StyleData(ws, styles.GraphicStyle(), styles.CellRange())
					ExitExcel(filePath, xlApp, wb, ws)
				# if excel is closed and data is being written to multiple sheets
				else:
					xlApp.Workbooks.open(unicode(filePath))
					wb = xlApp.ActiveWorkbook
					for i in styles:
						ws = xlApp.Sheets(i.SheetName())
						StyleData(ws , i.GraphicStyle(), i.CellRange())
					ExitExcel(filePath, xlApp, wb, ws)
			except:
				xlApp.Quit()
				Marshal.ReleaseComObject(xlApp)
	except:
			# if error accurs anywhere in the process catch it
			import traceback
			errorReport = traceback.format_exc()
else:
	errorReport = "Run Me is set to False. Please set \nto True if you wish to write data \nto Excel."

if errorReport == None:
	OUT = "Success!"
else:
	OUT = errorReport
