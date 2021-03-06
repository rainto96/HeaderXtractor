# -*- coding: utf-8 -*- 
import os
import Config
import sys
os.chdir(Config.WORKSPACE)
import DisjointSet
import Geometry
import Tools
import copy
import GraphicManager
import Author
import StringManager
import EmailManager
BLOCK_HEIGHT_RATIO = 0.7
class Block:
	header=''
	l=0.0
	r=0.0
	u=0.0
	d=0.0
	rectangle = Geometry.Rectangle()
	originIdx = 0
	label=''
	def __init__(self, headerContent, xposList,sizesList,ypos,originIdx):
		self.header = headerContent
		#self.l = xposList[0][0] - sizesList[0][0]
		#self.r = xposList[-1][-1] + sizesList[-1][-1]
		length = xposList[-1][-1] - xposList[0][0]
		self.l = xposList[0][0] + length / 4.0 #trick避免错误合并，以竖直方向合并为主
		self.r = xposList[-1][-1] - length / 4.0 #trick避免错误合并，以竖直方向合并为主

		averageSz = sum([float(x) for x in Tools.flatList(sizesList)])*1.0 / len(Tools.flatList(sizesList))
		self.u = ypos - averageSz * BLOCK_HEIGHT_RATIO
		self.d = ypos + averageSz * BLOCK_HEIGHT_RATIO
		self.rectangle = Geometry.Rectangle(self.l, self.r, self.u, self.d)
		self.originIdx = originIdx

	def hash(self):
		return int(self.l)*10000+int(self.u)

#合并相交的词块矩形
def unionBlockByRectangleIntersect(dsu, blockList):
	for i in range(len(blockList)):
		for j in range(i+1,len(blockList)):
			#if i == 0 and j == 1:
			#	print 'i::',blockList[i].rectangle.__dict__
			#	print 'j::',blockList[j].rectangle.__dict__
			#	print 'res::',blockList[i].rectangle.isIntersect(blockList[j].rectangle)
			if blockList[i].rectangle.isIntersect(blockList[j].rectangle):
				dsu.unite(i,j)
#返回块集合范围
def getBlockSetRange(blockSet):
	l = blockSet[0].l
	r = blockSet[0].r
	u = blockSet[0].u
	d = blockSet[0].d
	for block in blockSet:
		l = min(l, block.l)
		r = max(r, block.r)
		u = min(u, block.u)
		d = max(d, block.d)
	return l,r,u,d

#将落单的单行含有@符号的块挂到正上方的块上
def fixSingleBlockContainAt(dsu, blockSetList, idInDSU):
	for i in range(len(blockSetList)):
		l1,r1,u1,d1 = getBlockSetRange(blockSetList[i])
		if len(blockSetList[i]) == 1 and '@' in blockSetList[i][0].header:
			for j in range(len(blockSetList)):
				if i == j or len(blockSetList[j])<=1:continue
				l2,r2,u2,d2 = getBlockSetRange(blockSetList[j])
				if (l1+r1)*1.0/2 < r2 and (l1+r1)*1.0/2 > l2 and u1 - d2 <= 10 and u1 - d2>=0:
					id1 = idInDSU[blockSetList[i][0].hash()]
					id2 = idInDSU[blockSetList[j][0].hash()]
					dsu.unite(dsu.find(id1), dsu.find(id2))


#将合并后的块按块平均高度排序后输出块列表
def getBlockSetList(dsu, blockList):
	blockSet = {}
	for i in range(len(blockList)):
		setId = dsu.find(i)
		if not blockSet.has_key(setId):
			blockSet[setId] = [[],0]
		blockSet[setId][0].append(blockList[i])
		blockSet[setId][1] += (blockList[i].u + blockList[i].d)/2.0
	blockSetList = []
	for key in blockSet.keys():
		blockSet[key][1] /= len(blockSet[key][0])
		blockSetList.append(copy.deepcopy(blockSet[key]))
		#print '===================='
		#for blk in blockSet[key][0]:
		#	print blk.__dict__
		#print '===================='
	blockSetList.sort(key = lambda x:x[1])
	return [x[0] for x in blockSetList]#仅取块集合

#该函数利用并查集通过词框合并得到一个个块，最后排序输出给分类器进行分类，排序规则如下
#计算块集合的平均高度y，首先输出平均高度y较小的块，块内按y从小到大
blockSetList=[]

def BlockUnionProcess(header, charSizes, ypos, xpos):
	global blockSetList
	idInDSU={}#通过块位置获得在并查集中的下标
	dsu = DisjointSet.DisjointSet(len(header))
	blockList = []
	for i in range(len(header)):
		blockList.append( Block(header[i], xpos[i], charSizes[i], ypos[i], i) )
		idInDSU[blockList[-1].hash()] = i
	unionBlockByRectangleIntersect(dsu, blockList)
	blockSetList = getBlockSetList(dsu, blockList)
	fixSingleBlockContainAt(dsu, blockSetList, idInDSU)
	blockSetList = getBlockSetList(dsu, blockList)
	for i in range(len(blockSetList)):
		blockSetList[i].sort(key = lambda x: (x.u+x.d)/2.0)
	#print 'blockSetList', blockSetList

	#GraphicManager.printRecWithWords(Tools.flatList(blockSetList), idInDSU, dsu)#绘图查看分块效果

	sortedIdxList = []
	for blockset in blockSetList:
		for block in blockset:
			sortedIdxList.append(block.originIdx)
	return sortedIdxList

def matchInBlocks(label):
	authorInfo = []
	i=0
	for blockset in blockSetList:
		for block in blockset:
			block.label = label[i]
			i+=1
	for blockset in blockSetList:
		name=[]
		address=''
		affiliation=''
		email=[]
		for block in blockset:
			#if block.label == '<author>':
			#	name.append(block.header)
			if block.label == '<author>':#抽一行的作者，一行可能有多个作者
				tmpStr=[]
				if StringManager.hasBigComma(block.header, tmpStr):
					name += tmpStr[0].split('#')
				elif len(block.header.strip().split()) >= 4:
					name += splitByBigSpace(block.header, xpos[i])
				else:
					name.append(block.header)

			if block.label == '<affiliation>':
				affiliation += block.header
			if block.label == '<address>':
				address += block.header
			if block.label == '<email>':
				#email.append(block.header)
				email += EmailManager.handleOneEmailBlock(block.header)
			emailId=0
		for a_name in name:
			a_email = ''
			if emailId < len(email):
				a_email = email[emailId]
				emailId += 1
			authorInfo.append(Author.Author(a_name, address, affiliation, a_email))
	return authorInfo