class Singleton(object):
  _instances = {}
  def __new__(class_, *args, **kwargs):
    #print "__new__ called"
    if class_ not in class_._instances:
        #print "miss"
        class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
    return class_._instances[class_]
