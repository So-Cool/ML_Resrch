#!/usr/bin/env python


# import section
# import os
import sys
import subprocess
# import numpy
from random import randint
# import pickle


# global variables
weka = "java -cp weka.jar "
removeFilter1 = "weka.filters.unsupervised.attribute.Remove -R "
removeFilter2 = " -i "
removeFilter3 = " -o "
addIDfilter = "weka.filters.unsupervised.attribute.AddID -i "

meta1 = "weka.classifiers.meta.FilteredClassifier -F \'" # remove filter + in
meta2 =	" \' -W " # + classifier w/o options + -t train -T test -p 1
meta3 = " -- " # other classifer options -C 0.25 -M 2

trainingSwitch = " -t "
testSwitch = " -T "

#	J48
J481a = "weka.classifiers.trees.J48 -v -o -s "
J481b = " -C 0.25 -M 2 "
J482a = "weka.classifiers.trees.J48 -p 1 "
J482b = J481b
#	SMO-Poly
SMOP1a = "weka.classifiers.functions.SMO -v -o -s "
SMOP1b = ( " -C 1.0 -L 0.0010 -P 1.0E-12 -N 0 -V -1 -W 1 -K \"weka.classifiers.functions." +
	"supportVector.PolyKernel -C 250007 -E 1.0\"" )
SMOP2a = "weka.classifiers.functions.SMO -p 1 "
SMOP2b = SMOP1b
#	SMO-RBF
SMOR1a = "weka.classifiers.functions.SMO -v -o -s "
SMOR1b = ( " -C 1.0 -L 0.0010 -P 1.0E-12 -N 0 -V -1 -W 1 -K \"weka.classifiers.functions.supportVector." +
	"RBFKernel -C 250007 -G 0.01\"" )
SMOR2a = "weka.classifiers.functions.SMO -p 1 "
SMOR2b = SMOR1b
#	IBk
IBk1a = "weka.classifiers.lazy.IBk -v -o -s "
IBk1b = ( " -K 1 -W 0 -A \"weka.core.neighboursearch.LinearNNSearch -A " +
	"\\\"weka.core.EuclideanDistance -R first-last\\\"\"" )
IBk2a = "weka.classifiers.lazy.IBk -p 1 "
IBk2b = IBk1b


# functions
################################################################################
# count number of labels to predict
#
#
def countLabels(labels) :
	counter = 0

	for i in labels :
		if "<label name=\"" in i and "\"></label>" in i :
			counter += 1

	return counter
#
#
#
################################################################################
################################################################################
# give # to all data instances to be able to distinguish them later on
#
#
def IDdata(fileName):
	clas = subprocess.Popen( weka + addIDfilter + fileName + " -o " +
		fileName[0:-5] + "_ID.arff", stdout=subprocess.PIPE, shell=True )
	(out, err) = clas.communicate()
	if err!=None:
		print "Error while appending ID:\n" + err
		exit()
#
#
#
################################################################################
################################################################################
# remove ground truth for labels
#
#
def rmAttributes(fileName, IDrange):
	clas = subprocess.Popen( weka + removeFilter1 + IDrange + removeFilter2 +
		fileName[0:-5] + "_ID.arff" + removeFilter3 + fileName[0:-5] +
		"_unlabeled.arff", stdout=subprocess.PIPE, shell=True )
	(out, err) = clas.communicate()
	if err!=None:
		print "Error while removing labels:\n" + err
		exit()
#
#
#
################################################################################
################################################################################
# count number of data instances; return header of arff file and return list of
#	instances in arff file
#
def handleInstances(dataList):
	dataStarted = False
	counter = 0
	header = []
	instances = []
	for line in dataList:
		# exclude empty lines and commented lines
		if line[0] == '%' or line[0] == "\n" or line[0] == "\r" :
			continue

		# until "@data" put everything to header
		if not dataStarted and line.find("@data") == -1 :
			header.append(line)
		elif not dataStarted and "@data" in line :
			header.append(line)
			dataStarted = True
		# put all the rest into instances
		elif dataStarted :
			counter += 1
			instances.append(line)

	return (counter, header, instances)
#
#
#
################################################################################
################################################################################
# count number of attributes present in the data set
#
#
def countAtributes( data ) :
	count = 0

	# if it's empty return error
	if not data :
		print "Error encountered. Data file empty!"
		exit()
	# count commas what corresponds to attributes
	for i in data[0] :
		if i == ',' :
			count += 1

	# one less comma than instances
	return count + 1
#
#
#
################################################################################
################################################################################
# generate a list of 'x' indexes to pick for supervised learning
#
#
def supIndex(noToExtract, noInstances) :
	if noToExtract > noInstances :
		print( "You are extracting more elements that there is instances." +
			str(noToExtract) + " out of " + str(noInstances) + "!" )
		exit()

	remove = []

	for i in range(noToExtract):
		lock = 0
		# generate random between 0 and noInstances included
		r = randint(0, noInstances - 1)
		# if already appended to remove find another one
		# ???????what if all are included???????
		# try 1.5*noInstances times if not throw error
		while r in remove :
			if lock > 1.5*noInstances :
				# distinct element not found; throw error
				print "I think that you want to extract to many elements."
				exit()
			lock += 1
			r = randint(0, noInstances - 1)
		remove.append(r)
	return remove
#
#
#
################################################################################
################################################################################
# generate 2 lists: one containing training(labeled) instances and the other
# list of instances to instances to improve a classifier
#
def createTT(removeInd, instances) :
	rm = removeInd[:]
	test = []
	training = []

	for ind, val in enumerate(instances):
		# instance with ground-truth
		if ind in rm :
			# append element to training
			training.append(val)
			# remove ind element
			rm.remove(ind)
			continue
		test.append(val)

	if not rm :
		print "All elements appended."

	return (training, test)
#
#
#
################################################################################
################################################################################
# create arff files with selected instances
#
#
def saveToarff(fileName, arffHeader, unlabeledArffHeader, Training, Test,
	unlabeledTest, removeLabels) :
	# open two files to write
	testStream = open( fileName[0:-5]+"_unlabeledTest.arff", 'w')
	trainingStream = open( fileName[0:-5]+"_labeledTraining.arff", 'w')

	# save header info to streams
	for i in arffHeader :
		trainingStream.write(i)
	if removeLabels :
		for i in unlabeledArffHeader :
			testStream.write(i)
	else :
		for i in arffHeader :
			testStream.write(i)

	# save training info to streams
	for i in Training :
		trainingStream.write(i)

	# save test info to stream
	if removeLabels :
		for i in unlabeledTest :
			testStream.write(i)
	else :
		for i in Test :
			testStream.write(i)
#
#
#
################################################################################
################################################################################
# train selected classifiers with newly created arff files and test on boosting
#	data
#
def trainClassifier(fileName) :
	# take a random seed
	# r = 0

	# classify with J48
	# r = randint(1, 1000000)
	clas = subprocess.Popen( weka + meta1 + removeFilter1 + str(1) + meta2 +
		J482a + trainingSwitch + fileName[0:-5] + "_labeledTraining.arff" + 
		testSwitch + fileName[0:-5] + "_unlabeledTest.arff" + meta3 + J482b,
		stdout=subprocess.PIPE, shell=True )
	(J48, err) = clas.communicate()
	if err!=None:
		print "Error while classifying J48:\n" + err
		exit()

	# classify with IBk
	# r = randint(1, 1000000)
	clas = subprocess.Popen( weka + meta1 + removeFilter1 + str(1) + meta2 +
		IBk2a + trainingSwitch + fileName[0:-5] + "_labeledTraining.arff" + 
		testSwitch + fileName[0:-5] + "_unlabeledTest.arff" + meta3 + IBk2b,
		stdout=subprocess.PIPE, shell=True )
	(IBk, err) = clas.communicate()
	if err!=None:
		print "Error while classifying IBk:\n" + err
		exit()

	# classify with SMO-Poly
	# r = randint(1, 1000000)
	clas = subprocess.Popen( weka + meta1 + removeFilter1 + str(1) + meta2 +
		SMOP2a + trainingSwitch + fileName[0:-5] + "_labeledTraining.arff" + 
		testSwitch + fileName[0:-5] + "_unlabeledTest.arff" + meta3 + SMOP2b,
		stdout=subprocess.PIPE, shell=True )
	(SMOP, err) = clas.communicate()
	if err!=None:
		print "Error while classifying SMO-Poly:\n" + err
		exit()

	# classify with SMO-RBF
	# r = randint(1, 1000000)
	clas = subprocess.Popen( weka + meta1 + removeFilter1 + str(1) + meta2 +
		SMOR2a + trainingSwitch + fileName[0:-5] + "_labeledTraining.arff" + 
		testSwitch + fileName[0:-5] + "_unlabeledTest.arff" + meta3 + SMOR2b,
		stdout=subprocess.PIPE, shell=True )
	(SMOR, err) = clas.communicate()
	if err!=None:
		print "Error while classifying SMO-RBF:\n" + err
		exit()

	return( IBk, J48, SMOP, SMOR )
#
#
#
################################################################################
################################################################################
# make sens out from weka output
#
#
def extractOutput( rawIBk, rawJ48, rawSMOP, rawSMOR ) :
	rawData = [rawIBk, rawJ48, rawSMOP, rawSMOR]
	data = [ [], [], [], [] ] # IBk, J48, SMOP, SMOR

	# extract _ID_ and _prediction-ID_ from raw data
	#	find (*) brackets and extract id from inside
	#	 frist found brackets contain 'ID' inside so ignore it
	for ind, val in enumerate(rawData) :
		ID = []
		prediction = []
		# find all brackets
		tempIDa = [j for j, y in enumerate(val) if y == '(']
		tempIDb = [j for j, y in enumerate(val) if y == ')']
		# if number of brackets do not agree throw exception
		if len(tempIDa) != len(tempIDb) :
			print "Number of '(' and ')' does not match. Error encountered!"
			exit()
		# extract content of brackets
		for i in range(1, len(tempIDa)) :
			 ID.append( int( val[tempIDa[i]+1:tempIDb[i]] ) )

		# find all the ':'
		tempPre = [j for j, y in enumerate(val) if y == ':']
		# if number of ':'/2 is not equal to number of ')' throw error
		if len(tempPre)/2 != len(tempIDa)-1 :
			print( "Number of '(' and ')' does not match with number of ':'. " +
				"Error encountered!" )
			exit()
		# extract predictions
		# WARNING - restriction up to 9 values of predicted label - ERROR
		for i in range(1, len(tempPre), 2) :
			prediction.append( int( val[tempPre[i]-1:tempPre[i]] ) )

		# make a tuple (ID, prediction) and put into appropriate list
		# check whether theres exact amount of elements in both lists to zip
		if len(ID) != len(prediction) :
			print( "Number of IDs does not match with number of predictions. " +
				"Error encountered!" )
			exit()
		# zip all results into pairs (ID, prediction) and sort according to ID
		data[ind] = zip( ID, prediction )[:]
		# sort data according to ID
		data[ind].sort(key=lambda tup: tup[0])

	return ( data[0], data[1], data[2], data[3] )
#
#
#
################################################################################


# main program
#	read arguments to list
argumentList = list(sys.argv)

#	check correct number of arguments
if len(argumentList) < 2:
	print ( "There should be at least 1st argument given:" + "\n" +
		"	-*-1st: data set in 'arff' format" + "\n"
		"	-*-2nd: file containing labels in 'xml' format" )
	print( "If only 1st argument is given data set is treated as single class" +
		" classification.\n" + "If both arguments are given data is treated " +
		"as multi class classification an classified on each label " +
		"separately.\n" + "If you haven't supplied 2nd argument and you still" +
		" want to classify multi-label dataset please provide number of " +
		"labels when asked to confirm." )
		# + "\n" + "	-*- number of iterations" )
	exit()

#	if second argument not suppled consider data set as single labeled
if len(argumentList) == 2 :
	noLabels = 1
else :
	#	open labels data
	rawLabels = open(argumentList[2], 'r')
	labels = list(rawLabels)
	#	...and count them
	noLabels = countLabels(labels)

#	check whether counting is correct
print( str(noLabels) + " labels have(has) been found. Is it Correct?" )
noLabelsUsr = None
while not noLabelsUsr :
	try:
		noLabelsUsr = raw_input( "To confirm type 'y' or if the number is " +
			"incorrect please give true number of labels: " )
		# if user put 'y' continue
		if noLabelsUsr == 'y' :
			continue

		noLabels = int(noLabelsUsr)

	except ValueError:
		print 'Invalid Number. For YES write \'y\' and confirm with \'return\'.'
		noLabelsUsr = None

#	put ID as a first element of data
IDdata(argumentList[1])

#	open file with IDs
rawFile = open(argumentList[1][0:-5] + "_ID.arff", 'r')
fileList = list(rawFile)

#	count the number of instances and get data list and header list
(noInstances, arffHeader, data) = handleInstances(fileList)

#	count number of attributes
noAtributes = countAtributes(data)

#	remove the ground truth for labels
IDrangeRm = ( str(noAtributes-noLabels+1) + "-" + str(noAtributes) )
rmAttributes(argumentList[1], IDrangeRm)

#	get list of data instances with removed ground truth
rawFileUnlabeled = open(argumentList[1][0:-5] + "_unlabeled.arff", 'r')
fileUnlabeled = list(rawFileUnlabeled)
(empty, unlabeledArffHeader, unlabeledData) = handleInstances( fileUnlabeled )

#	ask how many to use for supervised learning
sup = None
while not sup :
	try:
		sup = int( raw_input( "How many out of " + str(noInstances) +
			" instances do you want to use for " + "supervised learning?: " ) )
	except ValueError:
		print 'Invalid Number'

#	Give a list of indexes to use for supervised learning
supIndexes = supIndex( sup, noInstances )

#	extract supIndexes and write to arff file
(Training, Test) = createTT(supIndexes, data)
(empty, unlabeledTest) = createTT(supIndexes, unlabeledData)

#	convert lists to arff files and write set_training.arff and set_test.arff
#	rmLabels decides whether to use labeled data or unlabeled as test set
rmLabels = False # True
saveToarff(argumentList[1], arffHeader, unlabeledArffHeader, Training, Test,
	unlabeledTest, rmLabels)

# 1
#	train classifiers on initial train set with mentioned schemes and test
#	(predict) on rest and return raw outputs
( rawIBk, rawJ48, rawSMOP, rawSMOR ) = trainClassifier(argumentList[1])

#	make sens of outputs
( IBk, J48, SMOP, SMOR ) = extractOutput( rawIBk, rawJ48, rawSMOP, rawSMOR )

#	check matching predictions

#	ask for numbers of samples to to add and boost classifier
boostNums = None
boostNum = 0
while not boostNums :
	try:
		# give current statistics
		print( "========================================" +
			"========================================" )
		print( "There are: " + "num" + " instances that agree in all 4 " +
			"classifiers." )
		print( "There are: " + "num" + " instances that agree in 3 out of 4 " +
			"classifiers." )
		print( "There are: " + "num" + " instances that agree in 2 out of 4 " +
			"classifiers." )
		print( "There are: " + "num" + " instances that agree in 1 out of 4 " +
			"classifiers." )
		print( "There are: " + "num" + " instances that agree in non of " +
			"classifiers." )
		print( "Priority in choosing instances for boost operation is given " +
			"to ones that agrees in most of classifiers." )
		print( "========================================" +
			"========================================\n" )

		boostNums = raw_input( "How many out of " + str(noInstances-sup) +
			" instances do you want to use to boost classifier?" + "\n" +
			"If you want to stop boosting operation and check accuracy of " +
			"classifier put letter [s]." )

		# if user put 's' stop boosting
		if boostNums == 's' :
			# go to 'cross-validating' classifier
			continue

		boostNum = int( boostNums )

		# number must be greater than 0
		if boostNum <= 0 :
			print "Number must be greater than 0!"
			boostNums = None

	except ValueError:
		print 'Invalid Number. I you want to stop put [s].'
		boostNums = None

#	rebuilt classifier with # of samples defined by user choosing all instances
#	where majority of classifiers agrees
#boils down to rebuilding datasets and going back to stage #1


#
##	Sunday
#
#	check accuracy of created classifier

#	then perform n-times with each of classifiers with cross validation
#	to compare accuracy of results

#	if theres enough time implement multilabel with 1 label at time using reformdata.py
#	from your last project
