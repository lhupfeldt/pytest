import py
defaultconftestpath = py.magic.autopath().dirpath('defaultconftest.py')

class Conftest(object):
    """ the single place for accessing values and interacting 
        towards conftest modules from py.test objects. 

        Note that triggering Conftest instances to import 
        conftest.py files may result in added cmdline options. 
        XXX
    """ 
    def __init__(self, path=None):
        self._path2confmods = {}
        if path is not None:
            self.setinitial([path])

    def setinitial(self, args):
        """ return a Conftest object initialized with a path obtained
            from looking at the first (usually cmdline) argument that points
            to an existing file object. 
            XXX note: conftest files may add command line options
            and we thus have no completely safe way of determining
            which parts of the arguments are actually related to options. 
        """
        current = py.path.local()
        for arg in args + [current]:
            anchor = current.join(arg, abs=1)
            if anchor.check(): # we found some file object 
                #print >>py.std.sys.stderr, "initializing conftest from", anchor
                # conftest-lookups without a path actually mean 
                # lookups with our initial path. 
                self._path2confmods[None] = self.getconftestmodules(anchor)
                #print " -> ", conftest._path2confmods
                break


    def getconftestmodules(self, path):
        """ return a list of imported conftest modules for the given path.  """ 
        try:
            clist = self._path2confmods[path]
        except KeyError:
            dp = path.dirpath()
            if dp == path: 
                return [self.importconfig(defaultconftestpath)]
            clist = self.getconftestmodules(dp)
            conftestpath = path.join("conftest.py")
            if conftestpath.check(file=1):
                clist.append(self.importconfig(conftestpath))
            self._path2confmods[path] = clist
        # be defensive: avoid changes from caller side to
        # affect us by always returning a copy of the actual list 
        return clist[:]

    def getconftest(self, path):
        """ Return a direct module of that path
        """
        if isinstance(path, str):
            path = py.path.local(path)
        try:
            conftestmod = self.getconftestmodules(path)[-1]
            if py.path.local(conftestmod.__file__).dirpath() != path:
                raise AttributeError
            return conftestmod
        except KeyError:
            raise AttributeError
        # we raise here AttributeError to unify error reporting in case
        # of lack of variable in conftest or lack of file, but we do not want to
        # hide ImportError

    # XXX no real use case, may probably go 
    #def lget(self, name, path=None):
    #    modules = self.getconftestmodules(path)
    #    return self._get(name, modules)
   
    def rget(self, name, path=None):
        modules = self.getconftestmodules(path)
        modules.reverse()
        return self._get(name, modules)

    def rget_path(self, name, path):
        """ can raise AttributeError
        """
        return getattr(self.getconftest(path), name)

    def _get(self, name, modules):
        for mod in modules:
            try:
                return getattr(mod, name)
            except AttributeError:
                continue
        raise KeyError, name

    def importconfig(self, configpath):
        # We could have used caching here, but it's redundant since
        # they're cached on path anyway, so we use it only when doing rget_path
        if not configpath.dirpath('__init__.py').check(file=1): 
            # HACK: we don't want any "globally" imported conftest.py, 
            #       prone to conflicts and subtle problems 
            modname = str(configpath).replace('.', configpath.sep)
            mod = configpath.pyimport(modname=modname)
        else:
            mod = configpath.pyimport()
        return mod
