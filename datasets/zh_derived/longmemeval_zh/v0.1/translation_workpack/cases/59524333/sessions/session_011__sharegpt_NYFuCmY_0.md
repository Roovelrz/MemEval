---
question_id: "59524333"
session_index: 11
session_id: "sharegpt_NYFuCmY_0"
timestamp: "2023/03/01 (Wed) 11:16"
is_evidence_session: false
turn_count: 2
translation_status: TODO
---
# Session 011 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
This is part of a ros package and in the path rospy/src/rospy/topics.py
class Subscriber(Topic):
 """
 Class for registering as a subscriber to a specified topic, where
 the messages are of a given type.
 """
 def \_\_init\_\_(self, name, data\_class, callback=None, callback\_args=None,
 queue\_size=None, buff\_size=DEFAULT\_BUFF\_SIZE, tcp\_nodelay=False):
 super(Subscriber, self).\_\_init\_\_(name, data\_class, Registration.SUB)
 #add in args that factory cannot pass in

 # last person to set these to non-defaults wins, not much way
 # around this
 if queue\_size is not None:
 self.impl.set\_queue\_size(queue\_size)
 if buff\_size != DEFAULT\_BUFF\_SIZE:
 self.impl.set\_buff\_size(buff\_size)

 if callback is not None:
 # #1852
 # it's important that we call add\_callback so that the
 # callback can be invoked with any latched messages
 self.impl.add\_callback(callback, callback\_args)
 # save arguments for unregister
 self.callback = callback
 self.callback\_args = callback\_args
 else:
 # initialize fields
 self.callback = self.callback\_args = None 
 if tcp\_nodelay:
 self.impl.set\_tcp\_nodelay(tcp\_nodelay) 
 
class \_SubscriberImpl(\_TopicImpl):
 """
 Underyling L{\_TopicImpl} implementation for subscriptions.
 """
 def \_\_init\_\_(self, name, data\_class):
 
 super(\_SubscriberImpl, self).\_\_init\_\_(name, data\_class)
 # client-methods to invoke on new messages. should only modify
 # under lock. This is a list of 2-tuples (fn, args), where
 # args are additional arguments for the callback, or None
 self.callbacks = [] 
 self.queue\_size = None
 self.buff\_size = DEFAULT\_BUFF\_SIZE
 self.tcp\_nodelay = False

 def add\_callback(self, cb, cb\_args):
 if self.closed:
 raise ROSException("subscriber [%s] has been closed"%(self.resolved\_name))
 with self.c\_lock:
 # we lock in order to serialize calls to add\_callback, but
 # we copy self.callbacks so we can it
 new\_callbacks = self.callbacks[:]
 new\_callbacks.append((cb, cb\_args))
 self.callbacks = new\_callbacks

 # #1852: invoke callback with any latched messages
 for c in self.connections:
 if c.latch is not None:
 self.\_invoke\_callback(c.latch, cb, cb\_args)

 def remove\_callback(self, cb, cb\_args):
 if self.closed:
 return
 with self.c\_lock:
 # we lock in order to serialize calls to add\_callback, but
 # we copy self.callbacks so we can it
 matches = [x for x in self.callbacks if x[0] == cb and x[1] == cb\_args]
 if matches:
 new\_callbacks = self.callbacks[:]
 # remove the first match
 new\_callbacks.remove(matches[0])
 self.callbacks = new\_callbacks
 if not matches:
 raise KeyError("no matching cb")

 def \_invoke\_callback(self, msg, cb, cb\_args):
 try:
 if cb\_args is not None:
 cb(msg, cb\_args)
 else:
 cb(msg)
 except Exception as e:
 if not is\_shutdown():
 logerr("bad callback: %s\n%s"%(cb, traceback.format\_exc()))
 else:
 \_logger.warn("during shutdown, bad callback: %s\n%s"%(cb, traceback.format\_exc()))
 
 def receive\_callback(self, msgs):
 """
 Called by underlying connection transport for each new message received
 @param msgs: message data
 @type msgs: [L{Message}]
 """
 # save reference to avoid lock
 callbacks = self.callbacks
 for msg in msgs:
 for cb, cb\_args in callbacks:
 self.\_invoke\_callback(msg, cb, cb\_args)

# Implementation note: Publisher attaches to a
# \_PublisherImpl singleton for that topic. The underlying impl
# manages the connections for that publication and enables
# thread-safe access

class Publisher(Topic):
 """
 Class for registering as a publisher of a ROS topic.
 """

 def \_\_init\_\_(self, name, data\_class, subscriber\_listener=None, tcp\_nodelay=False, latch=False, headers=None):
 super(Publisher, self).\_\_init\_\_(name, data\_class, Registration.PUB)

 if subscriber\_listener:
 self.impl.add\_subscriber\_listener(subscriber\_listener)
 if tcp\_nodelay:
 get\_tcpros\_handler().set\_tcp\_nodelay(self.resolved\_name, tcp\_nodelay)
 if latch:
 self.impl.enable\_latch()
 if headers:
 self.impl.add\_headers(headers)
 
 def publish(self, \*args, \*\*kwds):
 if self.impl is None:
 raise ROSException("publish() to an unregistered() handle")
 if not is\_initialized():
 raise ROSException("ROS node has not been initialized yet. Please call init\_node() first")
 data = args\_kwds\_to\_message(self.data\_class, args, kwds)
 try:
 self.impl.acquire()
 self.impl.publish(data)
 except roslib.message.SerializationError as e:
 # can't go to rospy.logerr(), b/c this could potentially recurse
 \_logger.error(traceback.format\_exc(e))
 raise ROSSerializationException(str(e))
 finally:
 self.impl.release() 

class \_PublisherImpl(\_TopicImpl):
 
 def \_\_init\_\_(self, name, data\_class):
 super(\_PublisherImpl, self).\_\_init\_\_(name, data\_class)
 if python3 == 0:
 self.buff = StringIO()
 else:
 self.buff = BytesIO()
 self.publock = threading.RLock() #for acquire()/release
 self.subscriber\_listeners = []

 # additional client connection headers
 self.headers = {}
 
 # publish latch, starts disabled
 self.is\_latch = False
 self.latch = None
 
 #STATS
 self.message\_data\_sent = 0
 def publish(self, message, connection\_override=None):
 #TODO: should really just use IOError instead of rospy.ROSException

 if self.closed:
 # during shutdown, the topic can get closed, which creates
 # a race condition with user code testing is\_shutdown
 if not is\_shutdown():
 raise ROSException("publish() to a closed topic")
 else:
 return
 
 if self.is\_latch:
 self.latch = message

 if not self.has\_connections():
 #publish() falls through
 return False

 if connection\_override is None:
 #copy connections so we can iterate safely
 conns = self.connections
 else:
 conns = [connection\_override]

 # #2128 test our buffer. I don't now how this got closed in
 # that case, but we can at least diagnose the problem.
 b = self.buff
 try:
 b.tell()

 # serialize the message
 self.seq += 1 #count messages published to the topic
 serialize\_message(b, self.seq, message)

 # send the buffer to all connections
 err\_con = []
 data = b.getvalue()

 for c in conns:
 try:
 if not is\_shutdown():
 c.write\_data(data)
 except TransportTerminated as e:
 logdebug("publisher connection to [%s] terminated, see errorlog for details:\n%s"%(c.endpoint\_id, traceback.format\_exc()))
 err\_con.append(c)
 except Exception as e:
 # greater severity level
 logdebug("publisher connection to [%s] terminated, see errorlog for details:\n%s"%(c.endpoint\_id, traceback.format\_exc()))
 err\_con.append(c)

 # reset the buffer and update stats
 self.message\_data\_sent += b.tell() #STATS
 b.seek(0)
 b.truncate(0)
 
 except ValueError:
 if self.closed:
 if is\_shutdown():
 # we offer no guarantees on publishes that occur
 # during shutdown, so this is not exceptional.
 return
 else:
 # this indicates that user-level code most likely
 # closed the topic, which is exceptional.
 raise ROSException("topic was closed during publish()")
 else:
 # unexpected, so re-raise original error
 raise

 # remove any bad connections
 for c in err\_con:
 try:
 # connection will callback into remove\_connection when
 # we close it
 c.close()
 except:
 pass

#################################################################################
# TOPIC MANAGER/LISTENER

class \_TopicManager(object):

 def \_\_init\_\_(self):
 """ctor."""
 super(\_TopicManager, self).\_\_init\_\_()
 self.pubs = {} #: { topic: \_PublisherImpl }
 self.subs = {} #: { topic: \_SubscriberImpl }
 self.topics = set() # [str] list of topic names
 self.lock = threading.Condition()
 self.closed = False
 \_logger.info("topicmanager initialized")

 def get\_pub\_sub\_info(self):
 with self.lock:
 info = []
 for s in chain(iter(self.pubs.values()), iter(self.subs.values())):
 info.extend(s.get\_stats\_info())
 return info
 
 def get\_pub\_sub\_stats(self):
 with self.lock:
 return [s.get\_stats() for s in self.pubs.values()],\
 [s.get\_stats() for s in self.subs.values()]
 
 def close\_all(self):
 self.closed = True
 with self.lock:
 for t in chain(iter(self.pubs.values()), iter(self.subs.values())):
 t.close()
 self.pubs.clear()
 self.subs.clear() 
 
 def \_add(self, ps, rmap, reg\_type):
 resolved\_name = ps.resolved\_name
 \_logger.debug("tm.\_add: %s, %s, %s", resolved\_name, ps.type, reg\_type)
 with self.lock:
 rmap[resolved\_name] = ps
 self.topics.add(resolved\_name)
 
 # NOTE: this call can take a lengthy amount of time (at
 # least until its reimplemented to use queues)
 get\_registration\_listeners().notify\_added(resolved\_name, ps.type, reg\_type)

 def \_recalculate\_topics(self):
 """recalculate self.topics. expensive"""
 self.topics = set([x.resolved\_name for x in self.pubs.values()] +
 [x.resolved\_name for x in self.subs.values()])
 
 def \_remove(self, ps, rmap, reg\_type):
 resolved\_name = ps.resolved\_name
 \_logger.debug("tm.\_remove: %s, %s, %s", resolved\_name, ps.type, reg\_type)
 with self.lock:
 del rmap[resolved\_name]
 self. \_recalculate\_topics()
 
 # NOTE: this call can take a lengthy amount of time (at
 # least until its reimplemented to use queues)
 get\_registration\_listeners().notify\_removed(resolved\_name, ps.type, reg\_type)

 def get\_impl(self, reg\_type, resolved\_name):
 """
 Get the L{\_TopicImpl} for the specified topic. This is mainly for
 testing purposes. Unlike acquire\_impl, it does not alter the
 ref count.
 @param resolved\_name: resolved topic name
 @type resolved\_name: str
 @param reg\_type: L{rospy.registration.Registration.PUB} or L{rospy.registration.Registration.SUB}
 @type reg\_type: str
 """
 if reg\_type == Registration.PUB:
 rmap = self.pubs
 elif reg\_type == Registration.SUB:
 rmap = self.subs
 else:
 raise TypeError("invalid reg\_type: %s"%s)
 return rmap.get(resolved\_name, None)
 
 if reg\_type == Registration.PUB:
 rmap = self.pubs
 impl\_class = \_PublisherImpl
 elif reg\_type == Registration.SUB:
 rmap = self.subs
 impl\_class = \_SubscriberImpl
 else:
 raise TypeError("invalid reg\_type: %s"%s)
 with self.lock:
 impl = rmap.get(resolved\_name, None) 
 if not impl:
 impl = impl\_class(resolved\_name, data\_class)
 self.\_add(impl, rmap, reg\_type)
 impl.ref\_count += 1
 return impl

 def release\_impl(self, reg\_type, resolved\_name):
 if reg\_type == Registration.PUB:
 rmap = self.pubs
 else:
 rmap = self.subs
 with self.lock:
 # check for race condition where multiple things are cleaning up at once
 if self.closed:
 return
 impl = rmap.get(resolved\_name, None)
 assert impl is not None, "cannot release topic impl as impl [%s] does not exist"%resolved\_name
 impl.ref\_count -= 1
 assert impl.ref\_count >= 0, "topic impl's reference count has gone below zero"
 if impl.ref\_count == 0:
 \_logger.debug("topic impl's ref count is zero, deleting topic %s...", resolved\_name)
 impl.close()
 self.\_remove(impl, rmap, reg\_type)
 del impl
 \_logger.debug("... done deleting topic %s", resolved\_name)

 def get\_publisher\_impl(self, resolved\_name):
 return self.pubs.get(resolved\_name, None)

 def get\_subscriber\_impl(self, resolved\_name):
 return self.subs.get(resolved\_name, None)

 def has\_subscription(self, resolved\_name): 
 return resolved\_name in self.subs

 def has\_publication(self, resolved\_name):
 return resolved\_name in self.pubs

 def get\_topics(self): 
 return self.topics
 
 def \_get\_list(self, rmap):
 return [[k, v.type] for k, v in rmap.items()]

 ## @return [[str,str],]: list of topics subscribed to by this node, [ [topic1, topicType1]...[topicN, topicTypeN]]
 def get\_subscriptions(self):
 return self.\_get\_list(self.subs)

 ## @return [[str,str],]: list of topics published by this node, [ [topic1, topicType1]...[topicN, topicTypeN]]
 def get\_publications(self):
 return self.\_get\_list(self.pubs)

set\_topic\_manager(\_TopicManager())

I want to make a new package that inherits this package but overwrites these two functions :

\_PublisherImpl.publish and \_SubscriberImpl.\_invoke\_callback

How should i structure my ros package and what src files should I have and how should they look?
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
To create a new ROS package that inherits from the existing package and overrides the two functions \_PublisherImpl.publish and \_SubscriberImpl.\_invoke\_callback, you can follow these steps:

1. Create a new ROS package. Let's call it `my_package`. Navigate to the `src` folder of your ROS workspace and run:
```
catkin_create_pkg my_package rospy
```
1. In the `my_package` folder, create a folder called `src` to store the source files.
2. Create a new Python file inside the `src` folder called `my_publisher_subscriber.py`. This file will contain the new classes that inherit from the existing package and override the specified functions.
3. In `my_publisher_subscriber.py`, you will need to import the required classes from the existing package:
```python
from rospy.topics import _PublisherImpl, _SubscriberImpl
```
1. Create the new classes that inherit from the existing classes and override the specified functions:
```python
class MyPublisherImpl(_PublisherImpl):
    def publish(self, message, connection_override=None):
        # Your custom implementation here
        pass

class MySubscriberImpl(_SubscriberImpl):
    def _invoke_callback(self, msg, cb, cb_args):
        # Your custom implementation here
        pass
```
1. If needed, you can create wrapper classes for the Subscriber and Publisher classes that use your custom implementations:
```python
from rospy.topics import Subscriber, Publisher, Topic

class MySubscriber(Subscriber):
    def __init__(self, *args, **kwargs):
        Topic.__init__(self, *args, **kwargs)
        self.impl = MySubscriberImpl(self.name, self.data_class)

class MyPublisher(Publisher):
    def __init__(self, *args, **kwargs):
        Topic.__init
```
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->
