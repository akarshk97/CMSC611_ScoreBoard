issueQueue = []
fetchQueue = []
readQueue = []
executeQueue = []
wbQueue = []

intDict = {'integer' : 0, 'latency' : 1}
dataDict = {'data' : 0, 'latency' : 1}


adderDict = {}
multDict = {}
divDict = {}
cacheDict = {}


adderUnit = []
multUnit = []
divUnit = []
cache = []
functionUnits = {}
functionUnits.update(adderDict)
functionUnits.update(multDict)
functionUnits.update(divDict)
functionUnits['integer'] = 0
functionUnits['data'] = 0


class Instruction:
    def __init__(self, instStr, instType, dest=None, s1=None, s2=None, branch=None):
        self.instStr =instStr
        self.instType = instType
        self.dest = dest
        self.s1 = s1
        self.s2 = s2
        self.branch = branch
        self.unitType = 0
        self.s1offset = 0
        self.s2offset = 0
        self.fetch_time=0
        self.issue_time = 0
        self.read_time = 0
        self.exec_start_time = 0
        self.exec_end_time = 0
        self.wb_time = 0
         
    # def __str__(self):
    #     return " %s %s %s %s %s" % (self.branch, self.instType, self.dest, self.s1, self.s2)

class Config:
    def __init__(self, unitType, latency, count):
        self.unitType = unitType
        self.latency = latency
        self.count = count

class InstCycles:
    def __inti__(self, instStr, fetch_time, issue_time, read_time, exec_end_time, wb_time, raw, waw, struct):
        self.instStr = instStr
        self.fetch_time = fetch_time
        self.issue_time = issue_time
        self.read_time = read_time
        self.exec_end_time = exec_end_time
        self.wb_time = wb_time
        self.raw = raw
        self.waw = waw
        self.struct = struct
        


def readConfig():
    
    f = open("Config.txt", "r")
    units = f.readlines()
    for x in units:
        x.strip()
        x = x.split(':')
        count, latency = x[1].strip().split(',')
        if x[0].lower()=="FP adder".lower() :
            for i in range(int(count)):
                adderUnit.append(Config(x[0], int(latency.strip()),int(count) ))
                adder = x[0]+str(i+1)
                adderDict[adder] = 0

        if x[0].lower()=="FP Multiplier".lower() :
            for i in range(int(count)):
                multUnit.append(Config(x[0], int(latency.strip()),int(count)))
                mult = x[0]+str(i+1)
                multDict[mult] = 0
        if x[0].lower()=="FP divider".lower() :
            for i in range(int(count)):
                divUnit.append(Config(x[0], int(latency.strip()),int(count)))
                div = x[0]+str(i+1)
                divDict[div] = 0
        if x[0].lower()=="I-Cache" :
            for i in range(int(count)):
                cache.append(Config(x[0], int(latency.strip()),int(count)))
                div = x[0]+str(i+1)
                cacheDict[div] = 0
    
    #print(adderDict,multDict,divDict,cacheDict)
    #print(vars(adderUnit[0]))

    #instList = []

        

def readInst():
    instList = []
    f = open("inst1.txt", "r", encoding = 'utf-8-sig')
    instructions = f.readlines()
    for x in instructions:
        #removing front and end spaces
        x = x.strip()
        x = x.replace('\t', ' ')
        x = x.replace(',', '')
        i = x.split(' ')

        # creating instruction objects using len of the list
        if(':' in i[0]):
            if(len(i)==5):

                s1offset = 0
                s2offset = 0
                branch = i[0]
                instType = i[1]
                dest = i[2]
                if '(' in i[3] :
                    s1offset = i[3][0:i[3].index('(')]
                    s1 = i[3][-3:-1]
                else:
                    s1 = i[3]
                if '(' in i[4] :
                    s2offset = i[4][0:i[3].index('(')]
                    s2 = i[4][-3:-1]
                else:
                    s2 = i[4]
                obj = Instruction(x, instType, dest, s1, s2, branch)
                obj.s1offset = s1offset
                obj.s2offset = s2offset

                instList.append(obj)
            elif(len(i)==4):
                s1offset = 0
                branch = i[0]
                instType = i[1]
                dest = i[2]
                if '(' in i[3] :
                    s1offset = i[3][0:i[3].index('(')]
                    s1 = i[3][-3:-1]
                else:
                    s1 = i[3]
                #obj.s2offset = s2offset
                obj = Instruction(x, instType, dest, s1, None,branch)
                obj.s1offset = s1offset
                instList.append(obj)    
        elif(len(i)==3):
            s1offset=0
            instType = i[0]
            dest = i[1]
            #s1 = i[2]
            if '(' in i[2] :
                s1offset = i[2][0:i[2].index('(')]
                s1 = i[2][-3:-1]
            else:
                s1 = i[2]
            obj = Instruction(x, instType, dest, s1)
            obj.s1offset = s1offset
            instList.append(obj)
        elif(len(i)==4):
            s1offset = 0
            s2offset = 0
            instType = i[0]
            dest = i[1]
            # s1 = i[2]
            # s2 = i[3]
            if '(' in i[2] :
                s1offset = i[2][0:i[3].index('(')]
                s1 = i[2][-3:-1]
            else:
                s1 = i[2]
            if '(' in i[3] :
                s2offset = i[3][0:i[3].index('(')]
                s2 = i[3][-3:-1]
            else:
                s2 = i[3]
            obj = Instruction(x, instType, dest, s1, s2)
            obj.s1offset = s1offset
            obj.s2offset = s2offset
            instList.append(obj)
        elif(len(i) == 1):
            instType = i[0]
            instList.append(Instruction(x, instType))
    return instList

dictRegister = {}

def fetch(obj, clockTime):
    if(len(issueQueue) == 0):
        issueQueue.append(obj)
        obj.fetch_time = clockTime
        return True
    return False

def issue(q,clockTime):
    
    if len(q) == 0:
        return False
    obj = q[0]
    if((obj.instType.upper() in ['DADD', 'DADDI', 'DSUB', 'DSUBI', 'AND', 'ANDI', 'OR', 'ORI', 'LI', 'LUI']) and (intDict['integer']==0) and (obj.dest not in dictRegister or dictRegister[obj.dest] != 1)):
        # for i in intDict.keys():
        #     if intDict[i] == 0:
        #         intDict[i] = 1
        #         break
        #integerUnit = 1
        intDict['integer'] = 1
        obj.unitType = 'integer'
        dictRegister[obj.dest] = 1
        obj.issue_time = clockTime
        readQueue.append(issueQueue.pop())

        
    elif((obj.instType.upper() in ['LW', 'SW','L.D', 'S.D']) and (dataDict['data']==0) and (obj.dest not in dictRegister or dictRegister[obj.dest] != 1)):
        # for i in dataDict.keys():
        #     if dataDict[i] == 0:
        #         dataDict[i] = 1
        #         break
        dataDict['data']=1
        obj.unitType = 'data'
        dictRegister[obj.dest] = 1
        #print(dictRegister)
        obj.issue_time = clockTime
        readQueue.append(issueQueue.pop())

    elif((obj.instType.upper() in ['ADD.D', 'SUB.D']) and ( 0 in adderDict.values()) and (obj.dest not in dictRegister or dictRegister[obj.dest] != 1)):
        for i in adderDict.keys():
            if adderDict[i] == 0:
                adderDict[i] = 1
                obj.unitType = 'adder'
                break
        
        dictRegister[obj.dest] = 1
        #print(dictRegister)
        obj.issue_time = clockTime
        readQueue.append(issueQueue.pop())

    elif((obj.instType.upper() in ['MUL.D']) and (0 in multDict.values()) and (obj.dest not in dictRegister or dictRegister[obj.dest] != 1)):
        for i in multDict.keys():
            if multDict[i] ==0:
                multDict[i] = 1
                obj.unitType = 'mult'
                break
        dictRegister[obj.dest] = 1
        obj.issue_time = clockTime
        readQueue.append(issueQueue.pop())

    elif((obj.instType.upper() in ['DIV.D']) and (0 in divDict.values()) and (obj.dest not in dictRegister or dictRegister[obj.dest] != 1)):
        for i in divDict.keys():
            if divDict[i] == 0:
                obj.unitType = 'div'
                divDict[i] = 1
                break
        dictRegister[obj.dest] = 1
        obj.issue_time = clockTime
        readQueue.append(issueQueue.pop())

def read(q, clockTime):
    if len(q) == 0:
        return False
    obj = q[0]
    if (obj.s1 not in dictRegister) or dictRegister[obj.s1] == 0:
        s1status = True
    if (obj.s2 not in dictRegister) or dictRegister[obj.s2] == 0:
        s2status = True
    if s1status and s2status:
        obj.read_time = clockTime
        executeQueue.append(readQueue.pop())


def exec(q, clockTime):
    if len(q) == 0:
        return False
    obj = q[0]
    
    if((obj.instType.upper() in ['DADD', 'DADDI', 'DSUB', 'DSUBI', 'AND', 'ANDI', 'OR', 'ORI', 'LI', 'LUI']) ):
        latency = intDict['latency']
    elif((obj.instType.upper() in ['LW', 'SW'])):
        latency = dataDict['latency']
    elif((obj.instType.upper() in ['L.D', 'S.D'])):
        latency = dataDict['latency'] + 1
    elif((obj.instType.upper() in ['ADD.D', 'SUB.D']) ):
        latency = adderUnit[0].latency
    elif((obj.instType.upper() in ['MUL.D']) ):
        latency = multUnit[0].latency
    elif((obj.instType.upper() in ['DIV.D']) ):
        latency = divUnit[0].latency
    #print(clockTime)
    if obj.exec_start_time == 0:
        obj.exec_start_time = clockTime
    if(clockTime - obj.exec_start_time == latency-1):
        obj.exec_end_time = clockTime
        wbQueue.append(executeQueue.pop())

def wb(q, clockTime):
    if len(q) == 0:
        return False
    obj = q[0]
    obj.wb_time = clockTime
    dictRegister[obj.dest] = 0
    obj.unitType == 'adder'
    for i in adderDict.keys():
        if adderDict[i] == 1:
            adderDict[i] = 0
            break
    obj.unitType == 'mult'
    for i in multDict.keys():
        if multDict[i] == 1:
            multDict[i] = 0
            break
    obj.unitType == 'div'
    for i in divDict.keys():
        if divDict[i] == 1:
            divDict[i] = 0
            break
    obj.unitType == 'integer'
    intDict['integer'] = 0

    obj.unitType == 'data'
    intDict['data'] = 0

    print(obj.fetch_time,obj.issue_time,obj.read_time,obj.exec_end_time,obj.wb_time)
    wbQueue.pop()

def mips_simulator():
    instList = readInst()
    for i in instList:
        print(vars(i))
    # print(len(instList))
    # print(instList[0])
    i=0
    cc = 1
    while cc < 500:
        try:
            wb(wbQueue, cc)
        except:
            print('error in wb')
        try:
            exec(executeQueue, cc)
        except:
            print('error in executeQueue')

        try:
            read(readQueue, cc)
        except:
            print('error in readQueue')
        try:
            issue(issueQueue, cc)
        except:
            print('error in issueQueue')
        try:
            if fetch(instList[i], cc) == True :
                i += 1
        except:
            print('error in fetching ')
        cc += 1

if __name__ == '__main__':
    readConfig()
    mips_simulator()