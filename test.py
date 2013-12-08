#!/usr/bin/python
import random

import Queue
import threading
import time

"""
nameList = ["One", "Two", "Three", "Four", "Five"]

exitFlag = 0

class searchThread(threading.Thread):

    def __init__(self, threadID, q, res):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.q = q
        self.res = res

    def run(self):
        print "Starting " + str(self.threadID)
        self.process_data(str(self.threadID), self.q, self.res)
        print "Exiting " + str(self.threadID)

    def process_data(self, threadName, q, res):
        while not exitFlag:
            queueLock.acquire()
            if not workQueue.empty():
                data = q.get()
                queueLock.release()
                time.sleep(random.randrange(5))
                print "%s processing %s" % (threadName, data)
                res.put("%s processing %s" % (threadName, data))
            else:
                queueLock.release()
            time.sleep(1)


queueLock = threading.Lock()
workQueue = Queue.Queue()
resQueue = Queue.Queue()

threads = []
threadID = 1

# Create new threads
for t in range(len(nameList)):
    thread = searchThread(threadID, workQueue, resQueue)
    thread.start()
    threads.append(thread)
    threadID += 1

# Fill the queue
queueLock.acquire()
for word in nameList:
    workQueue.put(word)
queueLock.release()

# Wait for queue to empty
while not workQueue.empty():
    pass

# Notify threads it's time to exit
exitFlag = 1


# Wait for all threads to complete
for t in threads:
    t.join()




print "Exiting Main Thread"

result = []
while not resQueue.empty():
    result.append(resQueue.get())

print result
"""


"""
def get_mem(servername, q):
    #res = os.popen('ssh %s "grep MemFree /proc/meminfo | sed \'s/[^0-9]//g\'"' % servername)
    time.sleep(random.randrange(5))
    q.put(servername)



q = Queue.Queue()

servers = ['serv1','serv2','serv3']
for i in servers:
    threading.Thread(target=get_mem, args=(i, q)).start()

result = []
for i in servers:
    result.append(q.get())

print result

"""


nameList = ["One", "Two", "Three", "Four", "Five"]

class searchThread(threading.Thread):

    def __init__(self, threadID, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.q = q

    def run(self):
        process_data(str(self.threadID), self.q)


def process_data(threadName, q):
    time.sleep(random.randrange(5))
    q.put("%s processing %s" % (threadName, 'data'))


#queueLock = threading.Lock()
resQueue = Queue.Queue()

threads = []
threadID = 1

# Create new threads
for t in range(len(nameList)):
    thread = searchThread(threadID, resQueue)
    thread.start()
    threads.append(thread)
    threadID += 1


# Wait for all threads to complete
for t in threads:
    t.join()


result = []
while not resQueue.empty():
    result.append(resQueue.get())

print result
