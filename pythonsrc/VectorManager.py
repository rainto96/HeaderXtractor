# -*- coding: utf-8 -*- 
import Config
import re
import os
'''
打印一个vectorList成csv文件格式，指定人工标注的tag列名，且该列放在最后
'''
def printVectorListToCSV(vectorList, outputPath, tagColName):
	if len(vectorList) == 0:
		print '向量列表为空'
		return
	
	fout = open(outputPath, 'w')
	
	keys = vectorList[0].keys()
	keys = sorted(keys)
	
	#打印元信息
	for key in keys:
		if key==tagColName:
			continue
		fout.write(str(key)+',')
	fout.write(tagColName+'\n')
	#打印向量
	for vector in vectorList:
		for key in keys:
			if key==tagColName:
				continue
			fout.write(str(vector[key])+',')
		if not vector.has_key(tagColName): vector[tagColName] = 'false'
		fout.write(str(vector[tagColName])+'\n')
	fout.close()
'''
打印一个vectorList成arff文件格式，指定人工标注的tag列名，且该列放在最后
'''
def printVectorListToARFF(vectorList, outputPath, tagColName):
	tmpCSV_Addr = Config.TMP_ADDR+r'/tmp.csv'
	printVectorListToCSV(vectorList,tmpCSV_Addr,tagColName)
	print '正在转化为arff'
	os.system(r'java -classpath "C:/Program Files (x86)/Weka-3-6/weka.jar" weka.core.converters.CSVLoader %s > %s'%(tmpCSV_Addr, outputPath))
	
	lines = open(outputPath).readlines()
	fout = open(outputPath,'w')
	for line in lines:
		if '@attribute classfication_tag' in line:
			line = '@attribute classfication_tag {true,false}\n'
		if '@attribute classification_tag' in line:
			line = '@attribute classification_tag {true,false}\n'
		fout.write(line)
	fout.close()
	print 'arff转化完毕'

def getTag(oneline):
	list = oneline.split('::line_number::')
	line = list[0].strip()
	for tag in re.findall(r'<\w+>',line):
		return tag[1:-1]

if __name__ == '__main__':
	print getTag(r'<affiliation> Georgia Institute of Technology  </affiliation>')