'''
-Recreates the keyframes on an object in world space from all the connected groups and constraints

-Creates a locator that has the original animation trajectory before the transfer as reference

-May interpolate differently from original animation - may have to add more keyframes for a more
accurate transfer

'''

import maya.cmds as cmds

def removeUnicode(unicode):
     unicodeString = str(unicode)
     return unicodeString[3:len(unicode)-3]

def findParent(object):
    parent = cmds.listRelatives(object, allParents=True)
    if parent == None:
        return None
    else:
        return removeUnicode(parent)

def collectParents(object):
    parentRelatives = []

    def checkAndAppendParents(object):
        if findParent(object) != None:
            currentParent = findParent(object)
            #print "appending current parent: " + str(currentParent)
            parentRelatives.append(currentParent)
            #print "finding parent: " + str(findParent(currentParent))
            checkAndAppendParents(currentParent)
        else:
            pass

    checkAndAppendParents(object)
    #print str(object) + " parentRelatives: " + str(parentRelatives)
    return parentRelatives

def findConstraints(object):
    foundConstraintsList = cmds.listConnections(object, t="constraint")
    if foundConstraintsList == None:
        uniqueConstraintsList = []
    else:
        uniqueConstraintsList = set(foundConstraintsList)
    constraintsList = []
    # makes constraint list without unicode
    for i in uniqueConstraintsList:
        constraintsList.append(str(i))
    #print str(object) + " constraints list: " + str(constraintsList)
    return constraintsList

def collectIncomingConnections(object):
    listIncomingConnections = cmds.listConnections(object, d=False)
    incomingConnections = []
    if listIncomingConnections != None:
        for i in listIncomingConnections:
              if i == object:
                   pass
              else:
                   incomingConnections.append(str(i))
    else:
        pass
    #print str(object) + " incoming connections: " + str(sorted(set(incomingConnections)))
    return sorted(set(incomingConnections))                                

def findConstraintInfluencers(object):
    foundConstraints = findConstraints(object)
    constraintInfluencers = []
    for i in foundConstraints:
        incomingConnections = collectIncomingConnections(i)
        for c in incomingConnections:
            constraintInfluencers.append(c)
    return sorted(set(constraintInfluencers)) 


def collectTransformInfluencers(object):
     transformInfluencers = []

     def checkDuplicateInfluencers(object):
          duplicates = 0
          for i in transformInfluencers:
              if i == object:
                   duplicates += 1
              else: 
                    pass
          if duplicates > 0:
              return True
          else:
              return False

     def collectInfluencers(object):

         # find constraint connections of object
         constraintInfluencers = findConstraintInfluencers(object)
         for i in constraintInfluencers:
             if checkDuplicateInfluencers(i) == False:
                 transformInfluencers.append(i)
                 collectInfluencers(i)

         # find parent of object
         collectedParents = collectParents(object)
         for i in collectedParents:
             if checkDuplicateInfluencers(i) == False:
                 transformInfluencers.append(i)
                 collectInfluencers(i)

     collectInfluencers(object)
     return sorted(set(transformInfluencers))


# Collect Time Changes/key frame timings     
def collectTimeChanges(object):
    timeChanges = cmds.keyframe(object, query=True, tc=True)
    if timeChanges == None:
          timeChanges = 0
          uniqueKeyframes = []
    else:
          uniqueKeyframes = sorted(set(timeChanges))
    return uniqueKeyframes  


# returns keyframes of object and object's parents in an array
def findEffectingKeyframes(object):
    keyframeArray = []
    # collect time changes on object
    for i in collectTimeChanges(object):
          keyframeArray.append(i)

    for i in collectTransformInfluencers(object):
          for k in collectTimeChanges(i):
              keyframeArray.append(k)
    return sorted(set(keyframeArray))


# Collect Keyframe Data into a dictionary
def collectKeyframeData(currentObject):
    timeChanges = cmds.keyframe(currentObject, query=True, tc=True)
    #print "timeChanges: " + str(timeChanges)

    valueChanges = cmds.keyframe(currentObject, query=True, vc=True, at= ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"])
    #print "valueChanges: " + str(valueChanges)

    if timeChanges == None:
        timeChanges = 0
        uniqueKeyframes = []
    else:
        uniqueKeyframes = sorted(set(timeChanges))
    #print "uniqueKeyframes: " + str(uniqueKeyframes)

    if valueChanges == None:
        valueChanges = []
        keyframeAmount = 0
    else:
        keyframeAmount = len(valueChanges)
    #print "length: " + str(keyframeAmount)
    
    # manage keyframe data into a dictionary
    keyframeDictionary = {}

    # create dictionary keys representing keyframes
    for i in range(len(uniqueKeyframes)):
        keyframeDictionary[uniqueKeyframes[i]] = []

    # append values of position data to keys
    for i in range(keyframeAmount):
         currentKeyframe = timeChanges[i]
         currentValue = valueChanges[i]
         #print "currentKeyframe: " + str(currentKeyframe) + " | currentValue: " + str(currentValue)
         keyframeDictionary[currentKeyframe].append(currentValue)

    return keyframeDictionary


# create locator and copy anim data
def copyAnimToLocator(object):
    keyframeList = findEffectingKeyframes(object)
    locatorName = "loc_" + str(object) + "_copyAnim"
    cmds.spaceLocator(n = locatorName)
    for i in keyframeList:
         cmds.currentTime(i, edit = True)
         constraintName = str(object) + "_currentFrame_parentConstraint"
         cmds.parentConstraint(object, locatorName, mo=0, name = constraintName)

         cmds.setKeyframe(locatorName, at="translateX")
         cmds.setKeyframe(locatorName, at="translateY")
         cmds.setKeyframe(locatorName, at="translateZ")
         cmds.setKeyframe(locatorName, at="rotateX")         
         cmds.setKeyframe(locatorName, at="rotateY")  
         cmds.setKeyframe(locatorName, at="rotateZ")  

         cmds.delete(constraintName)

def deleteAttributeKeys(object, attributeArray):
    keyframeDictionary = collectKeyframeData(object)
    for f in keyframeDictionary:
        currentFrame = int(f)
        for a in attributeArray:
             cmds.cutKey(object, time = (currentFrame, currentFrame), at = str(a))
         


# deletes animation of object, copies to source object
def reanimateToObject(reanimatedObject,sourceAnimObject):
    sourceAnimKeyframes = findEffectingKeyframes(sourceAnimObject)
    keyedAttributes = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]
    deleteAttributeKeys(reanimatedObject, keyedAttributes)

    for i in sourceAnimKeyframes:
         cmds.currentTime(i, edit = True)
         constraintName = str(reanimatedObject) + "_currentFrame_parentConstraint"
         cmds.parentConstraint(sourceAnimObject, reanimatedObject, mo=0, name = constraintName)

         cmds.setKeyframe(reanimatedObject, at="translateX")
         cmds.setKeyframe(reanimatedObject, at="translateY")
         cmds.setKeyframe(reanimatedObject, at="translateZ")
         cmds.setKeyframe(reanimatedObject, at="rotateX")         
         cmds.setKeyframe(reanimatedObject, at="rotateY")  
         cmds.setKeyframe(reanimatedObject, at="rotateZ")  

         cmds.delete(constraintName)


def createOriginalAnimLocator(object):
      # create a corresponding locator - named "loc_object_originalAnim"
      locatorName = str("loc_" + str(object) + "_originalAnim")
      cmds.spaceLocator( n = locatorName)

      # parent constrain locator to object with offset off
      parentConstrainName = str(locatorName + "_parentConstrain")
      cmds.parentConstraint(  object, locatorName, mo = 0, n = parentConstrainName )

      # bake locator translate and rotation animation based on first and last keyframe
      #get Start and End Frame of Time Slider
      keyframeArray = findEffectingKeyframes(object)
      endIteration = len(keyframeArray) - 1
      
      startFrame = keyframeArray[0]
      endFrame = keyframeArray[endIteration]
      
      cmds.bakeResults( locatorName, t=(startFrame, endFrame))         

      # delete parent constrain on locator       
      cmds.delete(parentConstrainName)


def reanimateToWorldSpace(object):
    createOriginalAnimLocator(object)
    objectLocator = "loc_" + str(object) + "_copyAnim"
    copyAnimToLocator(object)
    cmds.parent(object, w=1)
    reanimateToObject(object, objectLocator)
    cmds.delete(objectLocator)


selectedObject = removeUnicode(cmds.ls(sl=True))
reanimateToWorldSpace(selectedObject)